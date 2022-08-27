import pygame
import threading
import random
import os

from src.ship import *
from src.client import *
from src.server import *

IP = input("Connect to IP (leave empty if host):").strip()
RES = [1280, 720]
R_SCL = RES[0] / 1280
FPS = 30

BG_COLOR = [0, 0, 35]
ENL_COLOR = [80, 0, 0]
MISSILE_COLOR = [24, 89, 55]
PLL_COLOR = [0, 80, 0]

def is_ship_on_board(ship: Ship) -> bool:
    for p in ship.parts:
        if not 0 <= p[0][0] < bd_size or not 0 <= p[0][1] < bd_size:
            return False
    return True

def translate(v1: list, v2: list) -> list:
    return [v1[i] + v2[i] for i in range(len(v1))]

def listen_to_server(client):
    global recv_msg
    while client.await_messages:
        recv_msg = client.get_new_msg()

pygame.init()
display = pygame.display.set_mode(RES)
clock = pygame.time.Clock()
win_font = pygame.font.SysFont("Comic Sans MS", int(64 * R_SCL))
notif_font = pygame.font.SysFont("Comic Sans MS", int(32 * R_SCL))
notif_text = notif_font.render("", False, [255, 255, 255], [0, 0, 0])
lose_text = win_font.render("| || this is so sad || |_", True, [255, 128, 128], [0, 0, 0])
win_text = win_font.render("gg ez", True, [128, 255, 128], [0, 0, 0])
server_info_text = None

volume = 0
restart_timer = -1
ship_units = [4, 3, 3, 2, 2, 1]
bd_separator = 50 * R_SCL
bd_size = int(8 * R_SCL)
bd_scale = int(64 * R_SCL)
notif_timer = 0
bd_sisc = bd_scale * bd_size
player_turn = False
reset_sound = False
recv_msg = None
msgs_to_send = []
result = None
mouse_in_enb = False
enb_mouse_pos = [0, 0]
mouse_in_plb = False
plb_mouse_pos = [0, 0]
is_ready = {
    "client": False,
    "player": False
}
stage = 1 # 1 = place; 2 = play

plb_topleft = [
    RES[0] // 2 - bd_sisc - bd_separator,
    (RES[1] - bd_sisc) // 2
]
enb_topleft = [
    RES[0] // 2 + bd_separator,
    (RES[1] - bd_sisc) // 2
]
_pos = translate(plb_topleft, [-10, -10])
_pos = translate(enb_topleft, [-10, -10])
del _pos

pygame.mixer.music.load('src/music/bgm.ogg')
pygame.mixer.music.set_volume(volume)
pygame.mixer.music.play(-1)

sounds = {}
for f in os.listdir('src/sfx'):
    f = os.path.splitext(f)
    if f[-1] == '.wav':
        sounds[f[0]] = pygame.mixer.Sound(f'src/sfx/{f[0]}.wav')
        sounds[f[0]].set_volume(volume)

sprites = {}
for f in os.listdir('src/sprites'):
    f = os.path.splitext(f)
    if f[-1] == '.png':
        sprites[f[0]] = pygame.image.load(f'src/sprites/{f[0]}.png').convert_alpha()
for k in ['1', '2', '3', '4']:
    sprites[k] = pygame.transform.scale(sprites[k], [int(sprites[k].get_width() * bd_scale/300), int(sprites[k].get_height() * bd_scale/300)])

missiles = []
shots = []
ships = []
banned_positions = set()
l = ship_units[len(ships)]
preview_ship = Ship(sprites[str(l)], [-100, -100], l, 0)

server = None
client = Client()

run = True
while run:

    # UPDATE ---------------------------------- #

    clock.tick(FPS)

    if stage == 1 and PLL_COLOR[1] < 128:
        PLL_COLOR[1] += (128 - PLL_COLOR[1]) * 0.05
        ENL_COLOR[0] -= (128 - PLL_COLOR[1]) * 0.05
    elif stage == 2 and ENL_COLOR[0] < 128:
        ENL_COLOR[0] += (128 - ENL_COLOR[1]) * 0.05
        PLL_COLOR[1] -= (128 - ENL_COLOR[1]) * 0.05

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            run = False
        
        elif e.type == pygame.MOUSEBUTTONDOWN:
            
            if client.connected_addr and stage == 1 and mouse_in_plb and not is_ready['client'] and is_ship_on_board(preview_ship):
                for p in preview_ship.parts:
                    if f'{p[0][0]};{p[0][1]}' in banned_positions:
                        break
                else:
                    ships.append(preview_ship)
                    for p in preview_ship.parts:
                        p = p[0]
                        for x in [p[0] - 1, p[0], p[0] + 1]:
                            for y in [p[1] - 1, p[1], p[1] + 1]:
                                banned_positions.add(f"{x};{y}")
                    if len(ships) < len(ship_units):
                        l = ship_units[len(ships)]
                        preview_ship = Ship(sprites[str(l)], [-1, -1], l, 0)
                    else:
                        msgs_to_send.append("READY")
                        is_ready["client"] = True
                        if is_ready["player"]:
                            stage = 2
            
            elif stage == 2 and mouse_in_enb and player_turn and enb_mouse_pos:
                shots.append([translate([p * bd_scale + bd_scale // 2 for p in enb_mouse_pos], enb_topleft), False])
                msgs_to_send.append(f"ATK {int(enb_mouse_pos[0])} {int(enb_mouse_pos[1])}")
                
                trg = shots[-1][0]
                for s in ships: # shoot missile from each ship left
                    src = translate([p * bd_scale + bd_scale // 2 for p in random.choice(s.parts)[0]], plb_topleft)
                    a = 0.001
                    b = (src[1] - trg[1] - a * (src[0]**2 - trg[0]**2)) / (src[0] - trg[0])
                    c = src[1] - a * src[0]**2 - b * src[0]
                    missiles.append([a, b, c, src[0], trg[0], random.uniform(0.5, 1.5)])
                player_turn = False
        
        elif e.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            mouse_in_enb =  enb_topleft[0] < mouse_pos[0] < enb_topleft[0] + bd_sisc and enb_topleft[1] < mouse_pos[1] < enb_topleft[1] + bd_sisc
            mouse_in_plb = plb_topleft[0] < mouse_pos[0] < plb_topleft[0] + bd_sisc and plb_topleft[1] < mouse_pos[1] < plb_topleft[1] + bd_sisc
            
            if stage == 1 and mouse_in_plb and not is_ready['client']:
                plb_mouse_pos = [p//bd_scale for p in translate(mouse_pos, [-plb_topleft[0], -plb_topleft[1]])]
                preview_ship.changePos(plb_mouse_pos)
            
            elif stage == 2 and mouse_in_enb:
                enb_mouse_pos = [p//bd_scale for p in translate(mouse_pos, [-enb_topleft[0], -enb_topleft[1]])]

        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_LEFT:
                preview_ship.changeDirection(preview_ship.direction - 90)
            elif e.key == pygame.K_RIGHT:
                preview_ship.changeDirection(preview_ship.direction + 90)
            elif e.key == pygame.K_h and not server: # pls fix later
                print("STARTING SERVER...")
                server = Server()
                server_thread = threading.Thread(target=server.start)
                server_thread.start()
                if IP == '':
                    IP = server.ADDR[0]
                client.connect(IP, 5050)
                listener_thread = threading.Thread(target=listen_to_server, args=(client, ))
                listener_thread.start()
                server_info_text = notif_font.render(f'{server.ADDR[0]}:{server.PORT}', True, [255, 255, 255], [128, 128, 128])
            elif e.key == pygame.K_k and not client.connected_addr: # pls fix later
                print("CONNECTING...")
                client.connect(IP, 5050)
                listener_thread = threading.Thread(target=listen_to_server, args=(client, ))
                listener_thread.start()
                print("CONNECTED")
            elif e.key == pygame.K_UP:
                volume += 0.1
                reset_sound = True
            elif e.key == pygame.K_DOWN:
                volume -= 0.1
                reset_sound = True

    # restart
    if restart_timer > 0:
        restart_timer -= 1
    elif restart_timer == 0:
        restart_timer -= 1
        player_turn = False
        result = None
        is_ready = {
            "client": False,
            "player": False
        }
        stage = 1
        missiles = []
        shots = []
        ships = []
        banned_positions = set()
        l = ship_units[len(ships)]
        preview_ship = Ship(sprites[str(l)], [-100, -100], l, 0)

    if reset_sound:
        reset_sound = False
        for k in sounds:
            sounds[k].set_volume(volume - 0.01)
        pygame.mixer.music.stop()
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)

    # SERVER COMMS ---------------------------- #

    # send to server
    if msgs_to_send:
        m = ';'.join(msgs_to_send)
        client.send(m)
        msgs_to_send = []

    # recv from server
    if recv_msg:
        notif_timer = 30
        notif_text = notif_font.render(recv_msg, True, [255, 255, 255], [0, 0, 0])
        recv_msgs = recv_msg.split(';')
        print(f'RECV: {recv_msgs}')
        for m in recv_msgs:
            m = m.split(' ')
            if m[0] == "ATK":
                sounds[f'alarm_{random.randint(1, 4)}'].play()
                player_turn = True
                pos = [int(m[1]), int(m[2])]
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
                            restart_timer = 120
                            player_turn = False
                    break
                msgs_to_send.append(f"ATK_RESP {1 if shots[-1][1] == True else 0}")

            elif m[0] == "ATK_RESP":
                sounds[f'shoot_{random.randint(1, 4)}'].play()
                if int(m[1]) == 1:
                    shots[-1][1] = True

            elif m[0] == "ENEMY_WIN":
                result = 'WIN'
                restart_timer = 120
                player_turn = False

            elif m[0] == "READY":
                is_ready['player'] = True
                player_turn = True
                if is_ready['client']:
                    stage = 2
                print(is_ready)

        recv_msg = None


    # DRAW ------------------------------------ #

    display.fill(BG_COLOR)

    # boards
    for b in [[PLL_COLOR, plb_topleft], [ENL_COLOR, enb_topleft]]:
        for l in range(1, bd_size):
            pygame.draw.line( # vertical
                display, b[0], 
                translate(b[1], [l * bd_scale, 0]),
                translate(b[1], [l * bd_scale, bd_sisc])
            )
            pygame.draw.line( # horizontal
                display, b[0], 
                translate(b[1], [0, l * bd_scale]),
                translate(b[1], [bd_sisc, l * bd_scale])
            )

    # ships
    for s in ships:
        s.draw(display, plb_topleft, bd_scale)
    if stage == 1 and is_ship_on_board(preview_ship):
        preview_ship.draw(display, plb_topleft, bd_scale)

    # lines
    for i, m in enumerate(missiles):
        x = 2 * (m[3] // 2)  # "lag" animation 
        pygame.draw.rect(display, MISSILE_COLOR, [x, m[0] *x**2 + m[1] * x + m[2], 5, 5], 2)
        missiles[i][3] += m[5]
        if missiles[i][3] > m[4]:
            del missiles[i]

    # shots
    for s in shots:
        shot_color = MISSILE_COLOR
        if s[1]:
            shot_color = [255, 0, 0]
        pygame.draw.circle(display, shot_color, s[0], bd_scale * 0.1)

    # result
    if result == 'WIN':
        display.blit(win_text, [(RES[0] - win_text.get_width())//2, (RES[1] - win_text.get_height())//2])
    elif result == 'LOSE':
        display.blit(lose_text, [(RES[0] - lose_text.get_width())//2, (RES[1] - lose_text.get_height())//2])

    # server notif
    if notif_timer > 0:
        notif_timer -= 1
        display.blit(notif_text, [(RES[0] - notif_text.get_width()) // 2, 0])
    if server_info_text:
        display.blit(server_info_text, [0, 0])

    pygame.display.update()

client.disconnect()
if server:
    server.stop()
pygame.quit()
