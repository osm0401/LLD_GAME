# main.py
# ------------------------------------------------------------
# 카지노: 사이드뷰(A/D + 바닥 스냅)
# 연구실: 아이작식 탑다운(WASD)
#
# 기능
# - SPACE: NPC 대화
# - E: 인벤토리 토글
# - F: 워프 게이트 상호작용
# - 연구실 입장 시 TopdownView로 렌더/카메라 전환
#
# 개선 포인트
# - top.enter/exit 은 "씬 변경 시점"에만 호출
# - JSON 경로를 main.py 기준 절대경로로 생성(Working Dir 문제 완화)
# - 인벤/대화 중 워프 입력 차단
# - 레벨 메서드 유무에 따른 안전한 바닥/스폰 처리
# ------------------------------------------------------------

import os
import sys
import pygame

import settings as S
from player import Player
from level import Level
from npc import NPC
from isac import TopdownView
import key as K

# ------------------------------------------------------------
# 경로 유틸(Working Directory 이슈 완화)
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def base_dir():
    # PyInstaller exe로 실행 중이면 exe 위치
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # 개발 중이면 main.py 위치
    return os.path.dirname(os.path.abspath(__file__))
def p(*paths):
    return os.path.join(base_dir(), *paths)

def resource_path(relative_path):
    # onefile일 때 임시 풀린 경로
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)

# ------------------------------------------------------------
# 폰트 유틸
# ------------------------------------------------------------
def _sysfont(name, size):
    try:
        return pygame.font.SysFont(name, size)
    except Exception:
        return pygame.font.SysFont(None, size)


class _NoKeys:
    """대화/인벤토리 중 이동 입력 차단용."""
    def __getitem__(self, k):
        return False


# ------------------------------------------------------------
# 인벤토리(지금은 UI만 유지)
# ------------------------------------------------------------
class Inventory:
    def __init__(self, font):
        self.font = font
        self.is_open = False
        self.cell = 48
        self.gap = 6

        self.weapon_slots = [None, None]
        self.evience_slots = [None, None, None, None, None]  # 원본 유지

        self.weapon_slots[0] = {"name": "장검"}
        self.weapon_slots[1] = {"name": "단검"}
        self.evience_slots[0] = {"name": "은행의 비밀 장부"}

        # 선택: 플레이어 아바타 이미지 표시용
        self.avatar_img = None

    def set_avatar(self, img):
        self.avatar_img = img

    def toggle(self):
        self.is_open = not self.is_open

    def draw(self, surf):
        if not self.is_open:
            return

        w = int(S.SCREEN_W * 0.6)
        h = int(S.SCREEN_H * 0.6)
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((15, 18, 25, 235))
        rect = panel.get_rect(center=(S.SCREEN_W // 2, S.SCREEN_H // 2))
        surf.blit(panel, rect.topleft)

        title = self.font.render("인벤토리 (E로 닫기)", True, (250, 230, 170))
        surf.blit(title, (rect.x + 20, rect.y + 20))

        cell, gap = self.cell, self.gap
        base_x = rect.x + 20
        base_y = rect.y + 60

        # 1) 사진 슬롯(2x3을 합친 큰 슬롯)
        avatar_cols, avatar_rows = 2, 3
        total_w = avatar_cols * cell + (avatar_cols - 1) * gap
        total_h = avatar_rows * cell + (avatar_rows - 1) * gap
        avatar_area = pygame.Rect(base_x, base_y, total_w, total_h)

        pygame.draw.rect(surf, (65, 70, 95), avatar_area)
        pygame.draw.rect(surf, (230, 230, 240), avatar_area, 2)

        if self.avatar_img:
            try:
                img = pygame.transform.smoothscale(self.avatar_img, (avatar_area.w, avatar_area.h))
                surf.blit(img, avatar_area.topleft)
            except Exception:
                pass
        else:
            photo_text = self.font.render("사진", True, (230, 230, 240))
            surf.blit(photo_text, (
                avatar_area.centerx - photo_text.get_width() // 2,
                avatar_area.centery - photo_text.get_height() // 2
            ))

        # 2) 무기 2개(각각 2칸 연결)
        weapon_label = self.font.render("무기", True, (230, 230, 240))
        weapon_origin_x = avatar_area.right + 40
        weapon_origin_y = base_y
        surf.blit(weapon_label, (weapon_origin_x, weapon_origin_y - 26))

        slot_width = 2 * cell + gap
        slot_height = cell

        for i, item in enumerate(self.weapon_slots):
            sx = weapon_origin_x
            sy = weapon_origin_y + i * (slot_height + 20)
            big_rect = pygame.Rect(sx, sy, slot_width, slot_height)

            pygame.draw.rect(surf, (60, 65, 85), big_rect)
            pygame.draw.rect(surf, (220, 220, 230), big_rect, 2)

            if item and "name" in item:
                txt = self.font.render(item["name"], True, (235, 235, 245))
                surf.blit(txt, (
                    big_rect.centerx - txt.get_width() // 2,
                    big_rect.centery - txt.get_height() // 2
                ))

        # 3) 소모품 5칸
        consum_label = self.font.render("소모품", True, (230, 230, 240))
        cons_origin_x = weapon_origin_x
        cons_origin_y = rect.bottom - 30 - cell
        surf.blit(consum_label, (cons_origin_x, cons_origin_y - 26))

        for i in range(5):
            cx = cons_origin_x + i * (cell + gap)
            cy = cons_origin_y
            c_rect = pygame.Rect(cx, cy, cell, cell)

            pygame.draw.rect(surf, (60, 65, 85), c_rect)
            pygame.draw.rect(surf, (220, 220, 230), c_rect, 2)

            item = self.evience_slots[i] if i < len(self.evience_slots) else None
            if item and "name" in item:
                txt = self.font.render(item["name"], True, (235, 235, 245))
                surf.blit(txt, (c_rect.x + 4, c_rect.y + c_rect.h // 2 - txt.get_height() // 2))


# ------------------------------------------------------------
# 워프 게이트
# ------------------------------------------------------------
class WarpGate:
    def __init__(self, world_x, level, label, target_scene):
        self.w, self.h = 40, 90

        # 레벨 지원 함수 유무에 따른 안전한 base_y 계산
        if hasattr(level, "get_support_y"):
            base_y = level.get_support_y(world_x)
        elif hasattr(level, "surface_y_rect_x"):
            base_y = level.surface_y_rect_x(world_x)
        else:
            base_y = getattr(S, "GROUND_Y", int(S.SCREEN_H * 0.78))

        self.x = world_x - self.w // 2
        self.y = base_y - self.h

        self.label = label
        self.target_scene = target_scene
        self.range = 90
        self.font = _sysfont(S.FONT_NAME, 18)

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, player_rect, events, *, blocked=False):
        if blocked:
            return False, False

        # 2D 거리 기반
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        near = (dx * dx + dy * dy) ** 0.5 <= self.range

        activated = False
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == K.INTERACT and near:
                activated = True

        return near, activated

    def draw_side(self, surf, camera_x):
        sx = int(self.x - camera_x)
        sy = int(self.y)
        r = pygame.Rect(sx, sy, self.w, self.h)
        pygame.draw.rect(surf, (120, 220, 255), r, border_radius=10)
        pygame.draw.rect(surf, (20, 40, 60), r, 2)

    def draw_hint_side(self, surf, camera_x, near):
        if not near:
            return
        text = self.font.render(f"F: {self.label}", True, (30, 30, 40))
        box = pygame.Surface((text.get_width() + 10, text.get_height() + 6), pygame.SRCALPHA)
        box.fill((255, 255, 255, 210))

        sx = int(self.rect.centerx - camera_x) - box.get_width() // 2
        sy = self.rect.top - 50
        surf.blit(box, (sx, sy))
        surf.blit(text, (sx + 5, sy + 3))


# ------------------------------------------------------------
# 씬 빌드
# ------------------------------------------------------------
def _safe_spawn_y_side(level, spawn_x):
    r = pygame.Rect(spawn_x, 0, *S.PLAYER_SIZE)
    if hasattr(level, "surface_y"):
        return level.surface_y(r)
    # fallback
    return getattr(S, "GROUND_Y", int(S.SCREEN_H * 0.78)) - S.PLAYER_SIZE[1]


def build_scene(scene_id: str):
    """
    반환:
      level, spawn_pos(x,y), npc, gate
    """
    if scene_id == "casino":
        level = Level(p("casino_map.json"))

        spawn_x = 1200
        spawn_y = _safe_spawn_y_side(level, spawn_x)

        npc = NPC("워니", 1400, level)
        gate = WarpGate(2000, level, "연구실로 이동", "lab")
        return level, (spawn_x, spawn_y), npc, gate

    if scene_id == "lab":
        level = Level(p("map_lab.json"))

        spawn_x = 400
        spawn_y = 200

        npc = NPC("상미니", 600, level)
        gate = WarpGate(300, level, "카지노로 돌아가기", "casino")
        return level, (spawn_x, spawn_y), npc, gate

    # fallback
    return build_scene("casino")


# ------------------------------------------------------------
# 씬 로드 헬퍼
# ------------------------------------------------------------
def load_scene(scene_id, player, top):
    level, spawn_pos, npc, gate = build_scene(scene_id)

    # 스폰 이동
    player.pos.x, player.pos.y = spawn_pos

    # 씬 진입 시점에만 모드 전환
    if scene_id == "lab":
        top.enter(player)
        top.camera_x = 0.0
        top.camera_y = 0.0
    else:
        top.exit(player)

    return level, spawn_pos, npc, gate


# ------------------------------------------------------------
# 메인
# ------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
    pygame.display.set_caption("LLD_GAME")
    clock = pygame.time.Clock()
    font = _sysfont(getattr(S, "FONT_NAME", None), 18)

    inventory = Inventory(font)
    top = TopdownView()

    # 플레이어(초기 값은 카지노 기준)
    player = Player((0, 0))

    # 첫 씬
    current_scene = "casino"
    level, spawn_pos, npc, gate = load_scene(current_scene, player, top)

    # 인벤 아바타에 플레이어 스프라이트 연결(있다면)
    if getattr(player, "sprite", None):
        inventory.set_avatar(player.sprite)

    # 사이드뷰 카메라
    player = Player(spawn_pos)

    # 사이드뷰 카메라
    camera_x = 0.0

    running = True
    last_talk_active = False  # ✅ 직전 프레임에 대화 중이었는지
    while running:
        dt = clock.tick(S.FPS) / 1000.0
        events = pygame.event.get()

        # -------------------------
        # 기본 이벤트
        # -------------------------
        for e in events:
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == K.INVENTORY:
                    inventory.toggle()

        # -------------------------
        # 인벤 열림 시 일부 입력 차단
        # - NPC SPACE 차단
        # - 워프 F는 gate.update에서 blocked로 처리
        # -------------------------
        npc_events = events
        if inventory.is_open:
            filtered = []
            for e in events:
                if e.type == pygame.KEYDOWN and (e.key == pygame.K_w):
                    continue
                filtered.append(e)
            npc_events = filtered

        # -------------------------
        # NPC 업데이트
        # -------------------------
        near_npc = npc.update(player.rect, npc_events)

        # 이번 프레임 대화 상태
        talk_active_now = getattr(npc, "talk_active", False)

        # 이번 프레임에 SPACE(대화 진행 키)가 눌렸는지
        used_continue_key = any(
            e.type == pygame.KEYDOWN and e.key == K.CONTINUE_TALK
            for e in events
        )

        # ✅ "직전에는 대화 중이었고, 지금은 아니고, 이번 프레임에 SPACE를 눌렀다" = 대화 막 끝난 프레임
        talk_just_closed = (last_talk_active and not talk_active_now and used_continue_key)

        # -------------------------
        # 게이트 업데이트
        # - 인벤/대화 중에는 워프 금지
        # -------------------------
        warp_blocked = inventory.is_open or getattr(npc, "talk_active", False)
        near_gate, gate_on = gate.update(player.rect, events, blocked=warp_blocked)

        # -------------------------
        # 입력 처리
        # -------------------------
        keys = pygame.key.get_pressed()

        # 점프만 막는 키 래퍼
        class _JumpFilteredKeys:
            def __init__(self, base):
                self._base = base

            def __getitem__(self, k):
                # 대화 막 끝난 프레임에 SPACE/W 점프만 무시
                if k == K.JUMP_SPACE or k == K.JUMP_W:
                    return False
                return self._base[k]

        # 1) 대화 중 또는 인벤토리 열림 → 전체 이동/점프 입력 차단
        if talk_active_now or inventory.is_open:
            keys_use = _NoKeys()

        # 2) 이번 프레임에 막 SPACE로 대화가 끝났다면 → 점프만 막고 나머지 입력 허용
        elif talk_just_closed:
            keys_use = _JumpFilteredKeys(keys)

        # 3) 그 외에는 그대로 사용
        else:
            keys_use = keys

        # -------------------------
        # 플레이어 업데이트
        # -------------------------
        player.update(dt, keys_use, level)

        # -------------------------
        # 워프 처리
        # -------------------------
        if gate_on:
            current_scene = gate.target_scene
            level, spawn_pos, npc, gate = load_scene(current_scene, player, top)

            # 사이드뷰 카메라 리셋
            if current_scene == "casino":
                camera_x = 0.0

        # -------------------------
        # 카메라 업데이트
        # -------------------------
        if current_scene == "casino":
            target = player.pos.x + player.w / 2 - S.SCREEN_W / 2
            if getattr(level, "world_w", S.SCREEN_W) > S.SCREEN_W:
                target = max(0, min(level.world_w - S.SCREEN_W, target))
            else:
                target = 0
            camera_x += (target - camera_x) * min(1.0, dt * 8.0)
        else:
            top.update(dt, player, level)

        # -------------------------
        # 렌더
        # -------------------------
        if current_scene == "casino":
            level.draw(screen, camera_x)
            gate.draw_side(screen, camera_x)
            npc.draw(screen, camera_x)
            player.draw(screen, camera_x)

            gate.draw_hint_side(screen, camera_x, near_gate)
            npc.draw_dialog(screen, camera_x, near_npc, S.SCREEN_W, S.SCREEN_H)

        else:
            # 연구실 탑다운 렌더
            top.draw(screen, level, player, npcs=[npc], gates=[gate])

            # 대화 UI는 화면 고정 방식이므로 camera_x=0으로 유지
            try:
                npc.draw_dialog(screen, 0, near_npc, S.SCREEN_W, S.SCREEN_H)
            except Exception:
                pass

        # 인벤 UI
        inventory.draw(screen)

        # -------------------------
        # 도움말
        # -------------------------
        help_lines = [
            "카지노: A/D 이동  SPACE 대화  E 인벤  F 워프",
            "연구실: WASD 이동(아이작 시점)  SPACE 대화  E 인벤  F 워프",
            f"현재 씬: {current_scene}",
        ]
        for i, s in enumerate(help_lines):
            img = font.render(s, True, (30, 30, 40))
            box = pygame.Surface((img.get_width() + 10, img.get_height() + 4), pygame.SRCALPHA)
            box.fill((255, 255, 255, 150))
            screen.blit(box, (10, 10 + i * 22))
            screen.blit(img, (15, 12 + i * 22))

        pygame.display.flip()
        last_talk_active = talk_active_now

    pygame.quit()


if __name__ == "__main__":
    main()
