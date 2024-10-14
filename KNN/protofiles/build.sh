#!/bin/bash

# # specific to my system
# GRPC_BIN=~/.local/bin

# # C++
# protoc -I=. --cpp_out=../client ./knn.proto
# protoc -I=. --grpc_out=../client --plugin=protoc-gen-grpc=${GRPC_BIN}/grpc_cpp_plugin ./knn.proto

# Python
python3 -m grpc_tools.protoc -I. --python_out=../server --grpc_python_out=../server ./knn.proto
python3 -m grpc_tools.protoc -I. --python_out=../client --grpc_python_out=../client ./knn.proto