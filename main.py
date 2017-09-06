# WoodchoppererRL
# A tiny little wood-chopping game
# originally developed by: @eigenbom 2016
# linux port / updates: @tsquar3d 2016

from collections import deque
import math
import os
import sys
import threading
import time
import random

import termios, atexit
from select import select

# save the terminal settings
fd = sys.stdin.fileno()
new_term = termios.tcgetattr(fd)
old_term = termios.tcgetattr(fd)

# new terminal setting unbuffered
new_term[3] = (new_term[3] & ~termios.ICANON & ~termios.ECHO)

# switch to normal terminal
def set_normal_term():
    termios.tcsetattr(fd, termios.TCSAFLUSH, old_term)

# switch to unbuffered terminal
def set_curses_term():
    termios.tcsetattr(fd, termios.TCSAFLUSH, new_term)

def putch(ch):
    sys.stdout.write(ch)

def getch():
    return sys.stdin.read(1)

def getche():
    ch = getch()
    putch(ch)
    return ch

def kbhit():
    dr,dw,de = select([sys.stdin], [], [], 0)
    return dr

atexit.register(set_normal_term)
set_curses_term()


class Blocks:
    """Block types."""
    air = 1
    rock = 2
    wood = 3
    rock = 4
    water = 5

def char_to_block(ch):
    return {
        ".": Blocks.air,
        "r": Blocks.rock,
        "w": Blocks.wood,
        "W": Blocks.water,
    }.get(ch, None)

def block_to_char(bl):
    return {
        Blocks.air: " ",
        Blocks.rock: "░",
        Blocks.wood: "¥",
    }.get(bl, "?")

def string_to_world(string, converter):
    world = []
    landmarks = {}
    row = 0
    for line in string.split("\n")[1:-1]:
        world_row = []
        for col, char in enumerate(line):
            bl = converter(char)
            if bl is None:
                l = landmarks.get(char, list())
                l.append((col, row))
                landmarks[char] = l
                world_row.append(Blocks.air)
            else:
                world_row.append(bl)
        world.append(world_row)
        row += 1
    return world, landmarks

world_string = """
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
rrr,,rr.,rrwwrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
rrr.@rr..wwwwrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
rrr..rr..wwwwwwwrrrrr........................................rr
rrr..rr.,.........rrr........r.............................rrrr
rrr..rr..rrrwwr..rrrrrr......rr....................rrrrrrrrrrrr
rrr..rr..r.,..w...rrrrr......rrrrrrrrrrrrrrr......rrrrrrrrrrrrr
rrr..rr.,...v,w...rrrrr......rrrrrrrrrrrrrrrr....rrrrrrrrrrrrrr
rrr........,,,r...rrrrr......rrrrrrrrrr................rrrrrrrr
rrr..rrrrrrrrrr..rrrr......rrrrrrrrrr....................rrrrrr
rrr.........,..,...........rrrrrrrrr......................rrrrr
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr.......................rrrrr
rrrrrrrrrrrrrrrrrrrrrrrrrrr...............................rrrrr
rrrrrrrrrrrrrrrrrrrrrrrwwwwwwwwwwwrrrrrrrrrrwwwwwwwwrrrrrrrrrrr
rrrrrrrrrrrrrrrrrrrrrrrrwwwwwwwwwwwrrrrrrrrwwwwwwwwwrrrrrrrrrrr
rrrrrrrrrrrrrrrrwrrrrwrrrrwwwwwwwwwrrrrrrrrrwwwwwww.rrrrrrrrrrr
rrrrrrrrrrrrrrrrwwwwwwwwwwwwwwwwwwwwrrrrrrrwwww.......rrrrrrrrr
rrrrrrrrrrrrrrwwwwwwwwwwwwwwwwwwwwwwwrrrrrrwww........wwwwrrrrr
rrrrrrrrrrrrrwwwwwwwwwwwwwww...........................wwwrrrrr
rrrrrrrrrrrwwwwwwwwwwwwwwwwww..........................wwwwrrrr
rrrwwwwwwwwwwwwwwwwwwwww.................................wwwrrr
rrrrrrwwwwwwwwwwwwwwrrrwwwwwwr.................rrr.........wwrr
rrrrrrrrrwwwwwwwwwwwrrrwwwwrrrrrw...............rr.........rrrr
rrrrrrrrrrrwwwwwwwwwrrwwwwwwwrrwww.........................rrrr
rrrrrrrrrrrrrrwwwwwwwrrrrrwwwwwwwww.........................rrr
rrrrrrrrrrrrrrrrrr.........wwwwwww..........................rrr
rrrrrrrrrrrrrrrrrrr..........wwww..........................rrrr
rrrrrrrrrrrrrrrrrrrr...........w.......................rrrrrrrr
rrrrrrrrrrrrrrrrrrrr......................rrrrr........rrrrrrrr
rrrrrrrrrrrrrrrrrrrrr.....................rrrrrrrr.....rrrrrrrr
rrrrrrrrrrrrrrrrrrrrr.............rrrrrrrrrrrrrr.........rrrrrr
rrrrrrrrrrrrrrrrrrrrrrrrrrr.......rrrrrrrrrrr.......rrrrrrrrrrr
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
"""

def worldGen():
    for x in range(0,406):
        world_string + random.choice(['d','.','w',',','v'])



world, landmarks = string_to_world(world_string, char_to_block)
print(landmarks)
world_dim = len(world[0]), len(world)
events = deque()
entities = list()
message_list = list()

class UIState:
    normal = 0
    target = 1
ui_state = UIState.normal
cursor = (0, 0)

class Entity(object):
    """An entity is a player, a mob, an item, a fireball, etc."""
    def __init__(self):
        # Location
        self.position = None

        # Contents, carrying, etc
        self.inventory = None
        self.in_inventory = None

        # Bigness, Material, etc
        self.is_solid = False # Only one solid entity is allowed per tile

        # Appearance
        self.appearance = "?"
        self.description = ""



player = Entity()
player.position = landmarks.get("@")[0]
player.appearance = "@"
player.is_solid = True
player.inventory = list()
player.description = "player"
entities.append(player)

axe = Entity()
axe.position = None
axe.appearance = "/"
axe.is_solid = False
axe.description = "axe"
entities.append(axe)

player.inventory.append(axe)
axe.in_inventory = player

for p in landmarks.get(",", list()):
    plant = Entity()
    plant.position = p
    plant.appearance = "√"
    plant.is_solid = False
    plant.description = "plant"
    entities.append(plant)

for p in landmarks.get("v", list()):
    plant = Entity()
    plant.position = p
    plant.appearance = "v"
    plant.is_solid = False
    plant.description = "reefer"
    entities.append(plant)

def world_to_string(tick):
    rows = []
    for y in range(world_dim[1]):
        row = []
        for x in range(world_dim[0]):
            if ui_state==UIState.target and tick%2 and cursor==(x,y):
                row.append('■')
            else:
                for e in entities:
                    if e.position == (x, y):
                        row.append(e.appearance)
                        break
                else:
                    row.append(block_to_char(world[y][x]))
        rows.append("".join(row))
    return "\n".join(rows)

# Math helpers
def clamp(x, a, b):
    if x < a:
        return a
    elif x > b:
        return b
    else:
        return x

update_lock = threading.Lock()

def read_input():

    with update_lock:
       if kbhit():
          ch = sys.stdin.read(1)
          #print(ch)
          return ch

       else:
          return None

def message(msg):
    message_list.append(msg)

shutdown_renderer = False

_print = print
def print(str = ""):
    for str in str.split("\n"):
        _print("    " + str)

def render():
    global world, player, entities, events, message_list, update_lock, shutdown_renderer
    # Render map and messages

    ticker = 0
    while True:
        with update_lock:
            if shutdown_renderer:
                return
            os.system('clear')
            title = "----WoodchopperRL----"
            cut = ticker % len(title)
            print()
            print(title[cut:len(title)] + title[0:cut])
            print()
            print(world_to_string(ticker))
            print()
            print("Carrying:")
            for i, item in enumerate(player.inventory):
                print("+ %s"%item.description)
            print()
            if len(message_list)>0:
                print("Messages:")
                for m in message_list:
                    print(m)
                print()

            if ui_state==UIState.normal:
                print("Command? (h for help)")
            elif ui_state==UIState.target:
                print("Targeting...")

            # Make sure everything is printed before pausing at end of frame
            sys.stdout.flush()

        # sleep
        ticker += 1
        time.sleep(0.1)

def main():
    global world, player, entities, events, message_list, shutdown_renderer, ui_state, cursor

    t = threading.Thread(target=render)
    t.daemon = True
    t.start()

    while True:

        command = None
        while command is None:
            command = read_input()

        # Input: System Command
        if command == 'q':
            if ui_state == UIState.target:
                with update_lock:
                    ui_state = UIState.normal
            else:
                with update_lock:
                    shutdown_renderer = True
                t.join()
                sys.exit(0)
        elif command in ['h', '?']:
            message("Help:")
            message("move  wsad")
            message("chop  space")
            message("get   g")
            message("quit  q")
            continue

        # Input: Direction Command
        # NB: These use the command_ext part
        direction = {
            'a': (-1, 0),  # Left arrow
            'd': (1, 0),   # Right arrow
            'w': (0, -1),  # Up arrow
            's': (0, 1)    # Down arrow
        }.get(command, None)

        if direction is not None:
            if ui_state==UIState.normal:
                # Attempt player move
                current_position = player.position
                target_position = player.position[0] + direction[0], player.position[1] + direction[1]
                events.append(("move", player, current_position, target_position))
            else:
                # Move cursor
                cursor = clamp(cursor[0] + direction[0], 0, world_dim[0]), clamp(cursor[1] + direction[1], 0, world_dim[1])

        if command==' ':
            if ui_state == UIState.normal:
                ui_state = UIState.target
                cursor = player.position
            else:
                # was in target mode, try to chop target
                ui_state = UIState.normal
                events.append(("chop", player, cursor))

        if command=='g':
            events.append(("get", player))

        # TODO: Input: Handle other commands

        with update_lock:
            message_list.clear()

            # TODO: Update World: Simulation

            # TODO: Update World: Entities
            for e in entities:
                pass

            # Update World: Events
            while events:
                ev = events.popleft()
                if ev[0] == "move":
                    _, entity, position, target_position = ev
                    # Check target position is in bounds
                    out_of_bounds = not (0 <= target_position[0] < world_dim[0] and 0 <= target_position[1] < world_dim[1])
                    if out_of_bounds:
                        message("Can't walk off the map!")
                    else:
                        tile = world[target_position[1]][target_position[0]]
                        if tile == Blocks.air:
                            entity.position = target_position
                        else:
                            message("Thud!")
                elif ev[0] == "chop":
                    _, entity, target = ev
                    out_of_bounds = not (0 <= target[0] < world_dim[0] and 0 <= target[1] < world_dim[1])
                    if out_of_bounds:
                        message("There's nothing here to chop!")
                    else:
                        dp = target[0] - entity.position[0], target[1] - entity.position[1]
                        correct_distance = abs(dp[0]) + abs(dp[1]) == 1
                        if correct_distance:
                            tile = world[target[1]][target[0]]
                            if tile == Blocks.wood:
                                world[target[1]][target[0]] = Blocks.air
                                lumber = Entity()
                                lumber.position = target
                                lumber.appearance = "="
                                lumber.is_solid = False
                                lumber.description = "lumber"
                                entities.append(lumber)
                            elif tile == Blocks.air:
                                message("Nothing to chop there!")
                            elif tile == Blocks.rock:
                                message("Can't chop stone!")
                        else:
                            message("Can't chop there!")
                elif ev[0] == "get":
                    _, entity = ev
                    for e in entities:
                        if e is not entity and e.position==entity.position:
                            # Pickup items and put in inventory
                            e.position = None
                            e.in_inventory = entity
                            entity.inventory.append(e)


            # Update World: Description
            for e in entities:
                if e is not player and e.position==player.position:
                    message("A(n) %s is here."%e.description)


if __name__ == "__main__":
    main()
