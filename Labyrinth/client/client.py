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

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def print_labyrinth(labyrinth,player_position):
    for i in range(len(labyrinth)):
        row = []
        for j in range(len(labyrinth[i])):
            if (i, j) == player_position:
                row.append('P')  # Player position
            elif labyrinth[i][j] == '*':
                row.append('.')
            elif labyrinth[i][j] == 'empty':
                row.append('E')
            elif labyrinth[i][j] == 'coin':
                row.append('C')
            elif labyrinth[i][j] == 'wall':
                row.append('W')
        print(' '.join(row))
    print()
    
    
def get_move():
    move = input("Enter move (up, down, left, right) or 'spell':").strip().lower()
    if move not in ['up', 'down', 'left', 'right', 'spell']:
        print("Invalid move. Try again.")
        return get_move()
    return move


def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = labyrinth_pb2_grpc.LabyrinthStub(channel)
        
        # Get labyrinth info
        response = stub.GetLabyrinthInfo(labyrinth_pb2.GetLabyrinthRequest())
        print(f"Labyrinth Size: {response.width}x{response.height}")
        width ,height = response.width, response.height
        
        # intialize labyrinth
        labyrinth = [['*' for j in range(width)] for i in range(height)]
        
        # Get player status
        player_status = stub.GetPlayerStatus(labyrinth_pb2.GetPlayerStatusRequest())
        print('Your Starting Health is:', player_status.health) 
            
        player_position = tuple(map(int, player_status.position.split(',')))
        labyrinth[player_position[0]][player_position[1]] = 'empty'

        # print('Your Starting Position is:', player_position)
        while True:
            # clear_terminal()
            print(f"Score: {player_status.score} | Health: {player_status.health} | Remaining Spells: {player_status.remaining_spells}")
            print_labyrinth(labyrinth, player_position)
            move = get_move()
            
            if move in ['up', 'down', 'left', 'right']:
                move_request = labyrinth_pb2.RegisterMoveRequest(direction = move)
                move_response = stub.RegisterMove(move_request)
                
                if move_response.status == 'Invalid Move':
                    print('Invalid Move. Try again.')
                    continue
                if move_response.status == 'Out of Bounds':
                    print('Out of Bounds. Try again.')
                    continue
                if move_response.status == 'Ouch! Hit a wall.. Health reduced by 1':
                    new_position = list(player_position)
                    if move == 'up':
                        new_position[0] -= 1
                    elif move == 'down':
                        new_position[0] += 1
                    elif move == 'left':
                        new_position[1] -= 1
                    elif move == 'right':
                        new_position[1] += 1
                    print('Ouch! Hit a wall.. Health reduced by 1')
                    labyrinth[new_position[0]][new_position[1]] = 'wall'
                    
                if move_response.status == 'Yahoo! Found a coin.. Score increased by 1':
                    print('Yahoo! Found a coin .. Score increased by 1')
                    
                if move_response.status == 'Game Over! Health reduced to 0':
                    print('Game Over! Health reduced to 0')
                    break
                if move_response.status == 'Victory! Reached the end of the labyrinth':
                    print('Victory! Reached the end of the labyrinth')
                    break
            elif move == 'spell':
                # Use Revelio or Bombarda spell
                if player_status.remaining_spells == 0:
                    print("No spells left.")
                    continue
                spell_type = input("Choose spell (revelio, bombarda):").strip().lower()
                if spell_type not in ['revelio', 'bombarda']:
                    print("Invalid spell. Try again.")
                    continue
                if spell_type == 'revelio':
                    x = int(input("Enter x coordinate to reveal:"))
                    y = int(input("Enter y coordinate to reveal:"))
                    tile_type = input("Enter tile type (empty, wall, coin):").strip().lower()
                    
                    if tile_type not in ['empty', 'wall', 'coin']:
                        print("Invalid tile type. Try again.")
                        continue
                    revelio_request = labyrinth_pb2.RevelioRequest(target_position = f"{x},{y}", tile_type = tile_type) 
                    for response in stub.Revelio(revelio_request):
                        position = response.target_positions
                        x,y = map(int,position.split(',')) 
                        labyrinth[int(x)][int(y)] = tile_type
                elif spell_type == 'bombarda':
                    print('Enter 3 different x coordinate to destroy')
                    p = []
                    
                    while(len(p) < 3):
                        x = int(input("Enter x coordinate to destroy: "))
                        if x < 0 or x >= height:
                            print("Invalid x coordinate. Try again.")
                            continue
                        y = int(input("Enter y coordinate to destroy: "))
                        if y < 0 or y >= width:
                            print("Invalid y coordinate. Try again.")
                            continue
                        labyrinth[int(x)][int(y)] = 'empty'
                        p.append(f"{x},{y}")
                        
                        def bombarda_request_generator():
                            for pos in p:
                                yield labyrinth_pb2.BombardaRequest(target_positions=pos)

                    response = stub.Bombarda(bombarda_request_generator())
                    if response.result == 'Spell casted successfully':
                        print('Spell casted successfully')
                    
            player_status = stub.GetPlayerStatus(labyrinth_pb2.GetPlayerStatusRequest())
            player_position = tuple(map(int, player_status.position.split(',')))
            labyrinth[player_position[0]][player_position[1]] = 'empty'
                    
            
if __name__ == '__main__':
    run()