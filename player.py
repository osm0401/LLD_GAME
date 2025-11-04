# player.py
import pygame
from pygame.math import Vector2 as V2
from settings import *

class Player:
    """
    3행 × 3열 구조 스프라이트 시트 (앞/옆/뒤 3컷씩)
    자동으로 좌/우 반전, 부족한 프레임은 채워서 4프레임 애니메이션 생성
    """
    def __init__(self, world_pos: V2,
                 spritesheet_path="assets/sprites/player_sheet.png"):
        self.world_pos = V2(world_pos)
        self.direction = "down"
        self.anim_timer = 0.0
        self.anim_speed = 0.12
        self.anim_frame = 0
        self.moving = False

        # 4방향 프레임 저장
        self.frames = {"down": [], "left": [], "right": [], "up": []}

        self._load_sheet(spritesheet_path)

        # 🔽 화면에 표시할 크기 (작게!)
        self.draw_size = (32, 42)  # 추천 크기, 필요하면 조절 가능

    def _load_sheet(self, path: str):
        try:
            sheet = pygame.image.load(path).convert_alpha()
            # 혹시 흰색 잔여 있으면 이 줄 활성화
            # sheet.set_colorkey((255, 255, 255))
        except Exception as e:
            print("[Player] spritesheet load failed:", e)
            tmp = pygame.Surface((48, 48), pygame.SRCALPHA)
            tmp.fill((255, 0, 255, 180))
            for k in self.frames:
                self.frames[k] = [tmp.copy()]
            return

        # 시트 크기 분석
        sheet_w, sheet_h = sheet.get_size()
        cols, rows = 3, 3
        frame_w, frame_h = sheet_w // cols, sheet_h // rows

        # 아래 순서로 자르기
        down, right, up = [], [], []

        # 1행: down
        for c in range(cols):
            surf = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            surf.blit(sheet, (0, 0), pygame.Rect(c * frame_w, 0, frame_w, frame_h))
            down.append(surf)

        # 2행: right
        for c in range(cols):
            surf = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            surf.blit(sheet, (0, 0), pygame.Rect(c * frame_w, frame_h, frame_w, frame_h))
            right.append(surf)

        # 3행: up
        for c in range(cols):
            surf = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            surf.blit(sheet, (0, 0), pygame.Rect(c * frame_w, frame_h * 2, frame_w, frame_h))
            up.append(surf)

        # 방향별 프레임 구성
        self.frames["down"] = self._pad_to_4(down)
        self.frames["left"] = self._pad_to_4(right)  # ← 오른쪽 프레임을 그대로 왼쪽으로
        self.frames["right"] = self._pad_to_4([pygame.transform.flip(f, True, False) for f in right])  # ← 반대로 뒤집기
        self.frames["up"] = self._pad_to_4(up)

    def _pad_to_4(self, frames):
        """3프레임밖에 없으면 4프레임으로 채워서 리턴"""
        if len(frames) >= 4:
            return frames[:4]
        if len(frames) == 3:
            return [frames[0], frames[1], frames[2], frames[1]]
        if len(frames) == 2:
            return [frames[0], frames[1], frames[0], frames[1]]
        if len(frames) == 1:
            return [frames[0]] * 4
        empty = pygame.Surface((48, 48), pygame.SRCALPHA)
        return [empty] * 4

    def set_direction_from_vec(self, vec: V2):
        if abs(vec.x) > abs(vec.y):
            self.direction = "right" if vec.x > 0 else "left"
        else:
            self.direction = "down" if vec.y > 0 else "up"

    def update_anim(self, dt: float):
        if not self.moving:
            self.anim_frame = 0
            return
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 4

    def draw(self, surf: pygame.Surface, camera_offset: V2):
        frames = self.frames[self.direction]
        frame = frames[self.anim_frame]

        # 🔽 스케일 적용 (너무 클 때 줄이기)
        if self.draw_size is not None:
            frame = pygame.transform.smoothscale(frame, self.draw_size)

        # 🔽 캐릭터를 중앙보다 살짝 아래로 위치시킴 (+10)
        rect = frame.get_rect(center=(CENTER.x, CENTER.y + 10))
        surf.blit(frame, rect)
