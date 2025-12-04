# main.py — 사이드뷰 런처
# 기능 요약:
# - A/D : 좌우 이동
# - SPACE : 가까운 NPC와 대화
# - E : 인벤토리 열기/닫기
# - F : 워프 게이트 상호작용(다른 맵으로 이동)
# - F2 : 맵 에디터 ON/OFF (벽/지형지물/바닥 수정 + S로 JSON 저장)

import pygame
from settings import SCREEN_W, SCREEN_H, FPS, FONT_NAME
from player import Player
from level import Level
from npc import NPC


# -----------------------------------------------------------------------------
# 1. 유틸리티
# -----------------------------------------------------------------------------
def _sysfont(name: str, size: int) -> pygame.font.Font:
    """시스템 폰트를 안전하게 가져오는 헬퍼."""
    try:
        return pygame.font.SysFont(name, size)
    except Exception:
        return pygame.font.SysFont(None, size)


class _NoKeys:
    """대화/인벤토리/에디터 중 입력 차단용: 어떤 키를 물어봐도 항상 False."""
    def __getitem__(self, k):
        return False


# -----------------------------------------------------------------------------
# 2. 인벤토리 (E 키)
# -----------------------------------------------------------------------------
class Inventory:
    """E 키로 여닫는 칸 형태 인벤토리 UI."""

    def __init__(self, font: pygame.font.Font):
        self.font = font
        self.is_open = False

        # 칸(셀) 기본 크기와 간격
        self.cell = 48
        self.gap = 6

        # 인벤토리 데이터
        self.weapon_slots = [None, None]       # 무기 2칸
        self.evidence_slots = [None] * 5       # 증거/소모품 5칸

        # 테스트용 더미 아이템
        self.weapon_slots[0] = {"name": "장검"}
        self.weapon_slots[1] = {"name": "단검"}
        self.evidence_slots[0] = {"name": "은행의 비밀 장부"}

    def toggle(self):
        self.is_open = not self.is_open

    def draw(self, surf: pygame.Surface):
        if not self.is_open:
            return

        w = int(SCREEN_W * 0.6)
        h = int(SCREEN_H * 0.6)
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((15, 18, 25, 235))
        rect = panel.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
        surf.blit(panel, rect.topleft)

        cell = self.cell
        gap = self.gap

        # 제목
        title = self.font.render("인벤토리 (E로 닫기)", True, (250, 230, 170))
        surf.blit(title, (rect.x + 20, rect.y + 20))

        # 기준 위치
        base_x = rect.x + 20
        base_y = rect.y + 60

        # ------------------------------------------------------------------
        # (1) 왼쪽 위: 사진 슬롯 (2×3 크기의 큰 슬롯 하나)
        # ------------------------------------------------------------------
        avatar_cols = 2
        avatar_rows = 3

        total_w = avatar_cols * cell + (avatar_cols - 1) * gap
        total_h = avatar_rows * cell + (avatar_rows - 1) * gap
        avatar_area = pygame.Rect(base_x, base_y, total_w, total_h)

        pygame.draw.rect(surf, (65, 70, 95), avatar_area)       # 안쪽
        pygame.draw.rect(surf, (230, 230, 240), avatar_area, 2) # 테두리

        photo_text = self.font.render("사진", True, (230, 230, 240))
        surf.blit(
            photo_text,
            (
                avatar_area.centerx - photo_text.get_width() // 2,
                avatar_area.centery - photo_text.get_height() // 2,
            ),
        )

        # ------------------------------------------------------------------
        # (2) 오른쪽: 무기 슬롯 2개 (가로 2칸짜리 긴 슬롯)
        # ------------------------------------------------------------------
        weapon_label = self.font.render("무기", True, (230, 230, 240))

        weapon_origin_x = avatar_area.right + 40
        weapon_origin_y = base_y
        surf.blit(weapon_label, (weapon_origin_x, weapon_origin_y - 26))

        weapon_cols = 2
        slot_width = weapon_cols * cell + (weapon_cols - 1) * gap
        slot_height = cell

        for i, item in enumerate(self.weapon_slots):
            sx = weapon_origin_x
            sy = weapon_origin_y + i * (slot_height + 20)

            big_rect = pygame.Rect(sx, sy, slot_width, slot_height)
            pygame.draw.rect(surf, (60, 65, 85), big_rect)
            pygame.draw.rect(surf, (220, 220, 230), big_rect, 2)

            if item is not None and "name" in item:
                txt = self.font.render(item["name"], True, (235, 235, 245))
                surf.blit(
                    txt,
                    (
                        big_rect.centerx - txt.get_width() // 2,
                        big_rect.centery - txt.get_height() // 2,
                    ),
                )

        # ------------------------------------------------------------------
        # (3) 아래쪽: 증거/소모품 5칸
        # ------------------------------------------------------------------
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

            item = self.evidence_slots[i]
            if item is not None and "name" in item:
                txt = self.font.render(item["name"], True, (235, 235, 245))
                surf.blit(
                    txt,
                    (
                        c_rect.x + 4,
                        c_rect.y + c_rect.h // 2 - txt.get_height() // 2,
                    ),
                )


# -----------------------------------------------------------------------------
# 3. 워프 게이트 (F 키)
# -----------------------------------------------------------------------------
class WarpGate:
    """플레이어가 가까이서 F를 누르면 다른 맵으로 보내주는 워프 게이트."""

    def __init__(self, world_x: int, level: Level, label: str, target_scene: str):
        self.w = 40
        self.h = 90

        ground_y = level.surface_y_rect_x(world_x)
        self.x = world_x - self.w // 2
        self.y = ground_y - self.h

        self.label = label              # 힌트에 표시할 텍스트
        self.target_scene = target_scene  # 예: "city", "lab"
        self.range = 80                 # 상호작용 가능한 거리
        self.font = _sysfont(FONT_NAME, 18)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, player_rect: pygame.Rect, events) -> tuple[bool, bool]:
        """
        - near: 플레이어가 게이트 근처에 있는지
        - activated: 근처에서 F 키를 눌렀는지
        """
        near = abs(player_rect.centerx - self.rect.centerx) <= self.range
        activated = False
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_f and near:
                activated = True
        return near, activated

    def draw(self, surf: pygame.Surface, camera_x: float):
        sx = int(self.x - camera_x)
        sy = int(self.y)
        gate_rect = pygame.Rect(sx, sy, self.w, self.h)

        pygame.draw.rect(surf, (120, 220, 255), gate_rect, border_radius=10)
        pygame.draw.rect(surf, (20, 40, 60), gate_rect, 2)

    def draw_hint(self, surf: pygame.Surface, camera_x: float, near: bool):
        if not near:
            return

        text = self.font.render(f"F: {self.label}", True, (30, 30, 40))
        box = pygame.Surface((text.get_width() + 10, text.get_height() + 6), pygame.SRCALPHA)
        box.fill((255, 255, 255, 210))

        sx = int(self.rect.centerx - camera_x) - box.get_width() // 2
        sy = self.rect.top - 50
        surf.blit(box, (sx, sy))
        surf.blit(text, (sx + 5, sy + 3))


# -----------------------------------------------------------------------------
# 4. 씬(맵) 구성 함수 — 맵별 NPC/워프/레벨 생성
# -----------------------------------------------------------------------------
def build_scene(scene_id: str) -> tuple[Level, int, NPC, WarpGate]:
    """
    scene_id에 따라:
      - Level 인스턴스 (map_<scene_id>.json 사용)
      - 플레이어 시작 x 위치
      - 해당 맵의 NPC 한 명
      - 해당 맵의 워프 게이트 하나
    를 만들어서 반환.
    """
    level = Level(scene_id)

    if scene_id == "city":
        # 첫 번째 맵: 워니 + 연구소로 가는 게이트
        spawn_x = 1200

        npc = NPC(
            "워니",
            1400,
            level,
            lines_by_visit=[
                [
                    "안녕 오늘도 하루가 시작됐네",
                    "진짜 오늘도 일가고 내일도 일가고",
                    "아니 주 100시간 제가 도입된대",
                    "아 너무 힘들다",
                ],
                [
                    "왜 뭐 할말 있어??",
                ],
                [
                    "음 이제 말 그만 걸어줄레??",
                ],
                [
                    "나 이제 일 가야해",
                ],
            ],
        )

        gate = WarpGate(
            world_x=2000,
            level=level,
            label="연구소로 이동",
            target_scene="lab",
        )

    elif scene_id == "lab":
        # 두 번째 맵: 상미니 + 도시로 돌아가는 게이트
        spawn_x = 400

        npc = NPC(
            "상미니",
            600,
            level,
            lines_by_visit=[
                [
                    "여긴 두 번째 맵이야.",
                    "워프 게이트 잘 도착했지?",
                ],
                [
                    "또 왔네.",
                    "조사는 잘 되고 있어?",
                ],
                [
                    "이제 도시로 돌아가도 좋아.",
                ],
                [
                    "가끔은 쉬는 것도 잊지마.",
                ],
            ],
        )

        gate = WarpGate(
            world_x=300,
            level=level,
            label="도시로 돌아가기",
            target_scene="city",
        )

    else:
        # 이상한 값이면 city로 fallback
        return build_scene("city")

    return level, spawn_x, npc, gate


# -----------------------------------------------------------------------------
# 5. 메인 루프
# -----------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    font = _sysfont(FONT_NAME, 18)

    inventory = Inventory(font)

    # 맵 에디터 상태
    edit_mode = False
    edit_layer = "wall"  # "wall", "prop", "ground"

    # ---- 맵/씬 초기화 ----
    current_scene = "city"
    level, spawn_x, npc, gate = build_scene(current_scene)

    # 플레이어 생성 + 현재 맵 시작 위치로 이동
    player = Player((spawn_x, 0))
    player.pos.y = level.surface_y(player.rect)

    camera_x = 0.0
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        # ------------------------------------------------------
        # 이벤트 처리
        # ------------------------------------------------------
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_e:
                    # E : 인벤토리 열기/닫기
                    inventory.toggle()
                elif e.key == pygame.K_F2:
                    # F2 : 맵 에디터 모드 토글
                    edit_mode = not edit_mode
                elif edit_mode:
                    # 에디터 전용 단축키
                    if e.key == pygame.K_1:
                        edit_layer = "wall"
                    elif e.key == pygame.K_2:
                        edit_layer = "prop"
                    elif e.key == pygame.K_3:
                        edit_layer = "ground"
                    elif e.key == pygame.K_s:
                        # 현재 맵 상태를 JSON으로 저장
                        level.save_to_json()

            # 마우스 클릭 → 에디터 모드일 때만 동작
            if edit_mode and e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = e.pos
                world_x = mx + camera_x   # 카메라를 고려한 월드 좌표
                world_y = my

                if e.button == 1:  # 왼쪽 클릭: 추가/수정
                    if edit_layer == "wall":
                        level.add_wall(world_x - 20, world_y - 80, 40, 80)
                    elif edit_layer == "prop":
                        level.add_prop(world_x - 16, world_y - 32, 32, 32)
                    elif edit_layer == "ground":
                        level.adjust_ground_at(world_x, world_y)
                elif e.button == 3:  # 오른쪽 클릭: 삭제
                    if edit_layer == "wall":
                        level.remove_wall_at(world_x, world_y)
                    elif edit_layer == "prop":
                        level.remove_prop_at(world_x, world_y)

        # 인벤토리나 에디터가 열려 있으면 NPC/게이트 상호작용은 막기
        if inventory.is_open or edit_mode:
            npc_events = []
            gate_events = []
        else:
            npc_events = events
            gate_events = events

        # ------------------------------------------------------
        # NPC / 워프 게이트 업데이트
        # ------------------------------------------------------
        near_npc = npc.update(player.rect, npc_events)
        near_gate, gate_activated = gate.update(player.rect, gate_events)

        # F 키로 워프 발동 → 씬 전환
        if gate_activated:
            current_scene = gate.target_scene
            level, spawn_x, npc, gate = build_scene(current_scene)
            player.pos.x = spawn_x
            player.pos.y = level.surface_y(player.rect)
            player.vel.x = 0

        # ------------------------------------------------------
        # 플레이어 이동 업데이트
        # ------------------------------------------------------
        keys = pygame.key.get_pressed()
        if npc.talk_active or inventory.is_open or edit_mode:
            keys_use = _NoKeys()
        else:
            keys_use = keys

        player.update(dt, keys_use, level)

        # ------------------------------------------------------
        # 카메라 업데이트
        # ------------------------------------------------------
        target = player.pos.x + player.w / 2 - SCREEN_W / 2
        world_w = level.world_w

        if world_w > SCREEN_W:
            if target < 0:
                target = 0
            if target > world_w - SCREEN_W:
                target = world_w - SCREEN_W
        else:
            target = 0

        camera_x += (target - camera_x) * min(1.0, dt * 8.0)

        # ------------------------------------------------------
        # 렌더링
        # ------------------------------------------------------
        level.draw(screen, camera_x)
        gate.draw(screen, camera_x)
        npc.draw(screen, camera_x)
        player.draw(screen, camera_x)

        npc.draw_dialog(screen, camera_x, near_npc, SCREEN_W, SCREEN_H)
        gate.draw_hint(screen, camera_x, near_gate)

        inventory.draw(screen)

        # 도움말
        help_lines = [
            "A/D: 이동   SPACE: 대화   E: 인벤토리   F: 워프 게이트",
            "F2: 맵 에디터  (에디터 ON: 1=벽  2=지형지물  3=바닥  S=저장, 마우스 좌/우 클릭)",
        ]
        for i, s in enumerate(help_lines):
            img = font.render(s, True, (30, 30, 40))
            box = pygame.Surface((img.get_width() + 10, img.get_height() + 4), pygame.SRCALPHA)
            box.fill((255, 255, 255, 150))
            screen.blit(box, (10, 10 + i * 22))
            screen.blit(img, (15, 12 + i * 22))

        # 에디터 상태 표시 (화면 아래)
        if edit_mode:
            info = f"맵 에디터 ON  |  현재 레이어: {edit_layer}  |  F2: 종료"
            info_img = font.render(info, True, (250, 240, 180))
            screen.blit(info_img, (10, SCREEN_H - 28))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
