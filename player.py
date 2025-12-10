# player.py
import pygame
from pygame.math import Vector2 as V2
import settings as S


class Player:
    """
    mode:
      - "side"    : 기존 사이드뷰 (A/D)
      - "topdown" : 아이작식 탑다운 (WASD)
    """

    def __init__(self, start_pos):
        self.pos = V2(start_pos)
        self.vel = V2(0, 0)

        self.w, self.h = getattr(S, "PLAYER_SIZE", (32, 56))
        self.facing = 1

        self.mode = "side"
        self.top_speed = getattr(S, "TOPDOWN_SPEED", 220)

        self.accel = getattr(S, "PLAYER_ACCEL", 1200)
        self.friction = getattr(S, "PLAYER_FRICTION", 1600)
        self.max_speed = getattr(S, "PLAYER_MAX_SPEED", 260)

        # ✅ 플레이어 사진/스프라이트 로드
        self.sprite = None

        sprite_path = getattr(S, "PLAYER_SPRITE", None)
        if sprite_path:
            try:
                print("[player] player.png 로드 완료")
                img = pygame.image.load(sprite_path).convert_alpha()
                self.sprite = pygame.transform.smoothscale(img, (self.w, self.h))
            except Exception:
                self.sprite = None

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x), int(self.pos.y), self.w, self.h)

    # ---------------------------------------------------------
    # 탑다운 충돌 이동(축 분리)
    # ---------------------------------------------------------
    def _move_axis(self, dx, dy, solids):
        if dx:
            self.pos.x += dx
            r = self.rect
            for s in solids:
                if r.colliderect(s):
                    if dx > 0:
                        self.pos.x = s.left - self.w
                    else:
                        self.pos.x = s.right
                    r = self.rect

        if dy:
            self.pos.y += dy
            r = self.rect
            for s in solids:
                if r.colliderect(s):
                    if dy > 0:
                        self.pos.y = s.top - self.h
                    else:
                        self.pos.y = s.bottom
                    r = self.rect

    def update(self, dt, keys, level):
        # =====================================================
        # 1) ✅ 탑다운 모드
        # =====================================================
        if self.mode == "topdown":
            solids = level.get_solid_rects() if hasattr(level, "get_solid_rects") else []

            mx = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)
            my = (1 if keys[pygame.K_s] else 0) - (1 if keys[pygame.K_w] else 0)

            move = V2(mx, my)
            if move.length_squared() > 0:
                move = move.normalize()

            dx = move.x * self.top_speed * dt
            dy = move.y * self.top_speed * dt

            self._move_axis(dx, 0, solids)
            self._move_axis(0, dy, solids)

            ww = getattr(level, "world_w", S.SCREEN_W)
            wh = getattr(level, "world_h", S.SCREEN_H)
            self.pos.x = max(0, min(ww - self.w, self.pos.x))
            self.pos.y = max(0, min(wh - self.h, self.pos.y))

            if mx:
                self.facing = 1 if mx > 0 else -1
            return

        # =====================================================
        # 2) 기존 사이드 모드
        # =====================================================
        move = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)

        if move:
            self.vel.x += move * self.accel * dt
            self.facing = 1 if move > 0 else -1
        else:
            if self.vel.x > 0:
                self.vel.x = max(0, self.vel.x - self.friction * dt)
            elif self.vel.x < 0:
                self.vel.x = min(0, self.vel.x + self.friction * dt)

        self.vel.x = max(-self.max_speed, min(self.max_speed, self.vel.x))

        old_x = self.pos.x
        self.pos.x += self.vel.x * dt

        ww = getattr(level, "world_w", S.SCREEN_W)
        self.pos.x = max(0, min(ww - self.w, self.pos.x))

        solids = level.get_solid_rects() if hasattr(level, "get_solid_rects") else []
        r = self.rect
        for s in solids:
            if r.colliderect(s):
                if self.pos.x > old_x:
                    self.pos.x = s.left - self.w
                elif self.pos.x < old_x:
                    self.pos.x = s.right
                self.vel.x = 0
                r = self.rect

        if hasattr(level, "surface_y"):
            self.pos.y = level.surface_y(self.rect)

    def draw(self, surf, camera_x=0.0, camera_y=0.0):
        x = int(self.pos.x - camera_x)
        y = int(self.pos.y - camera_y)

        # ✅ 사진이 있으면 사진으로 렌더
        if self.sprite:
            img = self.sprite
            if self.facing < 0:
                img = pygame.transform.flip(img, True, False)
            surf.blit(img, (x, y))
            return

        # 폴백(기존 사각형)
        body = pygame.Rect(x, y, self.w, self.h)
        pygame.draw.rect(surf, (120, 160, 255), body, border_radius=6)

        eye_x = body.centerx + self.facing * (self.w // 4)
        pygame.draw.line(surf, (30, 40, 60),
                         (eye_x, body.centery - 6),
                         (eye_x, body.centery + 6), 2)
