# player.py
import pygame
from pygame.math import Vector2 as V2
import settings as S
import pygame
from pygame.math import Vector2 as V2
import settings as S
import key as K   # ✅ 추가


class Player:
    """
    mode:
      - "side"    : 사이드뷰 (A/D + 점프)
      - "topdown" : 아이작식 탑다운 (WASD)
    """

    def __init__(self, start_pos):
        self.pos = V2(start_pos)
        self.vel = V2(0, 0)

        self.w, self.h = getattr(S, "PLAYER_SIZE", (36, 60))
        self.facing = 1  # 1: 오른쪽, -1: 왼쪽

        # 기본 모드
        self.mode = "side"

        # 탑다운 이동 속도
        self.top_speed = getattr(S, "TOPDOWN_SPEED", 220)

        # 사이드뷰 수평 이동 파라미터
        self.accel = getattr(S, "PLAYER_ACCEL", 1200)
        self.friction = getattr(S, "PLAYER_FRICTION", 1600)
        self.max_speed = getattr(S, "PLAYER_MAX_SPEED", 260)

        # 사이드뷰 점프/중력
        self.gravity = getattr(S, "PLAYER_GRAVITY", 2000)       # 아래로 당기는 힘
        self.jump_speed = getattr(S, "PLAYER_JUMP_SPEED", 750)  # 점프 초기 속도
        self.on_ground = False                                  # 바닥 접지 여부

        # 플레이어 사진/스프라이트
        self.sprite = None
        sprite_path = getattr(S, "PLAYER_SPRITE", None)
        if sprite_path:
            try:
                img = pygame.image.load(sprite_path).convert_alpha()
                self.sprite = pygame.transform.smoothscale(img, (self.w, self.h))
            except Exception:
                self.sprite = None

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x), int(self.pos.y), self.w, self.h)

    # ---------------------------------------------------------
    # 탑다운 충돌 이동(축 분리) - 기존 그대로 사용
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

    # ---------------------------------------------------------
    # 업데이트
    # ---------------------------------------------------------
    def update(self, dt, keys, level):
        # =====================================================
        # 1) 탑다운 모드 (아이작식)
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

            # 월드 클램프
            ww = getattr(level, "world_w", S.SCREEN_W)
            wh = getattr(level, "world_h", S.SCREEN_H)
            self.pos.x = max(0, min(ww - self.w, self.pos.x))
            self.pos.y = max(0, min(wh - self.h, self.pos.y))

            if mx:
                self.facing = 1 if mx > 0 else -1
            return

        # =====================================================
        # 2) 사이드뷰 모드 (A/D + 점프)
        # =====================================================
        solids = level.get_solid_rects() if hasattr(level, "get_solid_rects") else []

        # --- 수평 이동(A/D) ---
        move = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)

        if move:
            self.vel.x += move * self.accel * dt
            self.facing = 1 if move > 0 else -1
        else:
            # 마찰
            if self.vel.x > 0:
                self.vel.x = max(0, self.vel.x - self.friction * dt)
            elif self.vel.x < 0:
                self.vel.x = min(0, self.vel.x + self.friction * dt)

        # 수평 속도 제한
        self.vel.x = max(-self.max_speed, min(self.max_speed, self.vel.x))

        # --- 점프 입력 (key.JUMP → 지금은 SPACE 랑 W) ---
        jump_pressed_space = keys[K.JUMP_SPACE]
        jump_pressed_w = keys[K.JUMP_W]
        if (jump_pressed_space or jump_pressed_w) and self.on_ground:
            self.vel.y = -self.jump_speed
            self.on_ground = False

        # --- 중력 ---
        self.vel.y += self.gravity * dt

        # --- 수평 이동 + 충돌 ---
        old_x = self.pos.x
        self.pos.x += self.vel.x * dt

        ww = getattr(level, "world_w", S.SCREEN_W)
        self.pos.x = max(0, min(ww - self.w, self.pos.x))

        r = self.rect
        for s in solids:
            if r.colliderect(s):
                if self.pos.x > old_x:
                    self.pos.x = s.left - self.w
                elif self.pos.x < old_x:
                    self.pos.x = s.right
                self.vel.x = 0
                r = self.rect

        # --- 수직 이동 + 충돌 ---
        self.on_ground = False  # 일단 공중으로 보고, 바닥/벽과 닿으면 True로 세팅
        old_y = self.pos.y
        self.pos.y += self.vel.y * dt
        r = self.rect

        # 블록들과 수직 충돌
        for s in solids:
            if r.colliderect(s):
                if self.vel.y > 0:  # 아래로 떨어지는 중(바닥 충돌)
                    self.pos.y = s.top - self.h
                    self.vel.y = 0
                    self.on_ground = True
                elif self.vel.y < 0:  # 위로 점프 중(천장 충돌)
                    self.pos.y = s.bottom
                    self.vel.y = 0
                r = self.rect

        # --- 레벨에서 제공하는 바닥(suface_y) 기준 스냅(플랫 지면용) ---
        if hasattr(level, "surface_y"):
            ground_top = level.surface_y(self.rect)  # 플레이어 rect의 y(위쪽) 기준 위치
            if self.pos.y > ground_top:             # 지면보다 더 내려가면 바닥에 붙이기
                self.pos.y = ground_top
                self.vel.y = 0
                self.on_ground = True

        # --- 세로 월드 클램프 (혹시 모를 아래로 추락 대비) ---
        wh = getattr(level, "world_h", S.SCREEN_H)
        if self.pos.y + self.h > wh:
            self.pos.y = wh - self.h
            self.vel.y = 0
            self.on_ground = True
        if self.pos.y < 0:
            self.pos.y = 0
            if self.vel.y < 0:
                self.vel.y = 0

    # ---------------------------------------------------------
    # 그리기
    # ---------------------------------------------------------
    def draw(self, surf, camera_x=0.0, camera_y=0.0):
        x = int(self.pos.x - camera_x)
        y = int(self.pos.y - camera_y)

        # 스프라이트가 있으면 사진으로 그리기
        if self.sprite:
            img = self.sprite
            if self.facing < 0:
                img = pygame.transform.flip(img, True, False)
            surf.blit(img, (x, y))
            return

        # 스프라이트 없으면 기본 박스 렌더
        body = pygame.Rect(x, y, self.w, self.h)
        pygame.draw.rect(surf, (120, 160, 255), body, border_radius=6)

        eye_x = body.centerx + self.facing * (self.w // 4)
        pygame.draw.line(
            surf,
            (30, 40, 60),
            (eye_x, body.centery - 6),
            (eye_x, body.centery + 6),
            2,
        )
