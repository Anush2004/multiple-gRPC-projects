#!/bin/bash

echo "Installing necessary dependencies..."
pip install grpcio grpcio-tools

echo "Compiling proto files..."
PROTO_DIR="./protofiles"
OUT_DIR="./protofiles"

python -m grpc_tools.protoc -I $PROTO_DIR --python_out=$OUT_DIR --grpc_python_out=$OUT_DIR $PROTO_DIR/*.proto

echo "Starting the logger server..."
gnome-terminal --title="Logger Server" -- bash -c "cd server && python logger_server.py; exec bash"

echo "Starting the main server..."
gnome-terminal --title="Main Server" -- bash -c "cd server && python server.py; exec bash"

echo "Starting the first client..."
gnome-terminal --title="Client 1" -- bash -c "cd clients && python client.py; exec bash"

echo "Starting the second client..."
gnome-terminal --title="Client 2" -- bash -c "cd clients && python client.py; exec bash"

echo "All services have been started in separate terminal windows!"
