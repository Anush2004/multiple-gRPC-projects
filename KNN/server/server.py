import grpc
import argparse
import math
import pickle
import os, sys
from concurrent import futures


# assuming we can keep protoc output here; if not, uncomment these
# protodir = '/'.join(os.getcwd().split('/')[:-1]) + '/protofiles'
# sys.path.append(protodir)

import knn_pb2
import knn_pb2_grpc


class KNNServer(knn_pb2_grpc.KNNServicer):
    def __init__(self, my_start: int, my_end: int, dataset_filepath: str, port: int):
        self.start = my_start
        self.end = my_end
        self.dataset_filepath = dataset_filepath
        self.port = port
        self.points = self.fetch_points()

    def fetch_points(self):
        with open(self.dataset_filepath, 'rb') as infile:
            points = pickle.load(infile)[self.start: self.end]
        return points
    
    def euclidean_distance(self, p1: tuple[float], p2: tuple[float]):
        """Assuming 2D points"""
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def find_knns(self, query_point: tuple[float], k: int):
        # TODO: naive for now, will optimise later
        distances = [(self.euclidean_distance(p, query_point), p) for p in self.points]
        distances.sort()
        
        knns = [pair[1] for pair in distances[: k]]
        return knns

    # implementing the gRPC service
    def FindKNearestNeighbors(self, request, _context):
        query_point = request.dataPoint
        k = request.k
        knns = self.find_knns(tuple(query_point), k)
        
        # send stream
        for neighbour in knns:
            response = knn_pb2.KNNResponse(dataPoint = neighbour)
            yield response



def serve(start_idx: int, end_idx: int, dataset_filepath: str, port: int):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    knn_server = KNNServer(start_idx, end_idx, dataset_filepath, port)
    knn_pb2_grpc.add_KNNServicer_to_server(knn_server, server)
    
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Server started to hold elements from: [{start_idx}, {end_idx}), at port {[port]}")
    server.wait_for_termination()
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='start, end, datafile, port')
    parser.add_argument('start', type=int, help='Starting index in dataset')
    parser.add_argument('end', type=int, help='Ending index in dataset (non inclusive)')
    parser.add_argument('datafile', type=str, help='Absolute path of the file storing the dataset')
    parser.add_argument('port', type=int, help='Port to which the server will bind.')

    args = parser.parse_args()
    
    serve(args.start, args.end, args.datafile, args.port)

