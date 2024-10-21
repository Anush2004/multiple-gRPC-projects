import grpc
import argparse
import time
import threading

import utils

# assuming we can keep protoc output here; if not, uncomment these
# protodir = '/'.join(os.getcwd().split('/')[:-1]) + '/protofiles'
# sys.path.append(protodir)

import driver_pb2, driver_pb2_grpc

class DriverClient:
    def __init__(self, name: str, ports: list[int]):
        self.name = name
        self.conns = self.resolve_ports(ports)
        self.num_servers = len(ports)
        self.cur_server = 0
        self.cur_ride_req = None
        self.has_ride_req = False
        self.has_accepted_req = False
        self.ride_offer_time: int = 0
        self.has_timedout: bool = False
    
    def resolve_ports(self, ports: list[int]):
        addresses = [f"localhost:{port}" for port in ports]
        channels = [grpc.insecure_channel(address) for address in addresses]
        stubs = [driver_pb2_grpc.DriverStub(channel) for channel in channels]
        conns = {
            "ports": ports,
            "addresses": addresses,
            "channels": channels,
            "stubs": stubs
        }
        return conns

    def timeout_tracker(self):
        self.ride_offer_time = time.time_ns()
        self.has_timedout = False
        request = driver_pb2.TimedOutRideRequest()
        request.driver_id = self.name
        ride_id = self.cur_ride_req[0]
        request.ride_id = ride_id

        while True:
            cur_time = time.time_ns()
            if cur_time >= self.ride_offer_time + utils.TIMEOUT * 1e9:
                # keep trying till the correct server is reached
                while True:
                    stub = self.conns["stubs"][self.cur_server]
                    response = stub.TimedOutRide(request)
                    self.cur_server = (self.cur_server + 1) % self.num_servers # round robin LB
                    if response.status != utils.DriverStatus.NOTFOUND:
                        break
                print(f"\nRide offer for ride {ride_id} timed out.\n")
                self.ride_offer_time = 0
                self.has_timedout = True
                break

    def am_available(self):
        request = driver_pb2.AmAvailableRequest()
        request.driver_id = self.name
        request.message = "" # TODO: needed?

        print("Requesting a ride offer.")

        stub = self.conns["stubs"][self.cur_server]
        response = stub.AmAvailable(request) # sets request to that server
        self.cur_server = (self.cur_server + 1) % self.num_servers # round robin LB

        if response.status == utils.DriverStatus.NONE:
            # TODO: ask other servers
            print("No ride requested currently. Try again later.")
        else:
            self.has_ride_req = True
            self.cur_ride_req = (response.ride_id, response.rider_id, response.pickup_location, response.destination, response.status)
            print(f"Received ride ({response.ride_id}) request for rider {response.rider_id} from {response.pickup_location} to {response.destination} with status: {response.status}")
            # call timeout thread

            timer = threading.Thread(target = self.timeout_tracker)
            timer.start()

    def accept_ride(self):
        request = driver_pb2.AcceptRideRequest()
        request.driver_id = self.name
        request.ride_id = self.cur_ride_req[0]
        
        # keep trying till the correct server is reached
        while True:
            stub = self.conns["stubs"][self.cur_server]
            response = stub.AcceptRide(request)
            self.cur_server = (self.cur_server + 1) % self.num_servers # round robin LB
            if response.status != utils.DriverStatus.NOTFOUND:
                break
        
        print(f"Accepted ride {self.cur_ride_req[0]}")
        self.has_accepted_req = True

    def reject_ride(self):
        request = driver_pb2.RejectRideRequest()
        request.driver_id = self.name
        request.ride_id = self.cur_ride_req[0]

        # keep trying till the correct server is reached
        while True:
            stub = self.conns["stubs"][self.cur_server]
            response = stub.RejectRide(request)
            self.cur_server = (self.cur_server + 1) % self.num_servers # round robin LB
            if response.status != utils.DriverStatus.NOTFOUND:
                break

        print(f"Rejected ride {self.cur_ride_req[0]}")
        self.has_ride_req = False
        self.has_accepted_req = False
        self.cur_ride_req = None

    def complete_ride(self):
        request = driver_pb2.RideCompletionRequest()
        request.driver_id = self.name
        request.ride_id = self.cur_ride_req[0]
        
        # keep trying till the correct server is reached
        while True:
            stub = self.conns["stubs"][self.cur_server]
            response = stub.CompleteRide(request)
            self.cur_server = (self.cur_server + 1) % self.num_servers # round robin LB
            if response.status != utils.DriverStatus.NOTFOUND:
                break

        print(f"Completed ride {self.cur_ride_req[0]}")
        self.has_accepted_req = False
        self.has_ride_req = False
        self.cur_ride_req = None

    def menu(self):
        while True:
            if not self.has_ride_req:
                choice = input("Look for a ride or exit (y/n)?").strip()
                match(choice):
                    case "y":
                        self.am_available()
                    case "n":
                        print("Exiting...")
                        break
                    case _:
                        print("Invalid choice")
            
            elif not self.has_accepted_req:
                choice = input("Accept/reject ride (a/r)?")
                if self.has_timedout == True:
                    self.has_ride_req = False
                    self.has_accepted_req = False
                    self.cur_ride_req = None
                else:
                    match(choice):
                        case "a":
                            self.accept_ride()
                        case "r":
                            self.reject_ride()
                        case _:
                            print("Invalid choice")
            
            else:
                choice = input("Enter anything to complete ride:")
                if choice != "":
                    self.complete_ride()


def run(server_ports: list[int]):
    # TODO: handle multiple servers
    # TODO: load balancing

    driver_name = input("Enter your name: ").strip()

    # port = server_ports[0]
    print("Starting client")
    client = DriverClient(driver_name, server_ports)
    client.menu()
    # server_address = f"localhost:{port}"
    # with grpc.insecure_channel(server_address) as channel:
    #     client = DriverClient(driver_name, channel)
    #     client.menu()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Driver client for MyUber.")
    parser.add_argument("ports_file", type=str, help="Path to the file containing server ports.")
    args = parser.parse_args()
    ports_file = utils.resolve_relpath(args.ports_file)
    ports = utils.get_server_ports(ports_file)
    run(ports)
