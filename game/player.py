# game/player.py
# -----------------------------------------
# 플레이어(노란 사각형) + 우클릭 원 이펙트 통합
# - 우클릭 원(점점 줄어들며 페이드) 로직을 Player 내부로 이동
# -----------------------------------------
import pygame, math
from config import PLAYER_SIZE, PLAYER_SPEED, RING_START_RADIUS, RING_DURATION

class Player:
    def __init__(self, start_pos):
        # --- 이동 관련 ---
        self.size = PLAYER_SIZE
        self.pos_x, self.pos_y = float(start_pos[0]), float(start_pos[1])
        self.speed = PLAYER_SPEED
        self.target = None

        # --- 클릭 링 이펙트(내장) ---
        # (x, y, 생성시각_ms) 튜플을 보관
        self._rings = []
        self._ring_start_radius = RING_START_RADIUS
        self._ring_duration = RING_DURATION

    # ---------------- 이동 ----------------
    def set_target(self, pos):
        """우클릭 좌표를 목표로 설정(중앙 정렬)"""
        self.target = (float(pos[0] - self.size / 2), float(pos[1] - self.size / 2))

    def update(self, dt):
        """목표 지점으로 선형 이동"""
        if self.target is None:
            return
        dx = self.target[0] - self.pos_x
        dy = self.target[1] - self.pos_y
        dist = math.hypot(dx, dy)

        if dist <= 1e-3:
            self.pos_x, self.pos_y = self.target
            self.target = None
            return

        step = self.speed * dt
        if step >= dist:
            self.pos_x, self.pos_y = self.target
            self.target = None
        else:
            ux, uy = dx / dist, dy / dist
            self.pos_x += ux * step
            self.pos_y += uy * step

    def draw(self, surface):
        """플레이어(노란 사각형)"""
        pygame.draw.rect(surface, (255, 200, 60),
                         (int(self.pos_x), int(self.pos_y), self.size, self.size))

    # ------------- 클릭 링 이펙트 -------------
    def spawn_click_ring(self, x, y):
        """우클릭 시 호출: 해당 위치에 링 이펙트 생성"""
        self._rings.append((x, y, pygame.time.get_ticks()))

    def update_and_draw_click_rings(self, surface):
        """링 이펙트 업데이트 + 그리기(0.5초 동안 축소 + 페이드)"""
        now = pygame.time.get_ticks()
        new_rings = []
        start_radius = self._ring_start_radius
        duration = self._ring_duration

        for (cx, cy, st) in self._rings:
            elapsed = (now - st) / 1000.0
            if elapsed < duration:
                ratio = 1 - elapsed / duration            # 1→0
                radius = max(1, int(start_radius * ratio))
                alpha = int(255 * ratio)

                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (120, 200, 255, alpha),
                                   (radius, radius), radius, width=2)
                surface.blit(surf, (cx - radius, cy - radius))
                new_rings.append((cx, cy, st))

        self._rings = new_rings
