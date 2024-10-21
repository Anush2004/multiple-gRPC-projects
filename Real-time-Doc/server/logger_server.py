import grpc
import asyncio
import time
from concurrent import futures
import os
from datetime import datetime

pwd = os.getcwd()
pwd = pwd.split('/')
pwd = '/'.join(pwd[:-1])
pwd = pwd + '/protofiles'
import sys
sys.path.append(pwd)
import document_pb2
import document_pb2_grpc

class LoggerServicer(document_pb2_grpc.LoggerService):
    async def LogDocumentChange(self, request_iterator, context):
        log_file = "log.txt" 

        with open(log_file, "a") as f:
            async for change in request_iterator:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                log_entry = (
                    f"\n{'='*40}\n"
                    f"Timestamp: {timestamp}\n"
                    f"Client ID: {change.client_id}\n"
                    f"Operation: {change.operation}\n"
                    f"Content: '{change.content}'\n"
                    f"Position: {change.position}\n"
                    f"Last Change: {change.last_change}\n"
                    f"{'='*40}\n"
                )
                
                f.write(log_entry)
                print(f"Logged change:\n{log_entry}")
            
        return document_pb2.Ack(success=True, message="Changes logged successfully")



async def serve():
    server = grpc.aio.server() 
    document_pb2_grpc.add_LoggerServiceServicer_to_server(LoggerServicer(), server)
    
    server.add_insecure_port('[::]:50052') 
    await server.start()
    print("Logger gRPC server started at port 50052")
    
    # Wait for server termination
    await server.wait_for_termination()


if __name__ == '__main__':
    asyncio.run(serve())