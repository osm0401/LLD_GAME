# main.py
import os
import pygame
from pygame.math import Vector2 as V2

from settings import (
    SCREEN_W, SCREEN_H, CENTER, FPS,
    PLAYER_SPEED, FONT_NAME,
    TILE_SIZE,
)
import map_system
import buck_city
import buck_bank
from player import Player
from npc import NPC, BankNPC, DialogManager, SAMPLE_NODES


# --------------------------------------------------
# 보조 함수들
# --------------------------------------------------
def find_nearest_npc(player_pos, npc_list, max_range=90.0):
    """플레이어 주변에서 가장 가까운 NPC 하나 찾기 (NPC / BankNPC 공통)."""
    best = None
    best_d2 = max_range * max_range
    for npc in npc_list:
        if not hasattr(npc, "world_pos"):
            continue
        d2 = (npc.world_pos - player_pos).length_squared()
        if d2 < best_d2:
            best = npc
            best_d2 = d2
    return best


def clamp_world(pos: V2) -> V2:
    """map_system.clamp_to_world 이 있으면 그걸 쓰고, 없으면 그대로."""
    if hasattr(map_system, "clamp_to_world"):
        return map_system.clamp_to_world(pos)
    return pos


def get_cell(world_pos: V2):
    """map_system.get_cell_from_world 있으면 그걸 쓰고, 없으면 None."""
    if hasattr(map_system, "get_cell_from_world"):
        return map_system.get_cell_from_world(world_pos)
    return None


# --------------------------------------------------
# 메인 함수
# --------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("하늘섬 - 도시 / 은행 / 에디터")
    clock = pygame.time.Clock()

    # --- 클립보드 (Ctrl+V) 초기화 ---
    SCRAP_AVAILABLE = False
    try:
        pygame.scrap.init()
        SCRAP_AVAILABLE = True
        print("[clipboard] pygame.scrap 사용 가능 (Ctrl+V 지원)")
    except Exception as e:
        print("[clipboard] pygame.scrap 사용 불가:", e)

    # --- 폰트 & 대화 시스템 ---
    font = pygame.font.SysFont(FONT_NAME, 18)
    big_font = pygame.font.SysFont(FONT_NAME, 22)
    dialog = DialogManager(SAMPLE_NODES, font, big_font)

    # --- 맵 & 플레이어 & NPC 초기화 ---
    spawn_data = buck_city.load_default()  # (pos, npc_list) 또는 pos 만 반환할 수 있음

    if isinstance(spawn_data, tuple) and len(spawn_data) >= 2:
        player_world, active_npcs = spawn_data[0], spawn_data[1]
    else:
        player_world = V2(spawn_data)
        active_npcs = []

    move_target = None  # 이동 목표 (월드 좌표)

    # Player 생성
    try:
        player = Player(player_world, "assets/sprites/player_sheet.png")
    except TypeError:
        player = Player(player_world)

    if hasattr(player, "world_pos"):
        player.world_pos = V2(player_world)

    # --- 에디터 / 텔레포트 상태 ---
    editor_mode = False
    teleport_mode = False
    editing_cell = None
    input_text = ""

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # --------------------------------------------------
        # 이벤트 처리
        # --------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ---------------- KEYDOWN ----------------
            elif event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()

                # ESC
                if event.key == pygame.K_ESCAPE:
                    # 에디터에서 셀 입력 중이면 취소
                    if editor_mode and editing_cell is not None:
                        print("[editor] 입력 취소:", editing_cell)
                        editing_cell = None
                        input_text = ""
                    # 대화 중이면 대화 닫기
                    elif dialog.active:
                        dialog.close()
                    else:
                        running = False

                # 에디터 셀 경로 입력 중일 때
                elif editor_mode and editing_cell is not None:
                    if event.key == pygame.K_RETURN:
                        path_str = input_text.strip()
                        if path_str == "":
                            # 오버라이드 제거
                            if hasattr(map_system, "TILE_OVERRIDE"):
                                map_system.TILE_OVERRIDE.pop(editing_cell, None)
                            print("[editor] 오버라이드 제거:", editing_cell)
                        else:
                            if hasattr(map_system, "TILE_OVERRIDE"):
                                map_system.TILE_OVERRIDE[editing_cell] = path_str
                            print("[editor] 오버라이드 설정:", editing_cell, "->", path_str)

                        # 캐시 무효화 / 저장
                        if hasattr(map_system, "invalidate_cache"):
                            try:
                                map_system.invalidate_cache(editing_cell)
                            except Exception:
                                pass
                        if hasattr(map_system, "save_overrides"):
                            map_system.save_overrides()

                        editing_cell = None
                        input_text = ""

                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]

                    elif event.key == pygame.K_v and (mods & pygame.KMOD_CTRL):
                        # Ctrl+V 붙여넣기
                        if SCRAP_AVAILABLE and hasattr(pygame, "scrap"):
                            try:
                                data = pygame.scrap.get(pygame.SCRAP_TEXT)
                                if data:
                                    pasted = data.decode("utf-8", errors="ignore")
                                    pasted = pasted.replace("\x00", "")
                                    input_text += pasted
                                    print("[editor] Ctrl+V:", repr(pasted))
                            except Exception as e:
                                print("[editor] Ctrl+V 실패:", e)
                        else:
                            print("[editor] Ctrl+V: 클립보드 사용 불가")
                    else:
                        ch = event.unicode
                        if ch:
                            input_text += ch

                # 에디터 모드 토글
                elif event.key == pygame.K_e:
                    editor_mode = not editor_mode
                    teleport_mode = False
                    editing_cell = None
                    input_text = ""
                    print("[editor] mode:", editor_mode)

                # 에디터: 수동 저장 / 불러오기
                elif editor_mode and editing_cell is None:
                    if event.key == pygame.K_s and hasattr(map_system, "save_overrides"):
                        print("[editor] 수동 저장")
                        map_system.save_overrides()
                    elif event.key == pygame.K_l and hasattr(map_system, "load_overrides"):
                        print("[editor] 수동 불러오기")
                        map_system.load_overrides()

                # 텔레포트 모드 K
                elif event.key == pygame.K_k and (not editor_mode) and (not dialog.active):
                    teleport_mode = not teleport_mode
                    print("[teleport] mode:", teleport_mode)

                # 스페이스: 대화 or 맵 전환
                elif event.key == pygame.K_SPACE and (not editor_mode):
                    # 대화 중이면: 진행(선택지 강조/다음)
                    if dialog.active:
                        dialog.progress()
                    else:
                        target = find_nearest_npc(player_world, active_npcs, max_range=90)
                        if target is None:
                            continue

                        # 사람 NPC → 대화
                        if isinstance(target, NPC):
                            dialog.open(target)

                        # 은행 NPC → 맵 전환
                        elif isinstance(target, BankNPC):
                            action = target.on_interact()
                            if action == "enter_bank":
                                data = buck_bank.load_from_city()
                                if isinstance(data, tuple) and len(data) >= 2:
                                    player_world, active_npcs = data[0], data[1]
                                else:
                                    player_world = V2(data)
                                if hasattr(player, "world_pos"):
                                    player.world_pos = V2(player_world)
                                move_target = None
                                teleport_mode = False
                                print("[map] 도시 → 은행(내부)")
                            elif action == "exit_bank":
                                data = buck_city.load_from_bank()
                                if isinstance(data, tuple) and len(data) >= 2:
                                    player_world, active_npcs = data[0], data[1]
                                else:
                                    player_world = V2(data)
                                if hasattr(player, "world_pos"):
                                    player.world_pos = V2(player_world)
                                move_target = None
                                teleport_mode = False
                                print("[map] 은행(내부) → 도시")

            # ---------------- MOUSEBUTTONDOWN ----------------
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 대화창이 열려 있으면, 좌클릭은 대화 선택에 사용
                if dialog.active and event.button == 1:
                    dialog.handle_mouse(event.pos)
                    continue

                # 텔레포트 모드: 좌클릭 → 즉시 이동
                if teleport_mode and event.button == 1:
                    camera_offset = CENTER - player_world
                    world_pos = V2(event.pos) - camera_offset
                    world_pos = clamp_world(world_pos)
                    cell = get_cell(world_pos)
                    if cell is not None:
                        r, c = cell
                    else:
                        r, c = -1, -1
                    local_x = world_pos.x % TILE_SIZE
                    local_y = world_pos.y % TILE_SIZE

                    player_world = world_pos
                    if hasattr(player, "world_pos"):
                        player.world_pos = V2(player_world)
                    move_target = None
                    teleport_mode = False

                    print(
                        f"[teleport] world=({world_pos.x:.1f}, {world_pos.y:.1f}), "
                        f"cell=({r},{c}), local=({local_x:.1f}, {local_y:.1f})"
                    )
                    continue

                # 우클릭: 이동 (에디터/텔레포트 아니고, 대화 중 아님)
                if event.button == 3 and (not editor_mode) and (not dialog.active):
                    mouse_screen = V2(event.pos)
                    camera_offset = CENTER - player_world
                    world_target = mouse_screen - camera_offset
                    world_target = clamp_world(world_target)
                    move_target = world_target
                    # 플레이어 이동 시작
                    if hasattr(player, "moving"):
                        player.moving = True

                # 에디터 모드: 좌클릭으로 셀 선택
                elif event.button == 1 and editor_mode:
                    camera_offset = CENTER - player_world
                    world_pos = V2(event.pos) - camera_offset
                    cell = get_cell(world_pos)
                    if cell is not None:
                        editing_cell = cell
                        r, c = cell
                        default_path = os.path.join("assets", "tiles", f"{r}-{c}.png")
                        if hasattr(map_system, "TILE_OVERRIDE"):
                            current_path = map_system.TILE_OVERRIDE.get(cell, default_path)
                        else:
                            current_path = default_path
                        input_text = current_path
                        print("[editor] 셀 선택:", cell, "=", input_text)

        # --------------------------------------------------
        # 플레이어 이동 / 애니메이션
        # --------------------------------------------------
        if move_target is not None and (not editor_mode) and (not teleport_mode):
            to_target = move_target - player_world
            dist = to_target.length()
            if dist <= 2.0:
                # 도착
                move_target = None
                if hasattr(player, "moving"):
                    player.moving = False
            else:
                dir_vec = to_target.normalize()
                player_world += dir_vec * PLAYER_SPEED * dt
                player_world = clamp_world(player_world)
                if hasattr(player, "world_pos"):
                    player.world_pos = V2(player_world)
                if hasattr(player, "set_direction_from_vec"):
                    player.set_direction_from_vec(dir_vec)
                if hasattr(player, "moving"):
                    player.moving = True
        else:
            if hasattr(player, "moving"):
                player.moving = False

        if hasattr(player, "update_anim"):
            player.update_anim(dt)

        camera_offset = CENTER - player_world

        # --------------------------------------------------
        # 그리기
        # --------------------------------------------------
        map_system.draw_background(screen, camera_offset)

        # 이동 목표 표시 (move_target이 있을 때만)
        if move_target is not None and (not editor_mode):
            tpos = move_target + camera_offset
            pygame.draw.circle(screen, (200, 120, 40), tpos, 8, 2)
            pygame.draw.circle(screen, (200, 160, 60), tpos, 14, 1)

        # NPC들 (에디터 여부 상관 없이 항상 표시)
        for npc in active_npcs:
            npc.draw(screen, camera_offset, font, player_world)

        # 플레이어
        if hasattr(player, "draw"):
            player.draw(screen, camera_offset)
        else:
            pygame.draw.circle(screen, (220, 220, 235), CENTER, 14)
            pygame.draw.circle(screen, (90, 100, 120), CENTER, 2)

        # UI 안내
        ui_lines = [
            "우클릭: 이동 | SPACE: NPC 상호작용 | E: 에디터 | K: 텔레포트 모드",
            "에디터: 좌클릭=셀 선택, Enter=적용+저장, S=저장, L=불러오기, ESC=취소",
        ]
        if editor_mode:
            ui_lines.append("[에디터 모드]")
        if teleport_mode:
            ui_lines.append("[텔레포트 모드] 좌클릭: 순간이동 (좌표는 콘솔 출력)")

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
            txt_surf = big_font.render(prompt + input_text, True, (240, 240, 245))
            screen.blit(txt_surf, (20, 46))

            sel_rect = pygame.Rect(
                (c - 1) * TILE_SIZE,
                (r - 1) * TILE_SIZE,
                TILE_SIZE, TILE_SIZE
            )
            sel_rect.topleft = V2(sel_rect.topleft) + camera_offset
            pygame.draw.rect(screen, (255, 210, 80), sel_rect, 3)

        # 대화창
        dialog.update(dt)
        dialog.draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
