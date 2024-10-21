#!/bin/bash

python3 -m grpc_tools.protoc -I. --python_out=../server --grpc_python_out=../server ./rider.proto
python3 -m grpc_tools.protoc -I. --python_out=../client --grpc_python_out=../client ./rider.proto

python3 -m grpc_tools.protoc -I. --python_out=../server --grpc_python_out=../server ./driver.proto
python3 -m grpc_tools.protoc -I. --python_out=../client --grpc_python_out=../client ./driver.proto

# python3 -m grpc_tools.protoc -I. --python_out=../server --grpc_python_out=../server ./uber.proto
# python3 -m grpc_tools.protoc -I. --python_out=../client --grpc_python_out=../client ./uber.proto