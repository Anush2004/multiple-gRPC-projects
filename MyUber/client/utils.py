import sys, os
from enum import Enum
from dataclasses import dataclass

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


def get_server_ports(filepath: str):
    ports = []
    try:
        with open(filepath, 'r') as infile:
            for line in infile:
                ports.append(int(line.strip()))
    except IOError:
        print(f"ERROR: client couldn't open file {filepath}")
    
    return ports

def resolve_relpath(relpath: str) -> str:
    dirname = os.path.dirname(__file__)
    abspath = os.path.join(dirname, relpath)
    sys.path.append(abspath)
    return abspath

