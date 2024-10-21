# README

## Project Overview
This project consists of a collaborative document editing system implemented using gRPC, allowing multiple clients to edit a document in real time. The system includes a main server to manage client connections and document changes, a logger server to log changes made by clients, and two client applications to interact with the document.

## Directory Structure
```
/project-root
├── protofiles/          # Contains gRPC protocol definition files
│   ├── document.proto   # Protocol definition for document services
├── server/              # Contains the main server and logger server
│   ├── server.py        # Main server implementation
│   ├── logger_server.py  # Logger server implementation
├── clients/             # Contains client implementations
│   ├── client.py        # Client implementation
└── toBuild.sh           # Bash script to build and run the project
```

## Requirements
- Python 3.7 or higher
- `grpcio`
- `grpcio-tools`

You can install the required packages using:
```bash
pip install grpcio grpcio-tools
```

## Setup Instructions
1. **Compile the Proto Files**
   - The `toBuild.sh` script will automatically compile the proto files, generating the necessary Python files for gRPC.
   - Run the script:
     ```bash
     ./toBuild.sh
     ```

2. **Running the Servers and Clients**
   - The `toBuild.sh` script will launch the logger server, main server, and two client instances in separate terminal windows.

## Features
- **Real-time Document Editing:** Multiple clients can edit a document simultaneously. Changes are synced in real time.
- **Change Logging:** The logger server records all changes made to the document for auditing and debugging.
- **Client Management:** Each client maintains its state and syncs with the server to get the latest changes.

## Quirks and Known Issues
- **Error Handling:** If the main server crashes, clients will show a connection error. However, they cannot automatically reconnect; users must restart the clients manually.
- **Document Size:** Very large documents may lead to performance degradation. It's recommended to keep document sizes manageable.
- **Curses Interface:** The client uses the `curses` library for a terminal-based interface, which may have limitations based on terminal settings.
- **Limited Input Handling:** The current implementation primarily handles basic text editing operations. Advanced features like undo/redo, formatting, or special character inputs are not supported yet. Users should keep this in mind when editing documents.
- **Terminal Compatibility:** The use of `gnome-terminal` in the `toBuild.sh` script means that this setup is primarily designed for Linux environments. Users on other operating systems may need to adjust the script to use their terminal applications.
