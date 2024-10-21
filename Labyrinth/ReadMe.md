# Labyrinth Game

## Project Description

The Labyrinth game is a single-server, single-client architecture implemented in Python using gRPC. It features a grid-based maze where a player can navigate through various types of tiles to collect coins while avoiding walls. The objective is to reach the bottom-right corner of the labyrinth, collecting as many coins as possible while managing health points and spells.

## Table of Contents
- [Installation Instructions](#installation-instructions)
- [Usage Instructions](#usage-instructions)
- [Directory Structure](#directory-structure)
- [Features](#features)
- [RPC Methods](#rpc-methods)

## Installation Instructions

To run the Labyrinth game, ensure you have Python 3.x installed on your machine. You will also need to install the `grpcio` and `grpcio-tools` packages.

```bash
pip install grpcio grpcio-tools
```



### Generate gRPC Files

Navigate to the `protofiles` directory and run:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. labyrinth.proto
```

## Usage Instructions

### Start the Server

Navigate to the `server` directory and run the following command:

```bash
python server.py
```

The server will listen on port 50051.

### Start the Client

In a separate terminal, navigate to the `client` directory and run:

```bash
python client.py
```

The client will interact with the server, allowing you to move around the labyrinth and perform spells.

## Directory Structure

```
LabyrinthGame/
├── protofiles/
│   ├── labyrinth.proto      # Protobuf definitions for gRPC
│   └── labyrinth_pb2.py     # Generated protobuf classes
│   └── labyrinth_pb2_grpc.py # Generated gRPC classes
├── server/
│   ├── server.py            # Server implementation
└── client/
    ├── client.py            # Client implementation
```

## Features

- **Grid-Based Navigation**: Move through an m × n grid with empty tiles, coin tiles, and wall tiles.
- **Health Management**: Start with 3 health points and lose health upon colliding with walls.
- **Coin Collection**: Collect coins to increase your score.
- **Spell System**: Use spells like Revelio to reveal tiles and Bombarda to destroy walls or coins.
- **Game Victory**: Reach the bottom-right corner of the labyrinth to win.

## RPC Methods

The following RPC methods are implemented in the server:

1. **GetLabyrinthInfo**: Returns the width and height of the labyrinth.
2. **GetPlayerStatus**: Provides the player's score, health points, current position, and remaining spells.
3. **RegisterMove**: Moves the player in a specified direction and returns the status of the move (success, failure, victory, or death).
4. **Revelio**: Reveals surrounding tiles of a specified type around a target tile, including the target itself.
5. **Bombarda**: Destroys specified tiles, converting them into empty tiles.


