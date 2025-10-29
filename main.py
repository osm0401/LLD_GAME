import pygame
from pygame.math import Vector2 as V2
from settings import *
from map_system import *
from npc import NPC, DialogManager

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("LoL-style Camera + NPC")
    clock = pygame.time.Clock()

    load_overrides()

    player_world = V2(WORLD_W/2, WORLD_H/2)
    move_target, player_facing = None, V2(1,0)
    font = pygame.font.SysFont(FONT_NAME, 18)
    big_font = pygame.font.SysFont(FONT_NAME, 22)
    editor_mode, editing_cell, input_text = False, None, ""

    npcs = [
        NPC("연맹 파수꾼", V2(WORLD_W/2+100, WORLD_H/2),
            ["안녕, 여행자!", "북동쪽으로 가면 비석이 있어."]),
        NPC("상인 로웰", V2(WORLD_W/2-220, WORLD_H/2+180),
            ["필요한 게 있으면 언제든 찾아오게."])
    ]
    dialog = DialogManager()
    running = True

    while running:
        dt = clock.tick(FPS)/1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running=False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if dialog.active: dialog.close()
                    else: running=False
                elif e.key == pygame.K_SPACE and not editor_mode:
                    if dialog.active: dialog.progress()
                    else:
                        front = [n for n in npcs if n.is_in_front_of_player(player_world, player_facing)]
                        if front: dialog.open(front[0])

        # 이동
        if move_target and not dialog.active:
            diff = move_target - player_world
            if diff.length()<2: move_target=None
            else:
                dirv = diff.normalize()
                player_facing = dirv
                player_world += dirv*PLAYER_SPEED*dt
                player_world = clamp_to_world(player_world)

        camera_offset = CENTER - player_world
        draw_background(screen, camera_offset)
        for n in npcs: n.draw(screen, camera_offset, font)
        pygame.draw.circle(screen, (220,220,235), CENTER, PLAYER_RADIUS)
        pygame.draw.circle(screen, (90,100,120), CENTER, PLAYER_RADIUS, 2)
        if player_facing.length_squared()>1e-6:
            tip = CENTER + player_facing.normalize()*(PLAYER_RADIUS+10)
            pygame.draw.circle(screen, (255,210,80), tip, 3)
        dialog.draw(screen, big_font, font)
        pygame.display.flip()
    pygame.quit()
main()