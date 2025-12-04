# player.py — 사이드뷰 플레이어

import os
import pygame
from pygame.math import Vector2 as V2
from settings import PLAYER_SIZE, PLAYER_MAX_SPEED, PLAYER_ACCEL, PLAYER_FRICTION

class Player:
    def __init__(self, start_pos):
        self.pos = V2(start_pos)           # 월드 좌표(왼쪽 위)
        self.vel = V2(0, 0)
        self.w, self.h = PLAYER_SIZE
        self.facing = -1                  # 1:오른쪽, -1:왼쪽
        # 스프라이트 시도(없으면 색 박스)
        self.sprite = None
        self._try_load_sprite()


    def _try_load_sprite(self):
        # 사용자가 제공하면 씀: assets/sprites/player_side.png (투명 배경 권장)
        path = os.path.join("assets", "sprites", "player_side.png")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self.sprite = pygame.transform.smoothscale(img, (self.w, self.h))
            except Exception:
                self.sprite = None

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x), int(self.pos.y), self.w, self.h)

    def update(self, dt, keys, level):
        # ----------------------------
        # 1. 입력 처리 (좌우 이동)
        # ----------------------------
        move = 0
        if keys[pygame.K_a]:
            move -= 1
        if keys[pygame.K_d]:
            move += 1

        # 가속
        if move != 0:
            self.vel.x += move * PLAYER_ACCEL * dt
            self.facing = 1 if move > 0 else -1
        else:
            # 마찰로 감속
            if self.vel.x > 0:
                self.vel.x = max(0, self.vel.x - PLAYER_FRICTION * dt)
            elif self.vel.x < 0:
                self.vel.x = min(0, self.vel.x + PLAYER_FRICTION * dt)

        # 속도 제한
        if self.vel.x > PLAYER_MAX_SPEED:
            self.vel.x = PLAYER_MAX_SPEED
        if self.vel.x < -PLAYER_MAX_SPEED:
            self.vel.x = -PLAYER_MAX_SPEED

        # ----------------------------
        # 2. X 방향 이동 + 벽/지형지물 충돌
        # ----------------------------
        new_x = self.pos.x + self.vel.x * dt

        # 우선 월드 범위로 클램프
        new_x = max(0, min(level.world_w - self.w, new_x))

        # 임시 rect (이 위치로 갔을 때의 플레이어 사각형)
        test_rect = pygame.Rect(int(new_x), int(self.pos.y), self.w, self.h)

        # 레벨이 solid rect 정보를 제공하면 충돌 체크
        solid_rects = []
        if hasattr(level, "get_solid_rects"):
            solid_rects = level.get_solid_rects()

        for srect in solid_rects:
            if test_rect.colliderect(srect):
                # 오른쪽으로 이동 중 → 오른쪽 벽에 부딪힘
                if self.vel.x > 0:
                    new_x = srect.left - self.w
                # 왼쪽으로 이동 중 → 왼쪽 벽에 부딪힘
                elif self.vel.x < 0:
                    new_x = srect.right

                # 위치를 수정한 값으로 rect도 업데이트
                test_rect.x = int(new_x)

        # 실제 x 좌표 반영
        self.pos.x = new_x

        # ----------------------------
        # 3. Y 방향(바닥 위로 붙이기)
        # ----------------------------
        if hasattr(level, "surface_y"):
            # 레벨이 surface_y를 제공할 때
            self.pos.y = level.surface_y(self.rect)
        else:
            # 혹시 구버전 level.py와도 호환되게
            base_y = level.surface_y_rect_x(self.rect.centerx)
            self.pos.y = base_y - self.h

    def draw(self, surf, camera_x):
        screen_x = int(self.pos.x - camera_x)
        screen_y = int(self.pos.y)

        if self.sprite:
            img = self.sprite
            if self.facing < 0:
                img = pygame.transform.flip(img, True, False)
            surf.blit(img, (screen_x, screen_y))
        else:
            # 임시: 파란색 캐릭터 박스 + 얼굴 방향선
            body = pygame.Rect(screen_x, screen_y, self.w, self.h)
            pygame.draw.rect(surf, (120, 160, 255), body, border_radius=6)
            eye_x = body.centerx + (self.facing * (self.w//4))
            pygame.draw.line(surf, (30, 40, 60), (eye_x, body.centery-6), (eye_x, body.centery+6), 2)
