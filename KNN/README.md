# K Nearest Neighbours using gRPC

Run all scripts in their respective directories only.

## Generating GRPC code

Run this script inside the `protofiles` directory.

```bash
./build.sh
```

This compiles python code for client and server, and places it in both their directories.

## Dataset preparation

Run the script to generate a dataset and store it in a `.pkl` file in the `dataset` directory.

```bash
python3 dataset.py <num_points> <filepath>
```

where `filepath` is the path of the file where the dataset is to be saved. I'm using `dataset.pkl`

## Servers

Run this script to create a given number of servers and have them know their respective parts of the dataset.

```bash
python3 start_servers.py <num_servers> <dataset_file> <ports_file>
```

where `dataset_file` is `../dataset/dataset.pkl` and `ports_file` is `./server_ports.txt`

After killing the program, run this to clean up the server processes created:
```bash
kill $(ps aux | grep server.py | grep -v grep | awk '{print $2}')
```

## Client

Run this script to query the dataset for a given point and a given value of `k`.

```bash
python3 client.py <server_ports_file> <k> <query_point_x> <query_point_y>
```

where I take `server_ports_file` to be `../server/server_ports.txt`.