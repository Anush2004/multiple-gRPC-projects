"""Starts up servers"""

import os, argparse
import sys
import pickle


# hacky but okay for now
START_PORT = 12340

def get_indices(num_servers: int, num_points: int) -> list[tuple[int]]:
    indices = []
    equal_div = num_points // num_servers
    leftover = num_points - (num_servers * equal_div)

    for i in range(num_servers):
        start = indices[-1][1] if len(indices) > 0 else 0
        my_share = equal_div + (1 if i < leftover else 0)
        end = start + my_share

        indices.append((start, end))
    
    return indices

def split_dataset(num_servers: int, datafile: str, portsfile: str):
    with open(datafile, 'rb') as infile:
        points = pickle.load(infile)
    num_points = len(points)

    bounds = get_indices(num_servers, num_points)
    ports = [START_PORT + i for i in range(num_servers)]

    # store ports so client can read
    with open(portsfile, 'w') as outfile:
        lines = [str(port) + '\n' for port in ports]
        outfile.writelines(lines)
    
    # start servers
    for i in range(num_servers):
        # hacky parallelism
        os.system(f"python3 server.py {bounds[i][0]} {bounds[i][1]} {datafile} {ports[i]} &")


def resolve_relpath(relpath: str) -> str:
    dirname = os.path.dirname(__file__)
    abspath = os.path.join(dirname, relpath)
    sys.path.append(abspath)
    return abspath


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='num_servers, datafile')
    parser.add_argument('num_servers', type=int, help='The number of servers to launch')
    parser.add_argument('datafile', type=str, help='Relative path of the file storing the dataset')
    parser.add_argument('portsfile', type=str, help='Relative path of the file to write server ports in')

    args = parser.parse_args()

    num_servers = args.num_servers
    datafile = resolve_relpath(args.datafile)
    portsfile = args.portsfile

    try:
        split_dataset(num_servers, datafile, portsfile)
    except KeyboardInterrupt:
        # hacky way to clean up servers
        os.system("kill $(ps aux | grep server.py | grep -v grep | awk '{print $2}')")
