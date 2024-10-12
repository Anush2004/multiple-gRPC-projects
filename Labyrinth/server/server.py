import grpc
import random
from concurrent import futures
import os
pwd = os.getcwd()
pwd = pwd.split('/')
pwd = '/'.join(pwd[:-1])
pwd = pwd + '/protofiles'
import sys
sys.path.append(pwd)
import labyrinth_pb2
import labyrinth_pb2_grpc

class LabyrinthServicer(labyrinth_pb2_grpc.LabyrinthServicer):
    def __init__(self):
        # initialize the labyrinth
        self.width = 5
        self.height = 5
        self.labyrinth = [[0 for j in range(self.width)] for i in range(self.height)]
        self.player_score = 0
        self.player_position = (0, 0)
        self.remaining_spells = 3
        self.player_health = 3
        self.labyrinth = self.generate_labyrinth(width = self.width, height = self.height)
    
    def generate_labyrinth(self, width, height):
        labyrinth =[]
        
        for i in range(width):
            row = []
            for j in range(height):
                if i == 0 and j ==0:
                    row.append('empty')
                elif i == width-1 and j == height-1:
                    row.append('empty')
                else:
                    row.append(random.choice(['empty','coin']))
            labyrinth.append(row)
        y=0
        count =0
        for i in range(width):
            while(labyrinth[y][i] =='wall' or count == 0):
                if i == 0:
                    y = random.randint(1, height-1)
                elif i == width-1:
                    y = random.randint(0, height-2)
                else:
                    y = random.randint(0, height-1)
                count += 1
            if i == 0 and y == 0:
                continue
            if i == width-1 and y == height-1:
                continue
            labyrinth[i][y] = 'wall'
            count = 0
            y=0
        print(labyrinth)
        return labyrinth 
        
    def GetLabyrinthInfo(self,request,context):
        return labyrinth_pb2.GetLabyrinthInfoResponse(width = self.width,height = self.height)
    
    def GetPlayerStatus(self,request,context):
        return labyrinth_pb2.GetPlayerStatusResponse(
            score = self.player_score,
            health = self.player_health,
            position = f"{self.player_position[0]},{self.player_position[1]}",
            remaining_spells = self.remaining_spells
        )
    
    def RegisterMove(self,request,context):
        direction = request.direction
        x,y = self.player_position
        if direction == "up" :
            x-=1
        elif direction == "down":
            x+=1
        elif direction == "left":
            y-=1
        elif direction == "right":
            y+=1
        else:
            return labyrinth_pb2.RegisterMoveResponse(status = "Invalid Move")
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return labyrinth_pb2.RegisterMoveResponse(status = "Out of Bounds")
        
        if (x,y) == (self.width-1,self.height-1):
            return labyrinth_pb2.RegisterMoveResponse(status = "Victory! Reached the end of the labyrinth")
        
        tile = self.labyrinth[x][y]
        if tile == 'wall':
            self.player_health -= 1
            if(self.player_health == 0):
                return labyrinth_pb2.RegisterMoveResponse(status = "Game Over! Health reduced to 0")
            
            return labyrinth_pb2.RegisterMoveResponse(status = "Ouch! Hit a wall.. Health reduced by 1")
        elif tile == 'coin':
            self.player_score += 1
            self.labyrinth[x][y] = 'empty'
            self.player_position = (x,y)
            return labyrinth_pb2.RegisterMoveResponse(status = "Yahoo! Found a coin.. Score increased by 1")
        elif tile == 'empty':
            self.player_position = (x,y)
            return labyrinth_pb2.RegisterMoveResponse(status = "Moved to empty tile")
        
        return labyrinth_pb2.RegisterMoveResponse(status = "Unknown Error")
    
    def Revelio(self,request,context):
        if self.remaining_spells == 0:
            yield labyrinth_pb2.RevelioResponse(target_positions="No spells left")
            return
    
        target_position = request.target_position
        target_position = target_position.split(',')
        target_x, target_y = int(target_position[0]), int(target_position[1])
        self.remaining_spells -= 1

        tile_type = request.tile_type
        revealed_positions = []
        for i in range(-1,2):
            for j in range(-1,2):
                x = target_x  + i
                y = target_y + j
                if x >= 0 and x < self.width and y >= 0 and y < self.height:
                    if self.labyrinth[x][y] == tile_type:
                        revealed_positions.append(f"{x},{y}")

        if self.labyrinth[target_x][target_y] == tile_type:
            revealed_positions.append(f"{x},{y}")
        for position in revealed_positions:
            yield labyrinth_pb2.RevelioResponse(target_positions=position)
    
    def Bombarda(self,requests,context):
        if self.remaining_spells == 0:
            return labyrinth_pb2.BombardaResponse(result = "No spells left")
        self.remaining_spells -= 1
        for request in requests:
            position = request.target_positions
            x,y = map(int,position.split(','))
            if 0<=x<self.width and 0<=y<self.height:
                if self.labyrinth[x][y] in ['wall','coin']:
                    self.labyrinth[x][y] = 'empty'
                    
        return labyrinth_pb2.BombardaResponse(result = "Spell casted successfully")
           
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    labyrinth_pb2_grpc.add_LabyrinthServicer_to_server(LabyrinthServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server listening on port 50051")
    server.wait_for_termination()
    
if __name__ == '__main__':
    serve()