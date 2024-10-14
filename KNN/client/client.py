import grpc
import argparse
import os, sys
import numpy as np
import heapq


# assuming we can keep protoc output here; if not, uncomment these
# protodir = '/'.join(os.getcwd().split('/')[:-1]) + '/protofiles'
# sys.path.append(protodir)

import knn_pb2
import knn_pb2_grpc


class KNNClient:
    def __init__(self, channel):
        self.stub = knn_pb2_grpc.KNNStub(channel)

    def find_k_nearest_neighbors(self, query_point: list[float], k: int) -> list[list[float]]:
        # request
        request = knn_pb2.KNNRequest()
        request.dataPoint.extend(query_point)
        request.k = k

        # response stream
        response_iterator = self.stub.FindKNearestNeighbors(request)

        knns = []
        for response in response_iterator:
            knns.append(list(response.dataPoint))

        return knns


def get_server_ports(filepath):
    ports = []
    try:
        with open(filepath, 'r') as infile:
            for line in infile:
                ports.append(int(line.strip()))
    except IOError:
        print(f"ERROR: client couldn't open file {filepath}")
    
    return ports


def euclidean_distance(a, b):
    return np.sqrt(np.sum((np.array(a) - np.array(b)) ** 2))


def get_all_knns(server_ports, query_point, k):
    max_heap = []

    for port in server_ports:
        server_address = f"localhost:{port}"
        with grpc.insecure_channel(server_address) as channel:
            client = KNNClient(channel)
            local_knns = client.find_k_nearest_neighbors(query_point, k)

            for point in local_knns:
                dist = euclidean_distance(query_point, point)
                # -ve distance cos max heap
                heapq.heappush(max_heap, (-dist, point))
                if len(max_heap) > k:
                    heapq.heappop(max_heap)

    knns = []
    while len(max_heap) > 0:
        dist, point = heapq.heappop(max_heap)
        knns.append((-dist, point))

    return knns[::-1]


def print_point(point):
    print(f"({', '.join(map(str, point))})")


def run(server_ports: list[int], query_point: list[float], k: int):

    print(f"Finding {k} nearest neighbors for point: ", end="")
    print_point(query_point)

    all_knns = get_all_knns(server_ports, query_point, k)

    print("Points:")
    i = 1
    for dist, point in all_knns:
        print(i, dist, end = ":\t")
        i += 1
        print_point(point)


def resolve_relpath(relpath: str) -> str:
    dirname = os.path.dirname(__file__)
    abspath = os.path.join(dirname, relpath)
    sys.path.append(abspath)
    return abspath



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find K nearest neighbors for a given data point.")
    parser.add_argument("ports_file", type=str, help="Path to the file containing server ports.")
    parser.add_argument("k", type=int, help="Number of nearest neighbors to find.")
    parser.add_argument("data_point_x", type=float, help="X-coordinate of the query point.")
    parser.add_argument("data_point_y", type=float, help="Y-coordinate of the query point.")
    
    args = parser.parse_args()

    ports_file = resolve_relpath(args.ports_file)
    k = args.k
    query_point = [args.data_point_x, args.data_point_y]
    ports = get_server_ports(ports_file)
    
    run(ports, query_point, k)

