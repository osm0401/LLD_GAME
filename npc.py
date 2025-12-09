# npc.py
# ---------------------------------------------------------
# 사이드뷰 NPC + 방문횟수별 대사 + 선택지 지원.
#
# 핵심 기능
# 1) DIALOGUE_DB에서 npc_id로 대사 로드
# 2) 방문 1~4: 순서대로
# 3) 방문 5 이상: 3~4 세트 중 랜덤
# 4) 대사 노드가 dict면 선택지 처리
#    - {"text": "...", "choices":[{"label":"...", "next":[...]}]}
#
# 선택지 입력
# - 키보드 1~9
# - 마우스 클릭
#
# 주의
# - 선택지 렌더에서 만든 버튼 rect를
#   self._choice_rects에 저장해 update에서 클릭 판정
# ---------------------------------------------------------

import random
import pygame
from pygame.math import Vector2 as V2
import settings as S


def _sysfont(name, size):
    try:
        return pygame.font.SysFont(name, size)
    except Exception:
        return pygame.font.SysFont(None, size)


def _wrap_text(text, font, max_w):
    words = str(text).split(" ")
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


# ---------------------------------------------------------
# NPC 대사 DB
# ---------------------------------------------------------
DIALOGUE_DB = {
    "워니": {
        "lines_by_visit": [
            [
                "안녕 오늘도 하루가 시작됐네",
                "진짜 오늘도 일가고 내일도 일가고",
                {
                    "text": "주 100시간제가 도입된대…",
                    "choices": [
                        {"label": "헉… 괜찮아?", "next": ["괜찮진 않은데 버텨야지…"]},
                        {"label": "그만둬!", "next": ["그건… 현실적으로 쉽지 않다…"]},
                    ],
                },
            ],
            ["왜 뭐 할말 있어??"],
            ["음 이제 말 그만 걸어줄레??"],
            ["나 이제 일 가야해"],
        ]
    },

    "상미니": {
        "lines_by_visit": [
            ["원희야", "그림", "화이팅이다"],
            [
                {
                    "text": "퀄리티 기대 할께!",
                    "choices": [
                        {"label": "고마워!", "next": ["기대는 좋은 힘이지 ㅎㅎ"]},
                        {"label": "부담돼…", "next": ["부담 느끼지 말고 너 페이스로!"]},
                    ],
                }
            ],
            ["음 이제 말 그만 걸어줄레??"],
            ["아 좀 가라고;;"],
        ]
    },
}


class NPC:
    def __init__(self, npc_id: str, world_x: int, level, sprite_path=None):
        self.npc_id = npc_id
        self.name = npc_id
        self.w, self.h = 32, 56

        # 바닥/지형지물 위에 서기
        base_y = level.get_support_y(world_x)
        self.pos = V2(world_x, base_y - self.h)

        cfg = DIALOGUE_DB.get(npc_id, {})
        self.lines_by_visit = cfg.get("lines_by_visit", [["..."]])

        self.active_lines = []
        self.visit_count = 0
        self._idx = 0
        self.talk_active = False
        self.range = 90

        self.font = _sysfont(S.FONT_NAME, 18)
        self.big = _sysfont(S.FONT_NAME, 22)

        self.sprite = None
        if sprite_path:
            try:
                img = pygame.image.load(sprite_path).convert_alpha()
                self.sprite = pygame.transform.smoothscale(img, (self.w, self.h))
            except Exception:
                self.sprite = None

        # 선택지 버튼(rect, choice_dict) 저장용
        self._choice_rects = []

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x), int(self.pos.y), self.w, self.h)

    # ---------------------------
    # 방문 횟수별 세트 선택
    # ---------------------------
    def _select_lines_for_visit(self, visit: int):
        sets = self.lines_by_visit or [["..."]]

        # ✅ 5 이상일 때 3~4번 중 랜덤
        if visit >= 5 and len(sets) >= 4:
            return list(random.choice([sets[2], sets[3]]))

        idx = min(max(visit - 1, 0), len(sets) - 1)
        return list(sets[idx])

    def _start_conversation(self):
        self.visit_count += 1
        self.active_lines = self._select_lines_for_visit(self.visit_count) or ["..."]
        self._idx = 0
        self.talk_active = True

    def _current_node(self):
        if not self.active_lines:
            return "..."
        return self.active_lines[min(self._idx, len(self.active_lines) - 1)]

    # ---------------------------
    # 선택지 적용
    # ---------------------------
    def _apply_choice(self, choice: dict):
        nxt = choice.get("next")

        # next가 리스트면 그걸 새 대사 세트로
        if isinstance(nxt, list) and nxt:
            self.active_lines = list(nxt)
            self._idx = 0
            self.talk_active = True
            return

        # next가 문자열이면 한 줄짜리 응답
        if isinstance(nxt, str) and nxt:
            self.active_lines = [nxt]
            self._idx = 0
            self.talk_active = True
            return

        # next가 없으면 대화 종료
        self.talk_active = False

    # ---------------------------
    # 업데이트(입력 처리)
    # ---------------------------
    def update(self, player_rect: pygame.Rect, events):
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        near = (dx * dx + dy * dy) ** 0.5 <= self.range
        node = self._current_node()
        has_choices = isinstance(node, dict) and node.get("choices")

        for e in events:
            # 대화 시작/진행
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE and near:
                if not self.talk_active:
                    self._start_conversation()
                else:
                    # 선택지 노드에서는 SPACE로 넘기지 않게(실수 방지)
                    if has_choices:
                        continue
                    self._idx += 1
                    if self._idx >= len(self.active_lines):
                        self.talk_active = False

            # 키보드 선택지 1~9
            if e.type == pygame.KEYDOWN and self.talk_active and has_choices:
                if pygame.K_1 <= e.key <= pygame.K_9:
                    ci = e.key - pygame.K_1
                    choices = node.get("choices", [])
                    if 0 <= ci < len(choices):
                        self._apply_choice(choices[ci])

            # 마우스 선택지 클릭
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.talk_active and has_choices:
                mx, my = e.pos
                for r, choice in self._choice_rects:
                    if r.collidepoint(mx, my):
                        self._apply_choice(choice)
                        break

        return near

    # ---------------------------
    # 그리기
    # ---------------------------
    def draw(self, surf, camera_x: float):
        sx = int(self.pos.x - camera_x)
        sy = int(self.pos.y)

        if self.sprite:
            surf.blit(self.sprite, (sx, sy))
        else:
            body = pygame.Rect(sx, sy, self.w, self.h)
            pygame.draw.rect(surf, (210, 120, 120), body, border_radius=6)

        name_img = self.big.render(self.name, True, (40, 30, 35))
        box = pygame.Surface((name_img.get_width() + 10, name_img.get_height() + 4), pygame.SRCALPHA)
        box.fill((255, 255, 255, 160))
        surf.blit(box, (sx + self.w // 2 - box.get_width() // 2, sy - box.get_height() - 6))
        surf.blit(name_img, (sx + self.w // 2 - name_img.get_width() // 2, sy - box.get_height() - 4))

    def draw_dialog(self, surf: pygame.Surface, camera_x: float, near: bool,
                    screen_w: int, screen_h: int,
                    *, camera_y: float = 0.0, topdown: bool = False):
        # -------------------------------------------------
        # 1) 힌트: 가까이 있고 대화 중이 아닐 때
        #    - 사이드뷰: NPC 위
        #    - 탑다운: NPC 아래
        # -------------------------------------------------
        if near and not self.talk_active:
            hint = self.font.render("SPACE: 대화하기", True, (30, 30, 40))
            box = pygame.Surface((hint.get_width() + 10, hint.get_height() + 6), pygame.SRCALPHA)
            box.fill((255, 255, 255, 180))

            sx = int(self.rect.centerx - camera_x) - box.get_width() // 2

            if topdown:
                # ✅ 탑다운: NPC 바로 아래
                sy = int(self.rect.bottom - camera_y) + 8
                # 화면 밖으로 나가면 클램프
                if sy + box.get_height() > screen_h - 4:
                    sy = screen_h - box.get_height() - 4
            else:
                # ✅ 사이드뷰: 기존처럼 위쪽
                sy = int(self.rect.top - camera_y) - 70

            surf.blit(box, (sx, sy))
            surf.blit(hint, (sx + 5, sy + 3))
            return

        # -------------------------------------------------
        # 2) 대화 중이 아니면 종료
        # -------------------------------------------------
        if not self.talk_active:
            return

        # -------------------------------------------------
        # 3) 대화 패널(기존 그대로)
        # -------------------------------------------------
        box_h = 150
        panel = pygame.Surface((screen_w, box_h), pygame.SRCALPHA)
        panel.fill((18, 20, 24, 235))
        surf.blit(panel, (0, screen_h - box_h))

        # 이름 + 방문 뱃지
        title = f"{self.name}  ·  {self.visit_count}번째 만남"
        name_img = self.big.render(title, True, (250, 230, 170))
        surf.blit(name_img, (16, screen_h - box_h + 12))

        # 본문
        text = self.active_lines[min(self._idx, len(self.active_lines) - 1)]
        x0, y0 = 16, screen_h - box_h + 48
        max_w = screen_w - 32
        for i, ln in enumerate(_wrap_text(text, self.font, max_w)):
            line_img = self.font.render(ln, True, (235, 235, 240))
            surf.blit(line_img, (x0, y0 + i * 22))

        # 힌트
        hint = self.font.render("SPACE: 다음  |  마지막에서 닫힘", True, (200, 200, 210))
        surf.blit(hint, (screen_w - hint.get_width() - 12, screen_h - hint.get_height() - 10))

        # 선택지 렌더
        if choices:
            # 버튼 배치(가로로 2~3개씩 자연 분산)
            btn_y = screen_h - 36
            btn_pad_x = 10
            gap = 8

            cur_x = 16
            for i, ch in enumerate(choices):
                label = ch.get("label", f"선택 {i+1}")
                txt = self.font.render(f"{i+1}. {label}", True, (30, 30, 40))

                bw = txt.get_width() + btn_pad_x * 2
                bh = txt.get_height() + 8

                # 줄바꿈이 필요하면 다음 줄로
                if cur_x + bw > screen_w - 16:
                    cur_x = 16
                    btn_y -= (bh + 6)

                rect_btn = pygame.Rect(cur_x, btn_y, bw, bh)
                pygame.draw.rect(surf, (245, 245, 250), rect_btn, border_radius=6)
                pygame.draw.rect(surf, (30, 30, 50), rect_btn, 1, border_radius=6)
                surf.blit(txt, (rect_btn.x + btn_pad_x, rect_btn.y + 4))

                self._choice_rects.append((rect_btn, ch))
                cur_x += bw + gap

        else:
            hint = self.font.render("SPACE: 다음  |  마지막에서 닫힘", True, (200, 200, 210))
            surf.blit(hint, (screen_w - hint.get_width() - 12, screen_h - hint.get_height() - 8))
