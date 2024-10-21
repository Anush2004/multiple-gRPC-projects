"""Starts up servers"""

import os, argparse
import utils


# hacky but okay for now
START_PORT = 12340


def start_servers(num_servers: int, portsfile: str):
    ports = [START_PORT + i for i in range(num_servers)]

    # store ports so client can read
    with open(portsfile, 'w') as outfile:
        lines = [str(port) + '\n' for port in ports]
        outfile.writelines(lines)
    
    # start servers
    for i in range(num_servers):
        # hacky parallelism
        os.system(f"python3 server.py {ports[i]} &")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='num_servers, portsfile')
    parser.add_argument('num_servers', type=int, help='The number of servers to launch')
    parser.add_argument('portsfile', type=str, help='Relative path of the file to write server ports in')

    args = parser.parse_args()

    num_servers = args.num_servers
    portsfile = utils.resolve_relpath(args.portsfile)

    try:
        start_servers(num_servers, portsfile)
    except KeyboardInterrupt:
        # hacky way to clean up servers
        os.system("kill $(ps aux | grep server.py | grep -v grep | awk '{print $2}')")
