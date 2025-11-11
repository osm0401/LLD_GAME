import os
import json
import pygame
from pygame.math import Vector2 as V2
import math

"""
LoL-style 카메라 고정 + 맵 끝 제한 + 셀별 이미지 맵 + 인게임 에디터 (Pygame)
플레이어는 화면 중앙에 고정되고, 우클릭으로 이동합니다.
맵은 정사각형 타일 (행, 열) 기준으로 구성되며,
각 셀 이미지는 기본 규칙(assets/tiles/{r}-{c}.png) + 사용자 지정 경로를 사용할 수 있습니다.

인게임 에디터 기능:
 - E 키: 에디터 모드 토글
 - 에디터 모드에서 좌클릭: 셀 선택 후 경로 입력
 - Enter: 입력 적용
 - S: 오버라이드 저장
 - L: 불러오기

NPC/대화:
 - 스페이스: 앞에 있는 NPC와 대화 시작/진행 (에디터 모드가 아닐 때)
"""

SCREEN_W, SCREEN_H = 960, 540
CENTER = V2(SCREEN_W // 2, SCREEN_H // 2)
FPS = 60

PLAYER_SPEED = 240.0
PLAYER_RADIUS = 14

BG_CLEAR_COLOR = (17, 19, 24)
FONT_NAME = "malgungothic"

# ===== 셀 기반 맵 설정 =====
TILE_SIZE = 256
MAP_ROWS = 12
MAP_COLS = 12
TILE_FOLDER = "assets/tiles"
WORLD_W, WORLD_H = MAP_COLS * TILE_SIZE, MAP_ROWS * TILE_SIZE

# 오버라이드 저장 파일
MAP_SAVE_PATH = "map_overrides.json"

# ===== NPC / 상호작용 설정 =====
INTERACT_DISTANCE = 70           # 대화 가능 최대 거리(픽셀, 월드 좌표)
INTERACT_FOV_DEG = 70            # 플레이어 전방 판정 시야각(도)
INTERACT_FOV_COS = math.cos(math.radians(INTERACT_FOV_DEG))
NPC_RADIUS = 16

_image_cache = {}
TILE_OVERRIDE = {}

# ---------- NPC & Dialog ----------

class NPC:
    def __init__(self, name: str, world_pos: V2, lines, color=(140, 185, 255)):
        """
        lines: ["문장1", "문장2", ...]
        """
        self.name = name
        self.world_pos = V2(world_pos)
        self.lines = list(lines)
        self.color = color
        self.radius = NPC_RADIUS

    def draw(self, surf: pygame.Surface, camera_offset: V2, font: pygame.font.Font):
        # NPC 본체
        pos = self.world_pos + camera_offset
        pygame.draw.circle(surf, self.color, pos, self.radius)
        pygame.draw.circle(surf, (20, 30, 40), pos, self.radius, 2)

        # 이름표
        name_img = font.render(self.name, True, (240, 240, 245))
        name_rect = name_img.get_rect(midbottom=(pos.x, pos.y - self.radius - 6))
        # 이름 배경
        pad = 6
        bg_rect = pygame.Rect(name_rect.x - pad, name_rect.y - 2, name_rect.width + pad*2, name_rect.height + 4)
        pygame.draw.rect(surf, (30, 35, 45), bg_rect, border_radius=6)
        pygame.draw.rect(surf, (60, 70, 85), bg_rect, 1, border_radius=6)
        surf.blit(name_img, name_rect)

    def is_in_front_of_player(self, player_pos: V2, player_facing: V2) -> bool:
        to_npc = self.world_pos - player_pos
        dist = to_npc.length()
        if dist > INTERACT_DISTANCE:
            return False
        if dist < 1:
            return True  # 사실상 겹침
        to_npc_norm = to_npc / dist
        # 플레이어가 멈춰있어도 아주 가깝다면 상호작용 허용
        if player_facing.length_squared() < 1e-6:
            return dist <= (INTERACT_DISTANCE * 0.6)
        # 전방 각도 판정
        return player_facing.dot(to_npc_norm) >= INTERACT_FOV_COS


class DialogManager:
    def __init__(self):
        self.active = False
        self.npc: NPC | None = None
        self.index = 0

    def open(self, npc: NPC):
        self.active = True
        self.npc = npc
        self.index = 0

    def close(self):
        self.active = False
        self.npc = None
        self.index = 0

    def progress(self):
        if not self.active or not self.npc:
            return
        self.index += 1
        if self.index >= len(self.npc.lines):
            self.close()

    def draw(self, surf: pygame.Surface, big_font: pygame.font.Font, font: pygame.font.Font):
        if not self.active or not self.npc:
            return
        # 하단 대화 박스
        box_h = 130
        box = pygame.Surface((SCREEN_W, box_h), pygame.SRCALPHA)
        box.fill((18, 20, 24, 235))
        surf.blit(box, (0, SCREEN_H - box_h))

        # 이름 표시
        name_text = f"{self.npc.name}"
        name_img = big_font.render(name_text, True, (250, 230, 170))
        surf.blit(name_img, (20, SCREEN_H - box_h + 14))

        # 대사 (자동 줄바꿈 간단 처리)
        text = self.npc.lines[self.index]
        draw_multiline(surf, text, font, (235, 235, 240), (20, SCREEN_H - box_h + 48), max_width=SCREEN_W - 40)

        # 안내
        hint = font.render("스페이스: 다음 | ESC: 닫기", True, (200, 200, 210))
        surf.blit(hint, (SCREEN_W - hint.get_width() - 16, SCREEN_H - hint.get_height() - 10))


def draw_multiline(surf, text, font, color, pos, max_width=800, line_spacing=6):
    words = list(text)
    # 글자 단위로 줄바꿈(한글 호환용). 필요시 단어 단위로 개선 가능.
    lines = []
    cur = ""
    for ch in words:
        candidate = cur + ch
        if font.size(candidate)[0] <= max_width:
            cur = candidate
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    x, y = pos
    for ln in lines:
        img = font.render(ln, True, color)
        surf.blit(img, (x, y))
        y += img.get_height() + line_spacing

# ---------- Map I/O ----------

def load_overrides():
    global TILE_OVERRIDE
    if not os.path.exists(MAP_SAVE_PATH):
        return
    try:
        with open(MAP_SAVE_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        parsed = {}
        for k, v in raw.items():
            try:
                r, c = map(int, k.split(","))
                parsed[(r, c)] = v
            except Exception:
                pass
        TILE_OVERRIDE = parsed
        _image_cache.clear()
    except Exception:
        pass


def save_overrides():
    try:
        data = {f"{r},{c}": p for (r, c), p in TILE_OVERRIDE.items()}
        with open(MAP_SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_image_cached(path: str):
    if path in _image_cache:
        return _image_cache[path]
    try:
        if not os.path.exists(path):
            _image_cache[path] = None
            return None
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (TILE_SIZE, TILE_SIZE))
        _image_cache[path] = img
        return img
    except Exception:
        _image_cache[path] = None
        return None


def get_cell_from_world(world_pos: V2):
    c = int(world_pos.x // TILE_SIZE) + 1
    r = int(world_pos.y // TILE_SIZE) + 1
    if 1 <= r <= MAP_ROWS and 1 <= c <= MAP_COLS:
        return (r, c)
    return None


def draw_background(surf: pygame.Surface, camera_offset: V2):
    surf.fill(BG_CLEAR_COLOR)

    top_left_world = -camera_offset
    bottom_right_world = V2(SCREEN_W, SCREEN_H) - camera_offset

    start_c = max(1, int(top_left_world.x // TILE_SIZE) + 1)
    end_c = min(MAP_COLS, int(bottom_right_world.x // TILE_SIZE) + 1)
    start_r = max(1, int(top_left_world.y // TILE_SIZE) + 1)
    end_r = min(MAP_ROWS, int(bottom_right_world.y // TILE_SIZE) + 1)

    for r in range(start_r, end_r + 1):
        for c in range(start_c, end_c + 1):
            path = TILE_OVERRIDE.get((r, c))
            if not path:
                filename = f"{r}-{c}.png"
                path = os.path.join(TILE_FOLDER, filename)
            img = load_image_cached(path)
            if img is None:
                continue
            world_x = (c - 1) * TILE_SIZE
            world_y = (r - 1) * TILE_SIZE
            if 0 <= world_x < WORLD_W and 0 <= world_y < WORLD_H:
                spos = V2(world_x, world_y) + camera_offset
                surf.blit(img, spos)

    rect_screen = pygame.Rect(0, 0, WORLD_W, WORLD_H)
    rect_screen.topleft = camera_offset
    pygame.draw.rect(surf, (50, 58, 70), rect_screen, 1)


def clamp_to_world(pos: V2) -> V2:
    return V2(max(0, min(WORLD_W, pos.x)), max(0, min(WORLD_H, pos.y)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("LoL-style Camera | 타일맵 + 인게임 에디터 + NPC 대화")
    clock = pygame.time.Clock()

    load_overrides()

    player_world = V2(WORLD_W / 2, WORLD_H / 2)
    move_target = None
    player_facing = V2(1, 0)  # 기본적으로 오른쪽 바라봄

    font = pygame.font.SysFont(FONT_NAME, 18)
    big_font = pygame.font.SysFont(FONT_NAME, 22)

    editor_mode = False
    editing_cell = None
    input_text = ""

    # ---- NPC들 생성 (원하는 만큼 추가) ----
    npcs: list[NPC] = [
        NPC("연맹 파수꾼", V2(WORLD_W/2 + 100, WORLD_H/2), [
            "안녕, 여행자! 하늘섬 연맹에 처음 왔나?",
            "지도에서 북동쪽으로 가면 오래된 비석이 있어.",
            "거기서 바람소리를 잘 들어보게."
        ]),
        NPC("상인 로웰", V2(WORLD_W/2 - 220, WORLD_H/2 + 180), [
            "오오, 모험가의 눈빛이군!",
            "필요한 게 있으면 언제든지 찾아오라고."
        ], color=(255, 170, 120)),
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
                        editing_cell = None
                        input_text = ""
                    else:
                        running = False

                elif event.key == pygame.K_e:
                    # 에디터 토글 시 대화도 닫음
                    editor_mode = not editor_mode
                    dialog.close()
                    editing_cell = None
                    input_text = ""

                elif event.key == pygame.K_s and editor_mode:
                    save_overrides()

                elif event.key == pygame.K_l and editor_mode:
                    load_overrides()

                # ---- 스페이스: 대화 열기/진행 ----
                elif event.key == pygame.K_SPACE and not editor_mode:
                    if dialog.active:
                        dialog.progress()
                    else:
                        # 가장 가까운, 전방의 NPC 찾아 대화 시작
                        best_npc = None
                        best_dist = 1e9
                        for n in npcs:
                            if n.is_in_front_of_player(player_world, player_facing):
                                d = (n.world_pos - player_world).length()
                                if d < best_dist:
                                    best_dist = d
                                    best_npc = n
                        if best_npc:
                            dialog.open(best_npc)

                # ---- 에디터 입력 ----
                elif editor_mode and editing_cell is not None:
                    if event.key == pygame.K_RETURN:
                        if input_text.strip() == "":
                            TILE_OVERRIDE.pop(editing_cell, None)
                        else:
                            TILE_OVERRIDE[editing_cell] = input_text.strip()
                        _image_cache.pop(input_text.strip(), None)
                        editing_cell = None
                        input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        ch = event.unicode
                        if ch:
                            input_text += ch

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 우클릭 이동은 대화/에디터가 아닐 때만
                if event.button == 3 and (not editor_mode) and (not dialog.active):
                    mouse_screen = V2(event.pos)
                    camera_offset = CENTER - player_world
                    move_target = clamp_to_world(mouse_screen - camera_offset)
                # 에디터 좌클릭
                elif event.button == 1 and editor_mode:
                    camera_offset = CENTER - player_world
                    world_pos = V2(event.pos) - camera_offset
                    cell = get_cell_from_world(world_pos)
                    if cell is not None:
                        editing_cell = cell
                        r, c = cell
                        current_path = TILE_OVERRIDE.get(cell)
                        if not current_path:
                            current_path = os.path.join(TILE_FOLDER, f"{r}-{c}.png")
                        input_text = current_path

        # ---- 이동 업데이트(대화/에디터가 아닐 때만) ----
        if move_target is not None and (not editor_mode) and (not dialog.active):
            to_target = move_target - player_world
            dist = to_target.length()
            if dist < 2:
                move_target = None
            else:
                dir_vec = to_target.normalize()
                player_facing = dir_vec  # 바라보는 방향 갱신
                player_world += dir_vec * PLAYER_SPEED * dt
                player_world = clamp_to_world(player_world)

        camera_offset = CENTER - player_world

        # ---- 렌더 ----
        draw_background(screen, camera_offset)

        # 이동 목표 표시
        if move_target is not None and (not editor_mode) and (not dialog.active):
            tpos = move_target + camera_offset
            pygame.draw.circle(screen, (200, 120, 40), tpos, 8, 2)
            pygame.draw.circle(screen, (200, 160, 60), tpos, 14, 1)

        # NPC 그리기
        for n in npcs:
            n.draw(screen, camera_offset, font)

        # 플레이어(화면 중앙 고정)
        pygame.draw.circle(screen, (220, 220, 235), CENTER, PLAYER_RADIUS)
        pygame.draw.circle(screen, (90, 100, 120), CENTER, PLAYER_RADIUS, 2)

        # 플레이어 바라보는 작은 표시(전방)
        if player_facing.length_squared() > 1e-6:
            tip = CENTER + player_facing.normalize() * (PLAYER_RADIUS + 10)
            pygame.draw.circle(screen, (255, 210, 80), tip, 3)

        # UI 라인
        ui_lines = [
            "우클릭: 이동 | 스페이스: NPC 대화 | E: 에디터 모드 | 좌클릭(에디터): 셀 선택",
            "에디터 단축키: Enter=적용, ESC=취소, S=저장, L=불러오기",
            f"TILE_SIZE={TILE_SIZE}, MAP={MAP_ROWS}x{MAP_COLS}",
        ]
        for i, s in enumerate(ui_lines):
            img = font.render(s, True, (230, 230, 235))
            screen.blit(img, (12, 10 + i * 20))

        # 에디터 배너 & 하이라이트
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

        # 대화창
        dialog.draw(screen, big_font, font)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
