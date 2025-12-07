# player.py
# ---------------------------------------------------------
# 사이드뷰 플레이어(점프 없음).
#
# 성능/구조 원칙:
# 1) 매 프레임 새 객체 생성 최소화
# 2) 충돌은 "수평만" 단순 처리
# 3) y는 레벨이 정한 지원면(surface)로 고정
# ---------------------------------------------------------

import pygame
from pygame.math import Vector2 as V2
import settings as S


class Player:
    def __init__(self, start_pos):
        self.pos = V2(start_pos)
        self.vel = V2(0, 0)

        self.w, self.h = S.PLAYER_SIZE
        self.facing = 1

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x), int(self.pos.y), self.w, self.h)

    def update(self, dt, keys, level):
        # -------------------------
        # 1) 입력 → 목표 방향
        # -------------------------
        move = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)

        # -------------------------
        # 2) 가속/마찰
        # -------------------------
        if move:
            self.vel.x += move * S.PLAYER_ACCEL * dt
            self.facing = 1 if move > 0 else -1
        else:
            if self.vel.x > 0:
                self.vel.x = max(0, self.vel.x - S.PLAYER_FRICTION * dt)
            elif self.vel.x < 0:
                self.vel.x = min(0, self.vel.x + S.PLAYER_FRICTION * dt)

        # 속도 제한
        self.vel.x = max(-S.PLAYER_MAX_SPEED, min(S.PLAYER_MAX_SPEED, self.vel.x))

        # -------------------------
        # 3) 수평 이동 + 충돌
        # -------------------------
        old_x = self.pos.x
        self.pos.x += self.vel.x * dt

        # 월드 범위
        self.pos.x = max(0, min(level.world_w - self.w, self.pos.x))

        # 충돌 검사
        r = self.rect
        for srect in level.get_solid_rects():
            if r.colliderect(srect):
                # 오른쪽으로 가다 박았으면 벽 왼쪽에 붙임
                if self.pos.x > old_x:
                    self.pos.x = srect.left - self.w
                # 왼쪽으로 가다 박았으면 벽 오른쪽에 붙임
                elif self.pos.x < old_x:
                    self.pos.x = srect.right
                self.vel.x = 0
                r = self.rect  # 보정 후 rect 갱신

        # -------------------------
        # 4) y는 "지면" 기준으로 고정
        # -------------------------
        self.pos.y = level.surface_y(self.rect)

    def draw(self, surf, camera_x: float):
        # 스프라이트 미적용 → 임시 사각형
        x = int(self.pos.x - camera_x)
        y = int(self.pos.y)
        body = pygame.Rect(x, y, self.w, self.h)
        pygame.draw.rect(surf, (120, 160, 255), body, border_radius=6)

        # 얼굴 방향 표시(가벼운 디버그)
        eye_x = body.centerx + self.facing * (self.w // 4)
        pygame.draw.line(surf, (30, 40, 60), (eye_x, body.centery - 6), (eye_x, body.centery + 6), 2)
