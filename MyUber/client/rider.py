import grpc
import argparse

import utils

# assuming we can keep protoc output here; if not, uncomment these
# protodir = '/'.join(os.getcwd().split('/')[:-1]) + '/protofiles'
# sys.path.append(protodir)

import rider_pb2, rider_pb2_grpc

class RiderClient:
    def __init__(self, name: str, ports: list[int]):
        self.name = name
        self.conns = self.resolve_ports(ports)
        self.num_servers = len(ports)
        self.cur_server = 0
        self.cur_ride_resp = None # [ride_id, driver, status]
        self.has_requested_ride = False
    
    def resolve_ports(self, ports: list[int]):
        addresses = [f"localhost:{port}" for port in ports]
        channels = [grpc.insecure_channel(address) for address in addresses]
        stubs = [rider_pb2_grpc.RiderStub(channel) for channel in channels]
        conns = {
            "ports": ports,
            "addresses": addresses,
            "channels": channels,
            "stubs": stubs
        }
        return conns
    
    def request_ride(self, pickup: str, dest: str):
        request = rider_pb2.RideRequest()
        request.rider_id = self.name
        request.pickup_location = pickup
        request.destination = dest

        self.has_requested_ride = True
        print(f"Requesting ride from {pickup} to {dest}.")
        
        stub = self.conns["stubs"][self.cur_server]
        response = stub.RequestRide(request) # sets request to that server
        self.cur_server = (self.cur_server + 1) % self.num_servers # round robin LB
        
        self.cur_ride_resp = [response.ride_id, None, None]

    
    def request_ride_status(self):
        # not making parallel, as no such scenario will be expected
        if not self.has_requested_ride:
            print("No ride requested yet.")

        print("Requesting ride status.")
        request = rider_pb2.RideStatusRequest()
        request.rider_id = self.name
        request.ride_id = self.cur_ride_resp[0]
        
        # keep trying till the correct server is reached
        while True:
            stub = self.conns["stubs"][self.cur_server]
            response = stub.GetRideStatus(request)
            self.cur_server = (self.cur_server + 1) % self.num_servers # round robin LB
            if response.status != utils.RiderStatus.NOTFOUND:
                break

        self.cur_ride_resp[2] = response.status

        match(response.status):
            case utils.RiderStatus.COMPLETED:
                print("Ride completed.")
                self.has_requested_ride = False
                self.cur_ride_resp = None
            case utils.RiderStatus.REJECTED:
                print("Ride request rejected. Try again.")
                self.has_requested_ride = False
                self.cur_ride_resp = None
            case utils.RiderStatus.PROCESSING:
                print("Waiting for a driver to accept.")
            case utils.RiderStatus.ASSIGNED:
                self.cur_ride_resp[1] = response.driver
                print(f"Ride ID {self.cur_ride_resp[0]} assigned to driver {response.driver}.")

    def menu(self):
        while True:
            if not self.has_requested_ride:
                choice = input("Request a ride (y/n)? ").strip()
                match(choice):
                    case "y":
                        pickup = input("Enter your pickup location: ").strip()
                        dest = input("Enter your destination: ").strip()
                        self.request_ride(pickup, dest)
                    case "n":
                        print("Exiting...")
                        break
                    case _:
                        print("Invalid choice")
            else:
                choice = input("Enter anything to request ride status:")
                if choice != "":
                    self.request_ride_status()

def run(server_ports: list[int]):
    # TODO: handle multiple servers
    # TODO: load balancing

    rider_name = input("Enter your name: ").strip()

    print("Starting client")
    client = RiderClient(rider_name, server_ports)
    client.menu()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rider client for MyUber.")
    parser.add_argument("ports_file", type=str, help="Path to the file containing server ports.")
    args = parser.parse_args()
    ports_file = utils.resolve_relpath(args.ports_file)
    ports = utils.get_server_ports(ports_file)
    run(ports)

