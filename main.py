# main.py
import os, pygame
from pygame.math import Vector2 as V2
from settings import (
    SCREEN_W, SCREEN_H, CENTER, FPS,
    PLAYER_SPEED, FONT_NAME,
    TILE_SIZE, EDITOR_INPUT_HEIGHT, EDITOR_INPUT_PADDING,
    EDITOR_SELECT_INSET, EDITOR_SELECT_BORDER,
)
import map_system
import buck_city, buck_bank
from player import Player
from npc import NPC, BankNPC, DialogManager, SAMPLE_NODES

def find_nearest_npc(player_pos, npc_list, max_range=90.0):
    best, best_d2 = None, max_range * max_range
    for npc in npc_list:
        if not hasattr(npc, "world_pos"): continue
        d2 = (npc.world_pos - player_pos).length_squared()
        if d2 < best_d2: best, best_d2 = npc, d2
    return best

def clamp_world(pos: V2) -> V2:
    return map_system.clamp_to_world(pos) if hasattr(map_system, "clamp_to_world") else pos

def get_cell(world_pos: V2):
    return map_system.get_cell_from_world(world_pos) if hasattr(map_system, "get_cell_from_world") else None

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("하늘섬")
    clock = pygame.time.Clock()

    # Clipboard(Ctrl+V)
    try:
        pygame.scrap.init()
        print("[clipboard] pygame.scrap 사용 가능 (Ctrl+V 지원)")
        SCRAP = True
    except Exception as e:
        print("[clipboard] pygame.scrap 사용 불가:", e)
        SCRAP = False

    font = pygame.font.SysFont(FONT_NAME, 18)
    big_font = pygame.font.SysFont(FONT_NAME, 22)
    dialog = DialogManager(SAMPLE_NODES, font, big_font)

    # 초기 맵/플레이어/NPC
    spawn_data = buck_city.load_default()
    if isinstance(spawn_data, tuple) and len(spawn_data) >= 2:
        player_world, active_npcs = V2(spawn_data[0]), list(spawn_data[1])
    else:
        player_world, active_npcs = V2(spawn_data), []

    move_target: V2 | None = None

    try:
        player = Player(player_world, "assets/sprites/player_sheet.png")
    except TypeError:
        player = Player(player_world)
    if hasattr(player, "world_pos"): player.world_pos = V2(player_world)

    editor_mode = False
    teleport_mode = False
    editing_cell = None
    input_text = ""

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()

                if event.key == pygame.K_ESCAPE:
                    if editor_mode and editing_cell is not None:
                        editing_cell, input_text = None, ""
                    elif dialog.active:
                        dialog.close()
                    else:
                        running = False

                elif editor_mode and editing_cell is not None:
                    if event.key == pygame.K_RETURN:
                        path_str = input_text.strip()
                        if path_str == "":
                            map_system.TILE_OVERRIDE.pop(editing_cell, None)
                            print("[editor] 제거:", editing_cell)
                        else:
                            map_system.TILE_OVERRIDE[editing_cell] = path_str
                            print("[editor] 설정:", editing_cell, "->", path_str)
                        map_system.invalidate_cache(editing_cell)
                        map_system.save_overrides()
                        editing_cell, input_text = None, ""
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.key == pygame.K_v and (mods & pygame.KMOD_CTRL):
                        if SCRAP:
                            try:
                                data = pygame.scrap.get(pygame.SCRAP_TEXT)
                                if data:
                                    pasted = data.decode("utf-8", errors="ignore").replace("\x00", "")
                                    input_text += pasted
                                    print("[editor] Ctrl+V:", repr(pasted))
                            except Exception as e:
                                print("[editor] Ctrl+V 실패:", e)
                        else:
                            print("[editor] Ctrl+V 불가")
                    else:
                        if event.unicode: input_text += event.unicode

                elif event.key == pygame.K_e:
                    editor_mode = not editor_mode
                    teleport_mode = False
                    editing_cell, input_text = None, ""
                    print("[editor] mode:", editor_mode)

                elif editor_mode and editing_cell is None:
                    if event.key == pygame.K_s: map_system.save_overrides()
                    elif event.key == pygame.K_l: map_system.load_overrides()

                elif event.key == pygame.K_k and (not editor_mode) and (not dialog.active):
                    teleport_mode = not teleport_mode
                    print("[teleport] mode:", teleport_mode)

                elif event.key == pygame.K_SPACE and (not editor_mode):
                    if dialog.active:
                        dialog.progress()
                    else:
                        target = find_nearest_npc(player_world, active_npcs, 90)
                        if not target: continue
                        if isinstance(target, NPC):
                            dialog.open(target)
                        elif isinstance(target, BankNPC):
                            action = target.on_interact()
                            if action == "enter_bank":
                                data = buck_bank.load_from_city()
                            else:
                                data = buck_city.load_from_bank()
                            if isinstance(data, tuple) and len(data) >= 2:
                                player_world, active_npcs = V2(data[0]), list(data[1])
                            else:
                                player_world = V2(data)
                            if hasattr(player, "world_pos"): player.world_pos = V2(player_world)
                            move_target = None
                            teleport_mode = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if dialog.active and event.button == 1:
                    dialog.handle_mouse(event.pos)
                    continue

                if teleport_mode and event.button == 1:
                    camera_offset = CENTER - player_world
                    world_pos = V2(event.pos) - camera_offset
                    world_pos = clamp_world(world_pos)
                    cell = get_cell(world_pos) or (-1, -1)
                    local_x, local_y = world_pos.x % TILE_SIZE, world_pos.y % TILE_SIZE
                    player_world = world_pos
                    if hasattr(player, "world_pos"): player.world_pos = V2(player_world)
                    move_target = None; teleport_mode = False
                    print(f"[teleport] world=({world_pos.x:.1f},{world_pos.y:.1f}) cell={cell} local=({local_x:.1f},{local_y:.1f})")
                    continue

                if event.button == 3 and (not editor_mode) and (not dialog.active):
                    camera_offset = CENTER - player_world
                    world_target = V2(event.pos) - camera_offset
                    move_target = clamp_world(world_target)
                    if hasattr(player, "moving"): player.moving = True

                elif event.button == 1 and editor_mode:
                    camera_offset = CENTER - player_world
                    world_pos = V2(event.pos) - camera_offset
                    cell = get_cell(world_pos)
                    if cell is not None:
                        editing_cell = cell
                        r, c = cell
                        default_path = os.path.join("assets", "tiles", f"{r}-{c}.png")
                        current_path = map_system.TILE_OVERRIDE.get(cell, default_path)
                        input_text = current_path
                        print("[editor] 셀 선택:", cell, "=", input_text)

        # ---- 이동/애니메이션 ----
        if move_target is not None and (not editor_mode) and (not teleport_mode):
            to_target = move_target - player_world
            dist = to_target.length()
            if dist <= 2.0:
                move_target = None
                if hasattr(player, "moving"): player.moving = False
            else:
                dir_vec = to_target.normalize()
                player_world += dir_vec * PLAYER_SPEED * dt
                player_world = clamp_world(player_world)
                if hasattr(player, "world_pos"): player.world_pos = V2(player_world)
                if hasattr(player, "set_direction_from_vec"): player.set_direction_from_vec(dir_vec)
                if hasattr(player, "moving"): player.moving = True
        else:
            if hasattr(player, "moving"): player.moving = False

        if hasattr(player, "update_anim"): player.update_anim(dt)

        camera_offset = CENTER - player_world

        # ---- 그리기 ----
        map_system.draw_background(screen, camera_offset)

        if move_target is not None and (not editor_mode):
            tpos = move_target + camera_offset
            pygame.draw.circle(screen, (200,120,40), tpos, 8, 2)
            pygame.draw.circle(screen, (200,160,60), tpos, 14, 1)

        for npc in active_npcs:
            npc.draw(screen, camera_offset, font, player_world)

        if hasattr(player, "draw"):
            player.draw(screen, camera_offset)

        # ---- UI 패널 (겹침 없음) ----
        meta = map_system.get_override_meta()
        ui_lines = [
            f"맵: {meta['map']}  |  파일: {meta['file']}  |  오버라이드: {meta['count']} 셀",
            "우클릭: 이동  |  SPACE: 상호작용  |  E: 에디터  |  K: 텔레포트",
        ]
        if editor_mode:
            ui_lines.append("에디터: 좌클릭=셀 선택, Enter=적용+저장, S=저장, L=불러오기, ESC=취소")
        if teleport_mode:
            ui_lines.append("[텔레포트] 좌클릭: 순간이동 (좌표는 콘솔 출력)")

        pad_x, pad_y = 10, 8
        line_h = font.get_linesize()
        box_w = max(font.size(s)[0] for s in ui_lines) + pad_x * 2
        box_h = line_h * len(ui_lines) + pad_y * 2
        panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA); panel.fill((12,14,18,180))
        screen.blit(panel, (8, 8))
        y = 8 + pad_y
        for s in ui_lines:
            screen.blit(font.render(s, True, (230,230,235)), (8 + pad_x, y))
            y += line_h

        # ---- 에디터 입력/선택 ----
        if editor_mode and editing_cell is not None:
            box_w = SCREEN_W - 24
            box_h = EDITOR_INPUT_HEIGHT
            panel2 = pygame.Surface((box_w, box_h), pygame.SRCALPHA); panel2.fill((18,20,24,230))
            screen.blit(panel2, (12, 40))
            r, c = editing_cell
            prompt = f"({r},{c}) 경로 입력: "
            txt = font.render(prompt + input_text, True, (240,240,245))
            screen.blit(txt, (12 + EDITOR_INPUT_PADDING, 40 + (box_h - txt.get_height()) // 2))
            # 선택 타일 테두리 (안쪽으로)
            sel_x = (c - 1) * TILE_SIZE + EDITOR_SELECT_INSET
            sel_y = (r - 1) * TILE_SIZE + EDITOR_SELECT_INSET
            sel_w = TILE_SIZE - EDITOR_SELECT_INSET * 2
            sel_h = TILE_SIZE - EDITOR_SELECT_INSET * 2
            sel_rect = pygame.Rect(sel_x, sel_y, sel_w, sel_h)
            sel_rect.topleft = V2(sel_rect.topleft) + camera_offset
            pygame.draw.rect(screen, (255,210,80), sel_rect, EDITOR_SELECT_BORDER)

        dialog.update(dt); dialog.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
