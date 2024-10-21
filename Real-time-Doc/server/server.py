import grpc
import asyncio
import time
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

current_document ='''hi how r u ......blah blah
blah ''' # Start with empty document

def apply_change(document,change):
    if change.operation == "insert":
        return document[:change.position] + change.content + document[change.position:]
    elif change.operation == "delete":
        return document[:change.position] + document[change.position+1:]
    else:
        return document
    
class DocumentServicer(document_pb2_grpc.DocumentServiceServicer):
    def __init__(self):
        self.document = current_document
        self.clients = {}
        self.change_counter =0
        self.client_versions = {}
        self.change_history = []
        self.logger_stub = None  # Initialize logger stub
        self.last_logged_change = 0  # Track the last logged change
    
    async def InitializeDocument(self,request,context):
        client_id = request.client_id

        if client_id not in self.clients:
            self.clients[client_id] = asyncio.Queue()
        print(f"Client {client_id} connected")
        self.client_versions[client_id] = self.change_counter
        return document_pb2.Change(
            client_id = request.client_id,
            operation = "initialize",
            last_change = self.change_counter,
            content = self.document,
            position = 0
        )
    
    async def EditDocument(self,request,context):
        client_version = request.last_change
        # print(f"Client version: {client_version}")  
        # print("Old position: ",request.position)
        new_position = self.calculate_new_position(request.position,client_version)
        # print(f"New position: {new_position}")
        self.change_counter += 1
        if request.operation == "insert":
            self.document = self.document[:new_position] + request.content + self.document[new_position:]
        elif request.operation == "delete":
            self.document = self.document[:new_position] + self.document[new_position+1:]
        else:
            pass
        
        self.client_versions[request.client_id] = self.change_counter
        
        change = document_pb2.Change(
            client_id = request.client_id,
            operation = request.operation,
            last_change = self.change_counter,
            content = request.content,
            position = new_position
        )
        
        self.change_history.append(change)
        for queue in self.clients.values():
            await queue.put(change)
        
        return document_pb2.Ack(success=True,message="Edit applied successfully")
    
    def calculate_new_position(self,client_position,client_version):
        current_position = client_position
        
        for change in self.change_history:
            if change.last_change <= client_version:
                continue
            if change.operation == "insert":
                if change.position <= current_position:
                    current_position += len(change.content)
            elif change.operation == "delete":
                if change.position < current_position:
                    delete_end = change.position + len(change.content)
                    if delete_end <= current_position:
                        current_position -= len(change.content)
                    else:
                        current_position = change.position
  
        return max(0,min(current_position,len(self.document)))
    
    async def SyncDocument(self,request,context):
        
        client_id = request.client_id   
        last_change = request.last_change
        
        if client_id not in self.clients:
            self.clients[client_id] = asyncio.Queue()
        
        try:
            for change in self.change_history[last_change:]:
                yield change
            
            while True:
                change = await self.clients[client_id].get()
                print(f"Sending change to client {client_id}")
                print(f"Change: {change}")
                # if change.last_change > last_change:
                yield change
        except Exception:
            del self.clients[client_id]
            
            
    async def log_changes_to_logger(self):
        async with grpc.aio.insecure_channel('localhost:50052') as channel:
            self.logger_stub = document_pb2_grpc.LoggerServiceStub(channel)

            while True:
                if self.change_history and self.last_logged_change < self.change_counter:
                    change_stream = self.stream_new_changes()
                    await self.logger_stub.LogDocumentChange(change_stream)

                await asyncio.sleep(2)  # Push logs every 2 seconds

    async def stream_new_changes(self):
        for change in self.change_history[self.last_logged_change:]:
            yield change

        self.last_logged_change = self.change_counter
       

async def serve():
    server = grpc.aio.server()
    document_servicer = DocumentServicer()

    document_pb2_grpc.add_DocumentServiceServicer_to_server(document_servicer, server)
    # document_pb2_grpc.add_LoggerServiceServicer_to_server(LoggerServicer(), server)
    server.add_insecure_port('[::]:50051')
    
    await server.start()
    print(" Async Server started at port 50051")
    
    asyncio.create_task(document_servicer.log_changes_to_logger())
    await server.wait_for_termination()
    
if __name__ == '__main__':
    asyncio.run(serve())