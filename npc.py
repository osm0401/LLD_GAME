# npc.py — 사이드뷰 NPC (방문 횟수별 대사 세트 지원)

import os
import pygame
from pygame.math import Vector2 as V2
from settings import FONT_NAME

def _sysfont(name, size):
    try:
        return pygame.font.SysFont(name, size)
    except Exception:
        return pygame.font.SysFont(None, size)

def _wrap_text(text, font, max_w):
    """아주 단순한 줄바꿈: 공백 기준으로 끊어서 max_w 안에 맞춤."""
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class NPC:
    """
    사용법 1) lines_by_visit=[[...],[...],[...]]
        - 첫 대화(visit=1)는 0번째 세트, 두 번째(visit=2)는 1번째 세트...
        - visit이 세트 수를 넘으면 마지막 세트를 반복 사용

    사용법 2) lines=[...]  (예전 호환)
        - 매 대화 때마다 동일한 세트를 사용
    """

    def __init__(self, name: str, world_x: int, level,
                 lines=None,                   # 예전 방식: 한 세트 대사
                 lines_by_visit=None,          # 새 방식: 방문 횟수별 대사 세트(리스트 혹은 {int:[...]} 딕셔너리)
                 sprite_path="assets/sprites/npc_side.png"):

        self.name = name
        self.w, self.h = 32, 56

        # 바닥이나 지형지물 위에 서게 하기
        if hasattr(level, "get_support_y"):
            base_y = level.get_support_y(world_x)  # 발바닥이 닿을 y (바닥 or 오브젝트 위)
        else:
            base_y = level.surface_y_rect_x(world_x)

        y_top = base_y - self.h
        self.pos = V2(world_x, y_top)

        # 대화 데이터
        self.lines = list(lines) if lines else [
            "안녕, 여행자. 바람이 고요하네.",
            "엘테리아로 가려면 다리를 따라 서쪽으로.",
            "돈의 흐름이 변하면 세상도 변하지.",
        ]
        self.lines_by_visit = lines_by_visit  # list[list[str]] 또는 dict[int, list[str]]
        self.active_lines: list[str] = []     # 이번 대화에 사용할 세트

        # 상태
        self.talk_active = False
        self._idx = 0
        self.range = 90  # 상호작용 범위(px)
        self.visit_count = 0  # ← 대화 시작(열림) 횟수

        # 폰트
        self.font = _sysfont(FONT_NAME, 18)
        self.big  = _sysfont(FONT_NAME, 22)

        # 스프라이트
        self.sprite = None
        if os.path.exists(sprite_path):
            try:
                img = pygame.image.load(sprite_path).convert_alpha()
                self.sprite = pygame.transform.smoothscale(img, (self.w, self.h))
            except Exception:
                self.sprite = None

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x), int(self.pos.y), self.w, self.h)

    # ---- 내부 유틸 ----
    def _select_lines_for_visit(self, visit: int) -> list[str]:
        """방문 횟수에 맞는 대사 세트를 결정."""
        # dict 지원: 정확히 visit 키가 있으면 사용, 없으면 가장 큰 키 이하 중 최대, 그래도 없으면 마지막 수단으로 self.lines
        if isinstance(self.lines_by_visit, dict):
            if visit in self.lines_by_visit:
                return list(self.lines_by_visit[visit])
            # visit보다 작은 키 중 최대를 찾기
            candidates = [k for k in self.lines_by_visit.keys() if isinstance(k, int) and k <= visit]
            if candidates:
                return list(self.lines_by_visit[max(candidates)])
        # list 지원: 인덱스 기반, 초과하면 마지막 세트 재사용
        if isinstance(self.lines_by_visit, list) and self.lines_by_visit:
            idx = min(max(visit - 1, 0), len(self.lines_by_visit) - 1)
            return list(self.lines_by_visit[idx])
        # fallback
        return list(self.lines)

    def _start_conversation(self):
        """대화를 시작하며 방문 카운트를 올리고 세트를 고른다."""
        self.visit_count += 1
        self.active_lines = self._select_lines_for_visit(self.visit_count)
        if not self.active_lines:
            self.active_lines = ["..."]
        self._idx = 0
        self.talk_active = True

    # ---- 입력/상태 ----
    def update(self, player_rect: pygame.Rect, events) -> bool:
        near = abs(player_rect.centerx - self.rect.centerx) <= self.range
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE and near:
                if not self.talk_active:
                    self._start_conversation()
                else:
                    self._idx += 1
                    if self._idx >= len(self.active_lines):
                        self.talk_active = False
        return near

    # ---- 그리기 ----
    def draw(self, surf: pygame.Surface, camera_x: float):
        sx = int(self.pos.x - camera_x)
        sy = int(self.pos.y)

        # 본체
        if self.sprite:
            surf.blit(self.sprite, (sx, sy))
        else:
            body = pygame.Rect(sx, sy, self.w, self.h)
            pygame.draw.rect(surf, (210, 120, 120), body, border_radius=6)
            # 모자/망토 느낌
            pygame.draw.polygon(surf, (80, 40, 40),
                                [(sx-4, sy+12), (sx+self.w//2, sy-6), (sx+self.w+4, sy+12)])
            pygame.draw.rect(surf, (120, 60, 60), (sx+4, sy+18, self.w-8, self.h-22), border_radius=4)

        # 이름 라벨
        name_img = self.big.render(self.name, True, (40, 30, 35))
        name_box = pygame.Surface((name_img.get_width()+10, name_img.get_height()+4), pygame.SRCALPHA)
        name_box.fill((255, 255, 255, 160))
        nbx = sx + self.w//2 - name_box.get_width()//2
        nby = sy - name_box.get_height() - 6
        surf.blit(name_box, (nbx, nby))
        surf.blit(name_img, (nbx+5, nby+2))

    def draw_dialog(self, surf: pygame.Surface, camera_x: float, near: bool,
                    screen_w: int, screen_h: int):
        # 힌트
        if near and not self.talk_active:
            hint = self.font.render("SPACE: 대화하기", True, (30, 30, 40))
            box = pygame.Surface((hint.get_width()+10, hint.get_height()+6), pygame.SRCALPHA)
            box.fill((255, 255, 255, 180))
            sx = int(self.rect.centerx - camera_x) - box.get_width()//2
            sy = self.rect.top - 70
            surf.blit(box, (sx, sy))
            surf.blit(hint, (sx+5, sy+6))
            return

        if not self.talk_active:
            return

        box_h = 150
        panel = pygame.Surface((screen_w, box_h), pygame.SRCALPHA)
        panel.fill((18, 20, 24, 235))
        surf.blit(panel, (0, screen_h - box_h))

        # 이름 + (n번째 방문) 뱃지
        title = f"{self.name}  ·  {self.visit_count}번째 만남"
        name_img = self.big.render(title, True, (250, 230, 170))
        surf.blit(name_img, (16, screen_h - box_h + 12))

        # 본문
        text = self.active_lines[min(self._idx, len(self.active_lines)-1)]
        x0, y0 = 16, screen_h - box_h + 48
        max_w = screen_w - 32
        for i, ln in enumerate(_wrap_text(text, self.font, max_w)):
            line_img = self.font.render(ln, True, (235, 235, 240))
            surf.blit(line_img, (x0, y0 + i*22))

        # 힌트
        hint = self.font.render("SPACE: 다음  |  마지막에서 닫힘", True, (200, 200, 210))
        surf.blit(hint, (screen_w - hint.get_width() - 12, screen_h - hint.get_height() - 10))
