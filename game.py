import pygame
import threading

from src.ship import *
from src.client import *

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
RES = [1280, 720]
FPS = 30

BG_COLOR = [255, 255, 255]
ENB_COLOR = [232, 164, 82]
PLB_COLOR = [82, 164, 232]
ENL_COLOR = [c - 30 for c in ENB_COLOR]
PLL_COLOR = [c - 30 for c in PLB_COLOR]

def translate(v1: list, v2: list) -> list:
    return [v1[i] + v2[i] for i in range(len(v1))]

def listen_to_server(client):
    global recv_msg
    while client.await_messages:
        recv_msg = client.get_new_msg()

pygame.init()
display = pygame.display.set_mode(RES)
clock = pygame.time.Clock()
win_font = pygame.font.SysFont("Comic Sans MS", 64)
lose_text = win_font.render("You lost, better luck next time!", True, [255, 128, 128], [0, 0, 0])
win_text = win_font.render("You won! Congratulations!", True, [128, 255, 128], [0, 0, 0])

bd_separator = 50
bd_size = 8
bd_scale = 64
player_turn = True
recv_msg = None
msgs_to_send = []
result = None

plb_topleft = [
    RES[0] // 2 - bd_size * bd_scale - bd_separator,
    (RES[1] - bd_size * bd_scale) // 2
]
enb_topleft = [
    RES[0] // 2 + bd_separator,
    (RES[1] - bd_size * bd_scale) // 2
]
_pos = translate(plb_topleft, [-10, -10])
plb_bg_r = pygame.Rect(_pos[0], _pos[1], bd_size * bd_scale + 20, bd_size * bd_scale + 20)
_pos = translate(enb_topleft, [-10, -10])
enb_bg_r = pygame.Rect(_pos[0], _pos[1], bd_size * bd_scale + 20, bd_size * bd_scale + 20)
del _pos

shots = []
ships = []
ships.append(Ship([2, 1], 4, 'DOWN'))
ships.append(Ship([4, 6], 2, 'RIGHT'))

# connect to server
print("Connecting...")

IP = '192.168.1.60'
client = Client()
client.connect(IP, 5050)

listener = threading.Thread(target=listen_to_server, args=(client, ))
listener.start()

print(f"Connected to {client.connected_addr}!")

run = True
while run:

    # UPDATE ---------------------------------- #

    clock.tick(FPS)

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            run = False
        elif e.type == pygame.MOUSEBUTTONDOWN and player_turn:
            mouse_pos = pygame.mouse.get_pos()
            if not player_turn or result:
                print(mouse_pos)
                continue
            if enb_topleft[0] < mouse_pos[0] < enb_topleft[0] + bd_size * bd_scale and enb_topleft[1] < mouse_pos[1] < enb_topleft[1] + bd_size * bd_scale:
                enb_mouse_pos = [p//bd_scale for p in translate(mouse_pos, [-enb_topleft[0], -enb_topleft[1]])]
                shots.append([translate([p * bd_scale + bd_scale // 2 for p in enb_mouse_pos], enb_topleft), False])
                msgs_to_send.append(f"ATK {enb_mouse_pos[0]} {enb_mouse_pos[1]}")
                player_turn = False
    
    # SERVER COMMS ---------------------------- #

    # send to server
    if msgs_to_send:
        m = ';'.join(msgs_to_send)
        client.send(m)
        print(m)
        msgs_to_send = []

    # recv from server
    if recv_msg:
        recv_msgs = recv_msg.split(';')
        print(recv_msgs)
        for m in recv_msgs:
            m = m.split(' ')
            if m[0] == "ATK":
                player_turn = True
                pos = [int(m[1]), int(m[2])]
                print(pos)
                shots.append([translate([p * bd_scale + bd_scale // 2 for p in pos], plb_topleft), False])
                for i, s in enumerate(ships):
                    if not s.isHit(pos):
                        continue
                    shots[-1][1] = True
                    for p in s.parts:
                        if p[1] > 0:
                            break
                    else:
                        del ships[i]
                        if len(ships) == 0:
                            msgs_to_send.append("ENEMY_WIN")
                            result = 'LOSE'
                    break
                msgs_to_send.append(f"ATK_RESP {1 if shots[-1][1] == True else 0}")

            elif m[0] == "ATK_RESP":
                if int(m[1]) == 1:
                    shots[-1][1] = True

            elif m[0] == "ENEMY_WIN":
                result = 'WIN'
                
        recv_msg = None

    # DRAW ------------------------------------ #

    display.fill(BG_COLOR)

    # boards
    for b in [[PLL_COLOR, PLB_COLOR, plb_topleft, plb_bg_r], [ENL_COLOR, ENB_COLOR, enb_topleft, enb_bg_r]]:
        pygame.draw.rect(display, b[1], b[3])
        for l in range(1, bd_size):
            pygame.draw.line( # vertical
                display, b[0], 
                translate(b[2], [l * bd_scale, 0]),
                translate(b[2], [l * bd_scale, bd_size * bd_scale])
            )
            pygame.draw.line( # horizontal
                display, b[0], 
                translate(b[2], [0, l * bd_scale]),
                translate(b[2], [bd_size * bd_scale, l * bd_scale])
            )
    
    # ships
    for s in ships:
        s.draw(display, plb_topleft, bd_scale)

    # shots
    for s in shots:
        shot_color = [255, 255, 255]
        if s[1]:
            shot_color = [250, 0, 0]
        pygame.draw.circle(display, shot_color, s[0], bd_scale * 0.4)

    # result
    if result == 'WIN':
        display.blit(win_text, [(RES[0] - win_text.get_width())//2, (RES[1] - win_text.get_height())//2])
    elif result == 'LOSE':
        display.blit(lose_text, [(RES[0] - lose_text.get_width())//2, (RES[1] - lose_text.get_height())//2])

    pygame.display.update()

client.disconnect()
pygame.quit()
