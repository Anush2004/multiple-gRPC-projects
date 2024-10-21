import grpc
import curses

from flask import Flask, request, jsonify
import uuid
import asyncio
from concurrent import futures
import os
pwd = os.getcwd()
pwd = pwd.split('/')
pwd = '/'.join(pwd[:-1])
pwd = pwd + '/protofiles'
import sys
sys.path.append(pwd)
import document_pb2
import document_pb2_grpc

# app = Flask(__name__)
current_document = ""  # Start with an empty document
class DocumentClient:
    def __init__(self):
        self.client_id = str(uuid.uuid4())
        self.channel = grpc.aio.insecure_channel('localhost:50051')
        self.stub = document_pb2_grpc.DocumentServiceStub(self.channel)
        self.last_change = 0
        self.document = current_document
        
    def get_flat_cursor_index(self, cursor_x, cursor_y):
        return sum(len(line) + 1 for line in self.document.split('\n')[:cursor_y]) + cursor_x

    def convert_flat_to_2d(self, flat_index):
        lines = self.document.split('\n')
        total_length = 0
        for y, line in enumerate(lines):
            total_length += len(line) + 1  # +1 for the newline character
            if total_length > flat_index:
                return (y, flat_index - (total_length - len(line) - 1))
        return (len(lines) - 1, len(lines[-1]))  # Return last position if out of bounds

    async def initialize_document(self,stdscr):
        try:
            request = document_pb2.Change(client_id=self.client_id, operation="initialize",last_change=self.last_change, content="", position=0)
            response = await self.stub.InitializeDocument(request)
            self.last_change = response.last_change
            # print(f"Last change: {self.last_change}")
            self.document = response.content
            # print(f"Document initialized: {self.document}")
            self.sync_task = asyncio.create_task(self.sync_document())
        except grpc.aio.AioRpcError as e:
            stdscr.addstr(6, 0, f"Error: Unable to connect to the server. {e.code().name}")
            stdscr.refresh()
            await asyncio.sleep(20)
            return False
        return True
        
    async def edit_document(self, stdscr, operation, content, position):
        try:
            request = document_pb2.Change(client_id=self.client_id, operation=operation, last_change=self.last_change, content=content, position=position)
            response = await self.stub.EditDocument(request)
        except grpc.aio.AioRpcError as e:
            stdscr.addstr(6, 0, f"Error: Could not apply edit. {e.code().name}")
            stdscr.refresh()
            await asyncio.sleep(20)
            return
        # print(f"Edit response: {response}")
        
    async def sync_document(self):
        sync_request = document_pb2.SyncRequest(client_id=self.client_id, last_change=self.last_change)
        try:
            async for response in self.stub.SyncDocument(sync_request):
                # print(response)
                self.apply_change(response)
                self.last_change = response.last_change
        except asyncio.CancelledError:
            print("Syncing task cancelled.")
        except grpc.aio.AioRpcError as e:
            print(f"Sync failed: {e.code().name}")
        finally:
            print("Exiting sync task.")
            
    def apply_change(self, change):
        global cursor_x, cursor_y
        if change.operation == "insert":
            self.document = self.document[:change.position] + change.content + self.document[change.position:]
            cursor_offset = len(change.content)
            flat_index = self.get_flat_cursor_index(cursor_x, cursor_y)
            flat_index +=  cursor_offset
            cursor_y, cursor_x = self.convert_flat_to_2d(flat_index)
        elif change.operation == "delete":
            self.document = self.document[:change.position] + self.document[change.position + 1:]
            cursor_offset = -1
            flat_index = self.get_flat_cursor_index(cursor_x, cursor_y)
            flat_index +=  cursor_offset
            cursor_y, cursor_x = self.convert_flat_to_2d(flat_index)

client = DocumentClient()
# Background task to sync the document
sync_task = None

# @app.route('/initialize', methods=['GET'])
# async def initialize_document():
#     await client.initialize_document()
#     return jsonify({"document": client.document})

# @app.route('/edit', methods=['POST'])
# async def edit_document():
#     data = request.json
#     operation = data.get("operation", "insert")
#     content =   data.get("content","")
#     position = data.get("position",0)
#     await client.edit_document(operation, content, position)
#     return jsonify({
#         "message": "Edit successful",
#         "document": client.document
#     })
    
# @app.route('/sync/start', methods=['POST'])
# async def start_sync():
#     global sync_task
#     if sync_task and not sync_task.cancelled():
#         return jsonify({"message": "Sync task already running"})
    
#     sync_task = asyncio.create_task(client.sync_document())
#     return jsonify({"message": "Sync task started"})

async def run_client(stdscr):
    global cursor_x, cursor_y
    cursor_x = 0
    cursor_y = 0

    client = DocumentClient()
    if not await client.initialize_document(stdscr):
        return

    # Setup curses
    stdscr.nodelay(True)  # Non-blocking input
    # stdscr.keypad(True)   # Enable special keys
    curses.curs_set(1)     # Show cursor
    # Main editing loop
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Interactive Document Editor (Press F9 to quit)")
        # Display the document
        lines = client.document.split('\n')
        for idx, line in enumerate(lines):
            stdscr.addstr(idx + 2, 0, line)
        # Move the cursor to the correct position
        stdscr.move(cursor_y + 2, cursor_x)

        # Refresh to show changes
        stdscr.refresh()

        # Get user input
        key = stdscr.getch()
        if key == -1:
            # No input, continue loop
            await asyncio.sleep(0.1)
            continue
        elif key == 27:  # ESC or F9 to quit
            break
        elif key in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT):
            # Handle arrow keys for navigation
            if key == curses.KEY_UP and cursor_y > 0:
                cursor_y -= 1
                cursor_x = min(cursor_x, len(lines[cursor_y]))
            elif key == curses.KEY_DOWN and cursor_y < len(lines) - 1:
                cursor_y += 1
                cursor_x = min(cursor_x, len(lines[cursor_y]))
            elif key == curses.KEY_LEFT and cursor_x > 0:
                cursor_x -= 1
            elif key == curses.KEY_RIGHT and cursor_x < len(lines[cursor_y]):
                cursor_x += 1
                
        elif key == curses.KEY_BACKSPACE or key == 127:  # Handle backspace/delete
            if cursor_x > 0:
                # cursor_x -= 1
                index = sum(len(line) + 1 for line in lines[:cursor_y]) + cursor_x -1
                await client.edit_document(stdscr,"delete", "", index)
            else:
                if cursor_y > 0:
                    # cursor_y -= 1
                    # cursor_x = len(lines[cursor_y])
                    index = sum(len(line) + 1 for line in lines[:(cursor_y-1)]) + len(lines[cursor_y-1])
                    await client.edit_document(stdscr,"delete", "", index)
        elif key == 10:  # Handle Enter (new line)
            index = sum(len(line) + 1 for line in lines[:cursor_y]) + cursor_x
            await client.edit_document(stdscr,"insert", "\n", index)
            
            # cursor_y += 1
            # cursor_x = 0
        else:
            # Handle character input (insertion)
            try:
                char = chr(key)
                index = sum(len(line) + 1 for line in lines[:cursor_y]) + cursor_x
                await client.edit_document(stdscr,"insert", char, index)
                # cursor_x += 1
            except ValueError:
                pass  # Ignore invalid input

        # Real-time document syncing
        # await client.sync_document()


def start_async_loop():
    curses.wrapper(lambda stdscr: asyncio.run(run_client(stdscr)))


if __name__ == '__main__':
    start_async_loop()

    