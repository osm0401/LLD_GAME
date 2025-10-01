# game/player.py
# -----------------------------------------
# 256x256 스프라이트 시트(4열 x 4행) + 스케일 + 클릭 링
# 행: 0=down, 1=up, 2=left, 3=right
# 열: 0=idle, 1~3=walk
# -----------------------------------------
import pygame, math
from config import PLAYER_SPEED, RING_START_RADIUS, RING_DURATION

class Player:
    def __init__(
        self,
        start_pos,
        sprite_path="assets/character.png",
        tile=256,            # ← 프레임 크기 256
        scale=1.5,           # ← 배율 (원본 256px이 크니 1~2 사이로 조절 추천)
        cols=4,              # ← 가로 4칸
        rows=4,              # ← 세로 4칸
        margin=(0, 0),       # 여백 없음
        spacing=(0, 0),      # 간격 없음
    ):
        # --- 위치/이동 ---
        self.tile = tile
        self.scale = scale
        self.draw_w = int(tile * scale)
        self.draw_h = int(tile * scale)

        self.pos_x, self.pos_y = float(start_pos[0]), float(start_pos[1])
        self.speed = PLAYER_SPEED
        self.target = None

        # --- 스프라이트 시트 로드/슬라이스 ---
        self.sheet = pygame.image.load(sprite_path).convert_alpha()
        self.frames = self._slice_sheet_with_spacing(self.sheet, tile, tile, cols, rows, margin, spacing)

        # 스케일
        self.frames_scaled = [
            [pygame.transform.scale(frame, (self.draw_w, self.draw_h)) for frame in row]
            for row in self.frames
        ]

        # 방향 매핑
        self.frames_by_dir = {
            "down":  self.frames_scaled[0],
            "up":    self.frames_scaled[1],
            "left":  self.frames_scaled[2],
            "right": self.frames_scaled[3],
        }

        # --- 애니메이션 ---
        self.direction = "down"
        self.anim_index = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.12  # 초

        # --- 클릭 링 ---
        self._rings = []
        self._ring_start_radius = RING_START_RADIUS
        self._ring_duration = RING_DURATION

    # ===== 스프라이트 시트 자르기 =====
    def _slice_sheet_with_spacing(self, sheet, w, h, cols, rows, margin, spacing):
        mx, my = margin
        sx, sy = spacing
        out = []
        for r in range(rows):
            row_frames = []
            for c in range(cols):
                x = mx + c * (w + sx)
                y = my + r * (h + sy)
                rect = pygame.Rect(x, y, w, h)
                row_frames.append(sheet.subsurface(rect))
            out.append(row_frames)
        return out

    # ===== 이동 =====
    def set_target(self, pos):
        self.target = (float(pos[0] - self.draw_w / 2), float(pos[1] - self.draw_h / 2))

    def update(self, dt: float):
        if self.target is None:
            self.anim_index = 0
            self.anim_timer = 0.0
            return

        dx = self.target[0] - self.pos_x
        dy = self.target[1] - self.pos_y
        dist = math.hypot(dx, dy)

        if dist <= 1e-3:
            self.pos_x, self.pos_y = self.target
            self.target = None
            self.anim_index = 0
            self.anim_timer = 0.0
            return

        step = self.speed * dt
        if step >= dist:
            self.pos_x, self.pos_y = self.target
            self.target = None
            self.anim_index = 0
            self.anim_timer = 0.0
        else:
            ux, uy = dx / dist, dy / dist
            self.pos_x += ux * step
            self.pos_y += uy * step

            # 방향 판별
            if abs(dx) > abs(dy):
                self.direction = "right" if dx > 0 else "left"
            else:
                self.direction = "down" if dy > 0 else "up"

            # 걷기 애니메이션
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0.0
                self.anim_index = 1 + ((self.anim_index - 1) % 3)

    def draw(self, surface: pygame.Surface):
        row = self.frames_by_dir[self.direction]
        col = self.anim_index if self.target is not None else 0
        frame = row[col]
        surface.blit(frame, (int(self.pos_x), int(self.pos_y)))

    # ===== 클릭 링 =====
    def spawn_click_ring(self, x, y):
        self._rings.append((x, y, pygame.time.get_ticks()))

    def update_and_draw_click_rings(self, surface: pygame.Surface):
        now = pygame.time.get_ticks()
        new_rings = []
        start_radius = self._ring_start_radius
        duration = self._ring_duration

        for (cx, cy, st) in self._rings:
            elapsed = (now - st) / 1000.0
            if elapsed < duration:
                ratio = 1 - elapsed / duration
                radius = max(1, int(start_radius * ratio))
                alpha = int(255 * ratio)
                ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (120, 200, 255, alpha), (radius, radius), width=2)
                surface.blit(ring_surf, (cx - radius, cy - radius))
                new_rings.append((cx, cy, st))
        self._rings = new_rings
