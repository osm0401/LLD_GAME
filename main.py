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
# ------------------------------------------------------------

import pygame
import settings as S
from player import Player
from level import Level
from npc import NPC
from isac import TopdownView


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
        self.evience_slots = [None, None, None, None, None]

        self.weapon_slots[0] = {"name": "장검"}
        self.weapon_slots[1] = {"name": "단검"}
        self.evience_slots[0] = {"name": "은행의 비밀 장부"}

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

            item = self.evience_slots[i]
            if item and "name" in item:
                txt = self.font.render(item["name"], True, (235, 235, 245))
                surf.blit(txt, (c_rect.x + 4, c_rect.y + c_rect.h // 2 - txt.get_height() // 2))


# ------------------------------------------------------------
# 워프 게이트
# ------------------------------------------------------------
class WarpGate:
    def __init__(self, world_x, level, label, target_scene):
        self.w, self.h = 40, 90
        base_y = level.get_support_y(world_x) if hasattr(level, "get_support_y") else level.surface_y_rect_x(world_x)
        self.x = world_x - self.w // 2
        self.y = base_y - self.h

        self.label = label
        self.target_scene = target_scene
        self.range = 90
        self.font = _sysfont(S.FONT_NAME, 18)

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, player_rect, events):
        # 2D 거리 기반으로 안전하게
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        near = (dx * dx + dy * dy) ** 0.5 <= self.range

        activated = False
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_f and near:
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
def build_scene(scene_id: str):
    """
    반환:
      level, spawn_pos(x,y), npc, gate
    """

    if scene_id == "casino":
        level = Level("casino_map.json")

        spawn_x = 1200
        # 사이드뷰 시작 y는 바닥에 붙이기
        spawn_y = level.surface_y(pygame.Rect(spawn_x, 0, *S.PLAYER_SIZE))

        npc = NPC("워니", 1400, level)
        gate = WarpGate(2000, level, "연구실로 이동", "lab")

        return level, (spawn_x, spawn_y), npc, gate

    if scene_id == "lab":
        level = Level("map_lab.json")

        # 탑다운은 바닥 스냅이 없으니 적당히 안전한 위치
        spawn_x = 400
        spawn_y = 200

        # ✅ 연구실 대화는 상미니
        npc = NPC("상미니", 600, level)
        gate = WarpGate(300, level, "카지노로 돌아가기", "casino")

        return level, (spawn_x, spawn_y), npc, gate

    # fallback
    return build_scene("casino")


# ------------------------------------------------------------
# 메인
# ------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
    clock = pygame.time.Clock()
    font = _sysfont(S.FONT_NAME, 18)

    inventory = Inventory(font)
    top = TopdownView()  # ✅ 연구실 탑다운 컨트롤러

    # 첫 씬
    current_scene = "casino"
    level, spawn_pos, npc, gate = build_scene(current_scene)

    player = Player(spawn_pos)

    # 사이드뷰 카메라
    camera_x = 0.0

    running = True
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
                if e.key == pygame.K_e:
                    inventory.toggle()

        # -------------------------
        # 씬별 모드 전환
        # -------------------------
        if current_scene == "lab":
            top.enter(player)
        else:
            top.exit(player)

        # -------------------------
        # 인벤 열림 시 NPC/게이트 입력 일부 제한
        # -------------------------
        npc_events = events
        if inventory.is_open:
            filtered = []
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                    continue
                filtered.append(e)
            npc_events = filtered

        # -------------------------
        # NPC 업데이트
        # -------------------------
        near_npc = npc.update(player.rect, npc_events)

        # -------------------------
        # 게이트 업데이트
        # -------------------------
        near_gate, gate_on = gate.update(player.rect, events)

        # -------------------------
        # 입력 처리
        # -------------------------
        keys = pygame.key.get_pressed()

        # 대화/인벤 중 이동 차단
        if getattr(npc, "talk_active", False) or inventory.is_open:
            keys_use = _NoKeys()
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
            level, spawn_pos, npc, gate = build_scene(current_scene)
            player.pos.x, player.pos.y = spawn_pos
            # 탑다운 진입 즉시 카메라 리셋 느낌
            if current_scene == "lab":
                top.camera_x = 0.0
                top.camera_y = 0.0
            else:
                camera_x = 0.0

        # -------------------------
        # 카메라 업데이트
        # -------------------------
        if current_scene == "casino":
            # 사이드뷰 카메라
            target = player.pos.x + player.w / 2 - S.SCREEN_W / 2
            if level.world_w > S.SCREEN_W:
                target = max(0, min(level.world_w - S.SCREEN_W, target))
            else:
                target = 0
            camera_x += (target - camera_x) * min(1.0, dt * 8.0)

        else:
            # 탑다운 카메라
            top.update(dt, player, level)

        # -------------------------
        # 렌더
        # -------------------------
        if current_scene == "casino":
            level.draw(screen, camera_x)
            gate.draw_side(screen, camera_x)
            npc.draw(screen, camera_x)
            player.draw(screen, camera_x)

            # 힌트/대사
            gate.draw_hint_side(screen, camera_x, near_gate)
            npc.draw_dialog(screen, camera_x, near_npc, S.SCREEN_W, S.SCREEN_H)

        else:
            # ✅ 연구실: 아이작식 탑다운 렌더
            top.draw(screen, level, player, npcs=[npc], gates=[gate])

            # 탑다운에서도 대화 UI는 화면 고정 UI라 그대로 사용 가능
            # (camera_x만 받는 구조라면 0 넣어도 됨)
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

    pygame.quit()


if __name__ == "__main__":
    main()
