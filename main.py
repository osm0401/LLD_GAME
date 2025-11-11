# main.py
import os
import pygame
from pygame.math import Vector2 as V2

from settings import (
    SCREEN_W, SCREEN_H, CENTER, FPS,
    PLAYER_SPEED, FONT_NAME,
    TILE_SIZE, WORLD_W, WORLD_H,
)

import map_system
import buck_city
import buck_bank
from player import Player  # 네 Player 클래스에 맞게 조정


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("하늘섬 - 맵 에디터 + 맵 전환")
    clock = pygame.time.Clock()

    # ---- 클립보드(Ctrl+V) ----
    SCRAP_AVAILABLE = False
    try:
        pygame.scrap.init()
        SCRAP_AVAILABLE = True
        print("[clipboard] pygame.scrap 사용 가능 (Ctrl+V 지원)")
    except Exception as e:
        print("[clipboard] pygame.scrap 사용 불가:", e)

    # ---- 맵 및 플레이어 초기화 ----
    # 도시 기본 맵 로딩 + 시작 위치 받기
    player_world = buck_city.load_default()  # 내부에서 CURRENT_MAP="city" + 오버라이드 로드
    move_target = None

    # ---- 플레이어 생성 ----
    try:
        # 만약 Player(world_pos, sprite_path) 형태라면 이게 동작
        player = Player(player_world, "assets/sprites/player_sheet.png")
    except TypeError:
        # 아니면 단순히 Player(world_pos)만 받는 경우
        player = Player(player_world)

    if hasattr(player, "world_pos"):
        player.world_pos = player_world

    font = pygame.font.SysFont(FONT_NAME, 18)
    big_font = pygame.font.SysFont(FONT_NAME, 22)

    editor_mode = False
    editing_cell: tuple[int, int] | None = None
    input_text: str = ""

    teleport_mode = False  # K로 토글

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ================= KEYDOWN =================
            elif event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()

                # 1) ESC
                if event.key == pygame.K_ESCAPE:
                    if editor_mode and editing_cell is not None:
                        # 에디터 입력 취소
                        print("[editor] 입력 취소:", editing_cell)
                        editing_cell = None
                        input_text = ""
                    else:
                        running = False

                # 2) 에디터에서 셀 입력 중 (Enter / Backspace / Ctrl+V / 문자)
                elif editor_mode and editing_cell is not None:
                    # Enter: 적용 + 바로 파일에 저장
                    if event.key == pygame.K_RETURN:
                        path_str = input_text.strip()

                        if path_str == "":
                            # 비웠으면 오버라이드 제거 -> 기본 규칙으로 복귀
                            map_system.TILE_OVERRIDE.pop(editing_cell, None)
                            print("[editor] 오버라이드 제거:", editing_cell)
                        else:
                            # 전체 경로 그대로 저장 (예: "assets/tiles/1-1.png")
                            map_system.TILE_OVERRIDE[editing_cell] = path_str
                            print("[editor] 오버라이드 설정:", editing_cell, "->", path_str)

                        map_system.invalidate_cache(None)
                        print("[editor] 현재 TILE_OVERRIDE =", map_system.TILE_OVERRIDE)
                        # Enter 칠 때마다 자동 저장 (현재 맵의 json에 저장)
                        map_system.save_overrides()

                        editing_cell = None
                        input_text = ""

                    # Backspace
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]

                    # Ctrl+V
                    elif event.key == pygame.K_v and (mods & pygame.KMOD_CTRL):
                        if SCRAP_AVAILABLE and hasattr(pygame, "scrap"):
                            try:
                                data = pygame.scrap.get(pygame.SCRAP_TEXT)
                                if data:
                                    pasted = data.decode("utf-8", errors="ignore")
                                    pasted = pasted.replace("\x00", "")
                                    input_text += pasted
                                    print("[editor] Ctrl+V 붙여넣기:", repr(pasted))
                            except Exception as e:
                                print("[editor] Ctrl+V 실패:", e)
                        else:
                            print("[editor] Ctrl+V: 클립보드 사용 불가")

                    # 일반 문자 입력
                    else:
                        ch = event.unicode
                        if ch:
                            input_text += ch

                # 3) 에디터 모드 토글
                elif event.key == pygame.K_e:
                    editor_mode = not editor_mode
                    editing_cell = None
                    input_text = ""
                    teleport_mode = False
                    print("[editor] mode:", editor_mode)

                # 4) 수동 저장 (Enter에서도 이미 저장됨)
                elif event.key == pygame.K_s and editor_mode and editing_cell is None:
                    print("[editor] 수동 저장:", map_system.TILE_OVERRIDE)
                    map_system.save_overrides()

                # 5) 불러오기 (현재 맵의 오버라이드 json 로드)
                elif event.key == pygame.K_l and editor_mode and editing_cell is None:
                    map_system.load_overrides()

                # 6) 텔레포트 모드 토글
                elif event.key == pygame.K_k and (not editor_mode):
                    teleport_mode = not teleport_mode
                    print("[teleport] mode:", teleport_mode)

                # 7) F: 문에서 다른 맵으로 이동 (에디터 아닐 때만)
                elif event.key == pygame.K_f and (not editor_mode):
                    cell = map_system.get_cell_from_world(player_world)
                    if cell is None:
                        continue

                    # 7-1) 도시에서 은행으로 들어가기
                    if map_system.CURRENT_MAP == "city" and cell == buck_city.BANK_DOOR_CELL:
                        player_world = buck_bank.load_from_city()
                        if hasattr(player, "world_pos"):
                            player.world_pos = player_world
                        move_target = None
                        teleport_mode = False
                        print("[map] 도시 → 은행 이동")

                    # 7-2) 은행에서 도시로 나가기
                    elif map_system.CURRENT_MAP == "bank" and cell == buck_bank.EXIT_DOOR_CELL:
                        player_world = buck_city.load_from_bank()
                        if hasattr(player, "world_pos"):
                            player.world_pos = player_world
                        move_target = None
                        teleport_mode = False
                        print("[map] 은행 → 도시 이동")

            # ================= MOUSEBUTTONDOWN =================
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 텔레포트 모드: 좌클릭 → 그 위치로 순간이동
                if teleport_mode and event.button == 1:
                    camera_offset = CENTER - player_world
                    world_pos = V2(event.pos) - camera_offset
                    world_pos = map_system.clamp_to_world(world_pos)

                    cell = map_system.get_cell_from_world(world_pos)
                    if cell is not None:
                        r, c = cell
                    else:
                        r, c = -1, -1

                    local_x = world_pos.x % TILE_SIZE
                    local_y = world_pos.y % TILE_SIZE

                    player_world = world_pos
                    if hasattr(player, "world_pos"):
                        player.world_pos = player_world

                    move_target = None
                    teleport_mode = False

                    print(
                        f"[teleport] world=({world_pos.x:.1f}, {world_pos.y:.1f}), "
                        f"cell=({r},{c}), local=({local_x:.1f}, {local_y:.1f})"
                    )
                    continue

                # 우클릭 이동 (에디터 아닐 때)
                if event.button == 3 and (not editor_mode):
                    mouse_screen = V2(event.pos)
                    camera_offset = CENTER - player_world
                    move_target = map_system.clamp_to_world(mouse_screen - camera_offset)

                # 에디터: 좌클릭 셀 선택
                elif event.button == 1 and editor_mode:
                    camera_offset = CENTER - player_world
                    world_pos = V2(event.pos) - camera_offset
                    cell = map_system.get_cell_from_world(world_pos)
                    if cell is not None:
                        editing_cell = cell
                        r, c = cell
                        # 기본값: 오버라이드 있으면 그 경로, 없으면 기본 자리 경로
                        default_path = os.path.join("assets", "tiles", f"{r}-{c}.png")
                        current_path = map_system.TILE_OVERRIDE.get(cell, default_path)
                        input_text = current_path
                        print("[editor] 셀 선택:", cell, "현재값:", input_text)

        # ================= 플레이어 이동 =================
        if move_target is not None and (not editor_mode):
            to_target = move_target - player_world
            dist = to_target.length()
            if dist < 2:
                move_target = None
            else:
                dir_vec = to_target.normalize()
                player_world += dir_vec * PLAYER_SPEED * dt
                player_world = map_system.clamp_to_world(player_world)

                if hasattr(player, "world_pos"):
                    player.world_pos = player_world
                if hasattr(player, "set_direction_from_vec"):
                    player.set_direction_from_vec(dir_vec)
                if hasattr(player, "moving"):
                    player.moving = True

        if hasattr(player, "update_anim"):
            player.update_anim(dt)

        camera_offset = CENTER - player_world

        # ================= 그리기 =================
        map_system.draw_background(screen, camera_offset)

        # 이동 목표 표시
        if move_target is not None and (not editor_mode):
            tpos = move_target + camera_offset
            pygame.draw.circle(screen, (200, 120, 40), tpos, 8, 2)
            pygame.draw.circle(screen, (200, 160, 60), tpos, 14, 1)

        # 플레이어
        if hasattr(player, "draw"):
            player.draw(screen, camera_offset)
        else:
            # 혹시 draw가 없다면, 임시로 원으로 표시
            center_screen = CENTER
            pygame.draw.circle(screen, (220, 220, 235), center_screen, 14)
            pygame.draw.circle(screen, (90, 100, 120), center_screen, 2)

        # UI 텍스트
        ui_lines = [
            f"현재 맵: {map_system.CURRENT_MAP}",
            "우클릭: 이동 | E: 에디터 모드 | K: 텔레포트 모드 | F: 문에서 다른 맵 이동",
            "에디터: 좌클릭=셀 선택, Enter=적용+저장, S=수동 저장, L=불러오기, ESC=취소",
            "입력값은 전체 경로 예) assets/tiles/1-1.png",
        ]
        if teleport_mode:
            ui_lines.append("[텔레포트 모드] 좌클릭: 순간이동 (좌표는 콘솔에 출력)")

        y = 10
        for s in ui_lines:
            img = font.render(s, True, (230, 230, 235))
            screen.blit(img, (12, y))
            y += 20

        # 에디터 입력창
        if editor_mode and editing_cell is not None:
            box_w, box_h = SCREEN_W - 24, 36
            box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            box.fill((18, 20, 24, 230))
            screen.blit(box, (12, 40))

            r, c = editing_cell
            prompt = f"({r},{c}) 경로 입력: "
            txt = big_font.render(prompt + input_text, True, (240, 240, 245))
            screen.blit(txt, (20, 46))

            sel_rect = pygame.Rect(
                (c - 1) * TILE_SIZE,
                (r - 1) * TILE_SIZE,
                TILE_SIZE, TILE_SIZE
            )
            sel_rect.topleft = V2(sel_rect.topleft) + camera_offset
            pygame.draw.rect(screen, (255, 210, 80), sel_rect, 3)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
