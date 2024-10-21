import sys, os, datetime
from dataclasses import dataclass


MAX_NUM_REASSIGNS = 5
TIMEOUT = 10 # seconds


@dataclass
class RiderStatus:
    PROCESSING: int = 1
    REJECTED: int = 2
    ASSIGNED: int = 3
    COMPLETED: int = 4
    NOTFOUND: int = 5

@dataclass
class DriverStatus:
    NONE: int = 0
    SUCCESS: int = 1
    NOTFOUND: int = 2


class RideRequest:
    def __init__(self, ride_id: str = None, rider_id: str = None, pickup: str = None, dest: str = None, driver_id: str = None, status: int = None):
        self.ride_id: str = ride_id
        self.rider_id: str = rider_id
        self.pickup: str = pickup
        self.dest: str = dest
        self.driver_id: str = driver_id
        self.num_reassigns: int = 0
        self.status: int = status
    
    def print_req(self):
        print(f'''Ride request {self.ride_id}:
              \trider: {self.rider_id} 
              \tpickup: {self.pickup} 
              \tdest: {self.dest} 
              \tdriver: {self.driver_id} 
              \tnum_reassigns: {self.num_reassigns} 
              \tstatus: {self.status}\n''')


def resolve_relpath(relpath: str) -> str:
    dirname = os.path.dirname(__file__)
    abspath = os.path.join(dirname, relpath)
    sys.path.append(abspath)
    return abspath

def get_cur_time():
    now = datetime.datetime.now()
    # Format the time as DDMMYYYY HHMMSS
    formatted_time = now.strftime("%d/%m/%Y %H:%M:%S")
    return formatted_time
