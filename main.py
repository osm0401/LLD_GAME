# main.py
import os
import pygame
from npc import *
from pygame.math import Vector2 as V2

from settings import *
from map_system import (
    load_overrides, save_overrides, draw_background,
    get_cell_from_world, clamp_to_world, TILE_OVERRIDE, invalidate_cache
)
from npc import NPC, DialogManager
from player import Player   # ★ 여기 추가

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Sky Archipelago")
    clock = pygame.time.Clock()

    load_overrides()

    # 플레이어 월드 좌표
    player_world = V2(WORLD_W / 2, WORLD_H / 2)
    move_target = None
    player_facing = V2(1, 0)

    # 스프라이트 플레이어 생성 (48x48 기준)
    player = Player(player_world, "assets/sprites/player_sheet.png")

    font = pygame.font.SysFont(FONT_NAME, 18)
    big_font = pygame.font.SysFont(FONT_NAME, 22)

    editor_mode = False
    editing_cell = None
    input_text = ""

    npcs = [
        NPC("연맹 파수꾼", V2(WORLD_W / 2 + 100, WORLD_H / 2),
            dialog_nodes=SAMPLE_NODES, start_node_id="start"),
    ]
    dialog = DialogManager()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if dialog.active:
                        dialog.close()
                    elif editor_mode and editing_cell is not None:
                        editing_cell = None;
                        input_text = ""
                    else:
                        running = False

                elif event.key == pygame.K_e:
                    editor_mode = not editor_mode
                    dialog.close()
                    editing_cell = None;
                    input_text = ""

                elif event.key == pygame.K_s and editor_mode:
                    save_overrides()

                elif event.key == pygame.K_l and editor_mode:
                    load_overrides()

                elif event.key == pygame.K_SPACE and not editor_mode:
                    if dialog.active:
                        dialog.progress()
                    else:
                        # 가까운 NPC 열기
                        nearest, best = None, 1e9
                        for n in npcs:
                            d = n.distance_to(player_world)
                            if d < best and d <= INTERACT_DISTANCE:
                                best, nearest = d, n
                        if nearest:
                            dialog.open(nearest)

                # 🔽 숫자키(1~9)로 선택
                elif dialog.active and (pygame.K_1 <= event.key <= pygame.K_9):
                    idx = event.key - pygame.K_1
                    dialog.choose(idx)

                # 에디터 입력 (편집 중일 때만)
                elif editor_mode and editing_cell is not None:
                    if event.key == pygame.K_RETURN:
                        if input_text.strip() == "":
                            TILE_OVERRIDE.pop(editing_cell, None)
                        else:
                            TILE_OVERRIDE[editing_cell] = input_text.strip()
                            invalidate_cache(input_text.strip())
                        editing_cell = None;
                        input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        ch = event.unicode
                        if ch:
                            input_text += ch

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # ✅ 대화가 열려 있으면 좌클릭은 먼저 대화로 보낸다 (다른 처리로 내려가지 않게)
                if dialog.active and event.button == 1:
                    dialog.handle_mouse(event.pos)
                    continue

                # 우클릭 이동 (대화/에디터 아닐 때)
                if event.button == 3 and (not editor_mode) and (not dialog.active):
                    mouse_screen = V2(event.pos)
                    camera_offset = CENTER - player_world
                    move_target = clamp_to_world(mouse_screen - camera_offset)

                # 에디터: 좌클릭으로 셀 선택
                elif event.button == 1 and editor_mode and (not dialog.active):
                    camera_offset = CENTER - player_world
                    world_pos = V2(event.pos) - camera_offset
                    cell = get_cell_from_world(world_pos)
                    if cell is not None:
                        editing_cell = cell
                        r, c = cell
                        current_path = TILE_OVERRIDE.get(cell) or os.path.join(TILE_FOLDER, f"{r}-{c}.png")
                        input_text = current_path

        # 이동 업데이트
        player.moving = False
        if move_target is not None and (not editor_mode) and (not dialog.active):
            to_target = move_target - player_world
            dist = to_target.length()
            if dist < 2:
                move_target = None
            else:
                dir_vec = to_target.normalize()
                player_facing = dir_vec
                player_world += dir_vec * PLAYER_SPEED * dt
                player_world = clamp_to_world(player_world)

                player.set_direction_from_vec(dir_vec)
                player.moving = True

        # 플레이어 실제 월드 좌표 동기화
        player.world_pos = player_world

        # 애니메이션 진행
        player.update_anim(dt)

        # 카메라
        camera_offset = CENTER - player_world

        # ==== 렌더 ====
        draw_background(screen, camera_offset)

        # NPC
        for n in npcs:
            n.draw(screen, camera_offset, font, player_pos=player_world)

        # (기존) 흰 원 플레이어는 제거
        # pygame.draw.circle(screen, (220, 220, 235), CENTER, PLAYER_RADIUS)

        # 스프라이트 플레이어
        player.draw(screen, camera_offset)

        # UI
        ui_lines = [
            "우클릭: 이동 | 스페이스: NPC 대화 | E: 에디터 모드 | 좌클릭(에디터): 셀 선택",
            "에디터: Enter=적용, ESC=취소, S=저장, L=불러오기",
        ]
        for i, s in enumerate(ui_lines):
            img = font.render(s, True, (230, 230, 235))
            screen.blit(img, (12, 10 + i * 20))

        # 에디터 UI
        if editor_mode:
            banner = pygame.Surface((SCREEN_W, 28), pygame.SRCALPHA)
            banner.fill((30, 35, 45, 200))
            screen.blit(banner, (0, 0))
            label = big_font.render("[에디터 모드] 셀을 선택하고 경로 입력 후 Enter", True, (230, 230, 235))
            screen.blit(label, (12, 4))

            if editing_cell is not None:
                box_w, box_h = SCREEN_W - 24, 36
                box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                box.fill((18, 20, 24, 230))
                screen.blit(box, (12, 40))

                r, c = editing_cell
                prompt = f"({r},{c}) 이미지 경로 입력: "
                txt = big_font.render(prompt + input_text, True, (240, 240, 245))
                screen.blit(txt, (20, 46))

                sel_rect = pygame.Rect((c - 1) * TILE_SIZE, (r - 1) * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                sel_rect.topleft = V2(sel_rect.topleft) + camera_offset
                pygame.draw.rect(screen, (255, 210, 80), sel_rect, 3)

        # 대화
        dialog.draw(screen, big_font, font)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
