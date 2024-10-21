import grpc
import argparse
from concurrent import futures
import threading
import ssl
from cryptography import x509
from cryptography.hazmat.primitives import serialization

import utils

# assuming we can keep protoc output here; if not, uncomment these
# protodir = '/'.join(os.getcwd().split('/')[:-1]) + '/protofiles'
# sys.path.append(protodir)

import rider_pb2, rider_pb2_grpc
import driver_pb2, driver_pb2_grpc
# import uber_pb2, uber_pb2_grpc

class LoggingInterceptor(grpc.ServerInterceptor):
    def __init__(self):
        def abort(_request, context):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid signature")
        self._abort = grpc.unary_unary_rpc_method_handler(abort)

        self.driver_rpcs = (
            "AmAvailable",
            "AcceptRide",
            "RejectRide",
            "TimedOutRide",
            "CompleteRide"
        )

        self.rider_rpcs = (
            "RequestRide",
            "GetRideStatus"
        )
    
    def intercept_service(self, continuation, handler_call_details):
        method_name = handler_call_details.method.split('/')[-1]
        timestamp = utils.get_cur_time()

        
        if method_name in self.rider_rpcs:
            client_role = "Rider"
        elif method_name in self.driver_rpcs:
            client_role = "Driver"
        else:
            client_role = "Unknown"

        print(f"[LOGGING] {timestamp} - {client_role} call: {method_name}")
        
        return continuation(handler_call_details)


class AuthInterceptor(grpc.ServerInterceptor):
    def __init__(self):
        def abort(ignored_request, context):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid certificate")

        self._abort = grpc.unary_unary_rpc_method_handler(abort)

    def intercept_service(self, continuation, handler_call_details):
        metadata = dict(handler_call_details.invocation_metadata)
        
        # Extract client certificate from metadata
        if 'x-client-cert' in metadata:
            cert_pem = metadata['x-client-cert']
            cert = x509.load_pem_x509_certificate(cert_pem.encode())
            
            # Verify certificate (you may want to add more checks here)
            if self.verify_certificate(cert):
                return continuation(handler_call_details)
        
        return self._abort

    def verify_certificate(self, cert):
        # Implement certificate verification logic here
        # For example, check if it's issued by a trusted CA, not expired, etc.
        # Return True if valid, False otherwise
        return True  # Placeholder implementation


class RiderClientServicer(rider_pb2_grpc.RiderServicer):
    def __init__(self, request_buffer: list[int], ride_reqs: dict[str, utils.RideRequest], port: int):
        self.request_buffer: list[int] = request_buffer
        self.ride_reqs: dict[int, utils.RideRequest] = ride_reqs
        self.port = port
    
    def RequestRide(self, request, _context):
        # create new unique ID, will keep increasing as new requests come in
        new_ride_id: str = f"{self.port}:{len(self.ride_reqs)}"
        # create request
        ride_req = utils.RideRequest(
            new_ride_id,
            request.rider_id,
            request.pickup_location,
            request.destination,
            status = utils.RiderStatus.PROCESSING
        )
        self.request_buffer.append(ride_req.ride_id)
        self.ride_reqs[ride_req.ride_id] = ride_req
        print(f"[{self.port} {utils.get_cur_time()}] Ride request created (total {len(self.request_buffer)}): ")
        ride_req.print_req()

        response = rider_pb2.RideResponse(ride_id = ride_req.ride_id)
        return response

    def GetRideStatus(self, request, _context):
        ride_id = request.ride_id

        if ride_id not in self.ride_reqs:
            response = rider_pb2.RideStatusResponse(
                status = utils.RiderStatus.NOTFOUND
            )
            print(f"[{self.port} {utils.get_cur_time()}] Ride {ride_id} not available here.")
            return response

        ride_req = self.ride_reqs[ride_id]

        print(f"[{self.port} {utils.get_cur_time()}] Requested status for ride ID {ride_id}: {ride_req.status}")
        
        driver_id = ride_req.driver_id if ride_req.driver_id else ""
        status = ride_req.status
        response = rider_pb2.RideStatusResponse(driver = driver_id, status = status)
        return response


class DriverClientServicer(driver_pb2_grpc.DriverServicer):
    def __init__(self, request_buffer: list[int], ride_reqs: dict[str, utils.RideRequest], port: int):
        self.request_buffer: list[int] = request_buffer
        self.ride_reqs: dict[int, utils.RideRequest] = ride_reqs
        self.request_lock = threading.Lock()
        self.port: int = port

    def AmAvailable(self, request, _context):
        driver_id = request.driver_id
        
        print(f"[{self.port} {utils.get_cur_time()}] Driver {driver_id} requesting a ride to pick up.")
        with self.request_lock:
            if len(self.request_buffer) == 0:
                response = driver_pb2.AmAvailableResponse(
                    status = utils.DriverStatus.NONE
                )
                print(f"[{self.port} {utils.get_cur_time()}] No ride requests available.")
                return response
            
            ride_id = self.request_buffer.pop(0)

        response = driver_pb2.AmAvailableResponse(
            ride_id = ride_id,
            rider_id = self.ride_reqs[ride_id].rider_id,
            pickup_location = self.ride_reqs[ride_id].pickup,
            destination = self.ride_reqs[ride_id].dest,
            status = utils.DriverStatus.SUCCESS
        )
        print(f"[{self.port} {utils.get_cur_time()}] Offered ride {ride_id} for rider {self.ride_reqs[ride_id].rider_id} to driver {driver_id}.")
        return response

    def AcceptRide(self, request, _context):
        driver_id = request.driver_id
        ride_id = request.ride_id

        if ride_id not in self.ride_reqs:
            response = driver_pb2.AcceptRideResponse(
                status = utils.DriverStatus.NOTFOUND
            )
            print(f"[{self.port} {utils.get_cur_time()}] Ride {ride_id} not available here.")
            return response

        self.ride_reqs[ride_id].driver_id = driver_id
        self.ride_reqs[ride_id].status = utils.RiderStatus.ASSIGNED
        
        print(f"[{self.port} {utils.get_cur_time()}] Driver {driver_id} accepted ride request ID {ride_id} by rider {self.ride_reqs[ride_id].rider_id}.")
        response = driver_pb2.AcceptRideResponse(ride_id = ride_id)
        return response

    def RejectRide(self, request, _context):
        driver_id = request.driver_id
        ride_id = request.ride_id
        
        if ride_id not in self.ride_reqs:
            response = driver_pb2.RejectRideResponse(
                status = utils.DriverStatus.NOTFOUND
            )
            print(f"[{self.port} {utils.get_cur_time()}] Ride {ride_id} not available here.")
            return response

        with self.request_lock:
            self.ride_reqs[ride_id].num_reassigns += 1
            print(f"[{self.port} {utils.get_cur_time()}] Driver {driver_id} rejected ride request ID {ride_id} by rider {self.ride_reqs[ride_id].rider_id}. Total reassigns: {self.ride_reqs[ride_id].num_reassigns}")

            # reject ride if max reassigns reached
            if self.ride_reqs[ride_id].num_reassigns >= utils.MAX_NUM_REASSIGNS:
                self.ride_reqs[ride_id].status = utils.RiderStatus.REJECTED
            else:
                self.request_buffer.append(ride_id) # add back to queue

        response = driver_pb2.RejectRideResponse(ride_id = ride_id)
        return response
    
    def TimedOutRide(self, request, _context):
        driver_id = request.driver_id
        ride_id = request.ride_id
        
        if ride_id not in self.ride_reqs:
            response = driver_pb2.TimedOutRideResponse(
                status = utils.DriverStatus.NOTFOUND
            )
            print(f"[{self.port} {utils.get_cur_time()}] Ride {ride_id} not available here.")
            return response

        with self.request_lock:
            self.ride_reqs[ride_id].num_reassigns += 1
            print(f"[{self.port} {utils.get_cur_time()}] Driver {driver_id} timed out {"and rejected" if self.ride_reqs[ride_id].num_reassigns >= utils.MAX_NUM_REASSIGNS else ""} ride request ID {ride_id} \
                  by rider {self.ride_reqs[ride_id].rider_id}. Total reassigns: {self.ride_reqs[ride_id].num_reassigns}")

            # reject ride if max reassigns reached
            if self.ride_reqs[ride_id].num_reassigns >= utils.MAX_NUM_REASSIGNS:
                self.ride_reqs[ride_id].status = utils.RiderStatus.REJECTED
            else:
                self.request_buffer.append(ride_id) # add back to queue

        response = driver_pb2.TimedOutRideResponse(ride_id = ride_id)
        return response

    def CompleteRide(self, request, _context):
        driver_id = request.driver_id
        ride_id = request.ride_id

        if ride_id not in self.ride_reqs:
            response = driver_pb2.RideCompletionResponse(
                status = utils.DriverStatus.NOTFOUND
            )
            print(f"[{self.port} {utils.get_cur_time()}] Ride {ride_id} not available here.")
            return response
        
        self.ride_reqs[ride_id].status = utils.RiderStatus.COMPLETED
        
        print(f"[{self.port} {utils.get_cur_time()}] Driver {driver_id} completed ride ID {ride_id} by rider {self.ride_reqs[ride_id].rider_id}.")
        response = driver_pb2.RideCompletionResponse(ride_id = ride_id)
        return response


class UberServer:
    def __init__(self, port: int):
        self.request_buffer: list[int] = []
        self.ride_reqs: dict[str, utils.RideRequest] = dict()
        self.rider_servicer = RiderClientServicer(self.request_buffer, self.ride_reqs, port)
        self.driver_servicer = DriverClientServicer(self.request_buffer, self.ride_reqs, port)
        self.port = port
        
        # Create gRPC server with interceptors
        self.grpc_server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=10),
            interceptors=(LoggingInterceptor(),)
        )

        # register servicers
        rider_pb2_grpc.add_RiderServicer_to_server(self.rider_servicer, self.grpc_server)
        driver_pb2_grpc.add_DriverServicer_to_server(self.driver_servicer, self.grpc_server)
        
    def serve(self):
        self.grpc_server.add_insecure_port(f"[::]:{self.port}")
        self.grpc_server.start()
        print(f"Server started at port {self.port}")
        self.grpc_server.wait_for_termination()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Uber gRPC server')
    parser.add_argument('port', type=int, help='Port to which the server will bind.')

    args = parser.parse_args()
    
    uber_server = UberServer(args.port)
    uber_server.serve()
