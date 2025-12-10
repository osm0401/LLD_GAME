# npc.py — 사이드뷰 + 탑다운 공용 NPC
# - SPACE로 대화
# - 근처에 있을 때만 대화 가능(2D 거리)
# - draw_dialog는 camera_y, topdown 옵션까지 지원해서
#   main.py 의 두 가지 호출 모두 정상 작동

import os
import random
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
    사용법 1) 기본
        npc = NPC("워니", 1400, level)
        → 기본 대사 3줄 사용

    사용법 2) 방문 횟수별 대사
        npc = NPC("워니", 1400, level, lines_by_visit=[
            ["첫 방문 1", "첫 방문 2"],
            ["두 번째 방문 1", ...],
            ["세 번째 방문 ..."],
            ["네 번째 방문 ..."],
        ])

        # ✔ 5번 이상 방문하면 3~4번 세트 중 랜덤 선택
        visit >= 5 이고 lines_by_visit 길이가 4 이상이면,
        3번째(index 2)와 4번째(index 3) 세트 중 하나를 랜덤으로 사용.
    """

    def __init__(
        self,
        name: str,
        world_x: int,
        level,
        lines=None,          # 예전 방식: 한 세트 대사
        lines_by_visit=None, # 새 방식: 방문 횟수별 대사 세트(list or dict)
        sprite_path="assets/sprites/npc_side.png",
    ):
        self.name = name
        self.w, self.h = 32, 56

        # 바닥/지형지물 위에 서게 함
        if hasattr(level, "get_support_y"):
            base_y = level.get_support_y(world_x)
        else:
            base_y = level.surface_y_rect_x(world_x)
        y_top = base_y - self.h
        self.pos = V2(world_x, y_top)

        # 대사 데이터
        self.lines = list(lines) if lines else [
            "안녕, 여행자. 바람이 고요하네.",
            "엘테리아로 가려면 다리를 따라 서쪽으로.",
            "돈의 흐름이 변하면 세상도 변하지.",
        ]
        self.lines_by_visit = lines_by_visit  # list[list[str]] 또는 dict[int, list[str]]
        self.active_lines: list[str] = []     # 이번 대화에서 사용할 세트

        # 상태
        self.talk_active = False
        self._idx = 0               # 현재 줄 인덱스
        self.range = 90             # 상호작용 범위(px)
        self.visit_count = 0        # 대화를 "시작"한 횟수(열릴 때 +1)

        # 폰트
        self.font = _sysfont(FONT_NAME, 18)
        self.big = _sysfont(FONT_NAME, 22)

        # 스프라이트
        self.sprite = None
        if os.path.exists(sprite_path):
            try:
                img = pygame.image.load(sprite_path).convert_alpha()
                self.sprite = pygame.transform.smoothscale(img, (self.w, self.h))
            except Exception:
                self.sprite = None

    # -------------------------------------------------
    # 위치/충돌용 rect
    # -------------------------------------------------
    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x), int(self.pos.y), self.w, self.h)

    # -------------------------------------------------
    # 대사 세트 선택
    # -------------------------------------------------
    def _select_lines_for_visit(self, visit: int) -> list[str]:
        """
        방문 횟수에 따라 사용할 대사 리스트를 결정.

        - dict: visit 키가 있으면 해당 리스트 사용.
                없으면 visit보다 작은 키 중 최댓값 사용.
        - list: 인덱스 기반.
                visit-1이 범위를 벗어나면 마지막 인덱스 사용.
                ✔ visit >= 5 and len >= 4이면
                  index 2와 3 중 하나를 랜덤으로 사용 (3~4번 세트 랜덤).
        - 둘 다 없으면 self.lines 사용.
        """
        # dict 버전
        if isinstance(self.lines_by_visit, dict):
            if visit in self.lines_by_visit:
                return list(self.lines_by_visit[visit])
            candidates = [k for k in self.lines_by_visit.keys()
                          if isinstance(k, int) and k <= visit]
            if candidates:
                return list(self.lines_by_visit[max(candidates)])

        # list 버전
        if isinstance(self.lines_by_visit, list) and self.lines_by_visit:
            n = len(self.lines_by_visit)

            # ✅ 5 이상일 때 3~4번 세트 중 랜덤 (index 2 or 3)
            if visit >= 5 and n >= 4:
                idx = random.choice([2, 3])
                return list(self.lines_by_visit[idx])

            # 그 외는 기본 인덱스 로직
            idx = min(max(visit - 1, 0), n - 1)
            return list(self.lines_by_visit[idx])

        # fallback: 항상 동일 세트
        return list(self.lines)

    def _start_conversation(self):
        """SPACE를 처음 눌러 대화를 열 때 호출."""
        self.visit_count += 1
        self.active_lines = self._select_lines_for_visit(self.visit_count)
        if not self.active_lines:
            self.active_lines = ["..."]
        self._idx = 0
        self.talk_active = True

    # -------------------------------------------------
    # 상태 업데이트 (키 입력 포함)
    # -------------------------------------------------
    def update(self, player_rect: pygame.Rect, events) -> bool:
        """
        - 플레이어와의 거리 체크
        - SPACE 입력으로 대화 시작/다음 줄 진행
        - near: 플레이어가 대화 가능 거리 안에 있는지 여부 리턴
        """

        # ✅ 2D 거리(탑다운/사이드 공통)
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        near = (dx * dx + dy * dy) ** 0.5 <= self.range

        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE and near:
                if not self.talk_active:
                    self._start_conversation()
                else:
                    # 다음 줄로
                    self._idx += 1
                    if self._idx >= len(self.active_lines):
                        # 끝까지 봤으면 종료
                        self.talk_active = False

        return near

    # -------------------------------------------------
    # 본체 그리기 (월드→스크린 변환은 camera_x만 사용)
    # -------------------------------------------------
    def draw(self, surf: pygame.Surface, camera_x: float):
        sx = int(self.pos.x - camera_x)
        sy = int(self.pos.y)

        if self.sprite:
            surf.blit(self.sprite, (sx, sy))
        else:
            body = pygame.Rect(sx, sy, self.w, self.h)
            pygame.draw.rect(surf, (210, 120, 120), body, border_radius=6)
            pygame.draw.polygon(
                surf,
                (80, 40, 40),
                [(sx - 4, sy + 12),
                 (sx + self.w // 2, sy - 6),
                 (sx + self.w + 4, sy + 12)]
            )
            pygame.draw.rect(
                surf,
                (120, 60, 60),
                (sx + 4, sy + 18, self.w - 8, self.h - 22),
                border_radius=4,
            )

        # 이름 라벨
        name_img = self.big.render(self.name, True, (40, 30, 35))
        name_box = pygame.Surface(
            (name_img.get_width() + 10, name_img.get_height() + 4),
            pygame.SRCALPHA
        )
        name_box.fill((255, 255, 255, 160))
        nbx = sx + self.w // 2 - name_box.get_width() // 2
        nby = sy - name_box.get_height() - 6
        surf.blit(name_box, (nbx, nby))
        surf.blit(name_img, (nbx + 5, nby + 2))

    # -------------------------------------------------
    # 대화/힌트 UI
    # -------------------------------------------------
    def draw_dialog(
        self,
        surf: pygame.Surface,
        camera_x: float,
        near: bool,
        screen_w: int,
        screen_h: int,
        *,
        camera_y: float = 0.0,
        topdown: bool = False,
    ):
        """
        - near & not talk_active: "SPACE: 대화하기" 힌트
          * 사이드뷰: NPC 위에 표시
          * 탑다운: NPC 아래에 표시
        - talk_active: 화면 하단 대화 패널
        """

        # 1) 힌트
        if near and not self.talk_active:
            hint = self.font.render("SPACE: 대화하기", True, (30, 30, 40))
            box = pygame.Surface(
                (hint.get_width() + 10, hint.get_height() + 6),
                pygame.SRCALPHA,
            )
            box.fill((255, 255, 255, 180))

            sx = int(self.rect.centerx - camera_x) - box.get_width() // 2

            if topdown:
                # ✅ 탑다운: NPC 바로 아래
                sy = int(self.rect.bottom - camera_y) + 8
                if sy + box.get_height() > screen_h - 4:
                    sy = screen_h - box.get_height() - 4
            else:
                # ✅ 사이드뷰: 기존처럼 위쪽
                sy = int(self.rect.top - camera_y) - 70

            surf.blit(box, (sx, sy))
            surf.blit(hint, (sx + 5, sy + 3))
            return

        # 2) 대화 중이 아니면 끝
        if not self.talk_active:
            return

        # 3) 하단 대화 패널
        box_h = 150
        panel = pygame.Surface((screen_w, box_h), pygame.SRCALPHA)
        panel.fill((18, 20, 24, 235))
        surf.blit(panel, (0, screen_h - box_h))

        # 이름 + 방문 뱃지
        title = f"{self.name}  ·  {self.visit_count}번째 만남"
        name_img = self.big.render(title, True, (250, 230, 170))
        surf.blit(name_img, (16, screen_h - box_h + 12))

        # 본문 텍스트
        text = self.active_lines[min(self._idx, len(self.active_lines) - 1)]
        x0, y0 = 16, screen_h - box_h + 48
        max_w = screen_w - 32
        for i, ln in enumerate(_wrap_text(text, self.font, max_w)):
            line_img = self.font.render(ln, True, (235, 235, 240))
            surf.blit(line_img, (x0, y0 + i * 22))

        # 힌트 (다음/닫기)
        hint = self.font.render("SPACE: 다음  |  마지막에서 닫힘", True, (200, 200, 210))
        surf.blit(
            hint,
            (screen_w - hint.get_width() - 12, screen_h - hint.get_height() - 10),
        )
