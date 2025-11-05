# npc.py
import pygame
from pygame.math import Vector2 as V2
from settings import *
from utils import draw_multiline

# ===== 대화 트리 구조 =====
class DialogueNode:
    def __init__(self, node_id, text, choices=None):
        """
        node_id: 고유 id (str)
        text: 본문 (str)
        choices: [(라벨(str), next_id(str))]  # 없으면 [] 처리
        """
        self.id = node_id
        self.text = text
        self.choices = choices or []

# ===== 예시 트리: "안녕 / 어쩌라고" =====
SAMPLE_NODES = {
    "start": DialogueNode("start",
        "안녕. 무엇을 고를래?",
        choices=[("안녕", "hello")]),
    "hello": DialogueNode("hello",
        "나도 안녕! 하늘섬에 온 걸 환영해.",
        choices=[("여기는 어디야?", "where"), ("넌 누구야", "who")]),
    "where": DialogueNode("where",
        "여기는 엘테리아 야",
        choices=[("그게 뭐죠?",""),("알려주세요","")]),
    "bye": DialogueNode("bye", "바람이 너의 길을 비출 거야.", choices=[])
}

class NPC:
    def __init__(self, name, world_pos, lines=None, color=(140,185,255),
                 dialog_nodes=None, start_node_id=None):
        self.name = name
        self.world_pos = V2(world_pos)
        self.lines = list(lines) if lines else []  # 하위호환(선형 대사)
        self.color = color
        self.radius = NPC_RADIUS

        # 트리형 대화
        self.dialog_nodes = dialog_nodes or {}
        self.start_node_id = start_node_id

    def draw(self, surf, camera_offset, font, player_pos=None):
        pos = self.world_pos + camera_offset
        pygame.draw.circle(surf, self.color, pos, self.radius)
        pygame.draw.circle(surf, (20,30,40), pos, self.radius, 2)

        name_img = font.render(self.name, True, (240,240,245))
        name_rect = name_img.get_rect(midbottom=(pos.x, pos.y-self.radius-6))
        bg_rect = pygame.Rect(name_rect.x-6, name_rect.y-2, name_rect.width+12, name_rect.height+4)
        pygame.draw.rect(surf, (30,35,45), bg_rect, border_radius=6)
        pygame.draw.rect(surf, (60,70,85), bg_rect, 1, border_radius=6)
        surf.blit(name_img, name_rect)

        if player_pos is not None:
            if (self.world_pos - player_pos).length() <= INTERACT_DISTANCE:
                hint = font.render("스페이스: 대화 / 마우스로 선택", True, (250, 230, 120))
                hint_rect = hint.get_rect(midtop=(pos.x, pos.y + self.radius + 6))
                surf.blit(hint, hint_rect)

    def distance_to(self, player_pos: V2) -> float:
        return (self.world_pos - player_pos).length()

class DialogManager:
    def __init__(self):
        self.active = False
        self.npc: NPC | None = None

        # 선형 모드
        self.linear = False
        self.index = 0

        # 트리 모드
        self.tree = False
        self.nodes: dict[str, DialogueNode] = {}
        self.current_id: str | None = None
        self.choice_mode = False  # 시각적 강조용

        # 마우스 선택 히트박스
        self.choice_hitboxes: list[tuple[pygame.Rect, int]] = []

    # ----- 열기/닫기 -----
    def open(self, npc: NPC):
        self.active = True
        self.npc = npc
        if npc.dialog_nodes and npc.start_node_id in npc.dialog_nodes:
            self.tree = True
            self.linear = False
            self.nodes = npc.dialog_nodes
            self.current_id = npc.start_node_id
            self.choice_mode = False
        else:
            self.tree = False
            self.linear = True
            self.index = 0

    def close(self):
        self.active = False
        self.npc = None
        self.linear = False
        self.tree = False
        self.index = 0
        self.nodes = {}
        self.current_id = None
        self.choice_mode = False
        self.choice_hitboxes.clear()

    # ----- 진행/선택 -----
    def progress(self):
        if not self.active or not self.npc:
            return
        if self.linear:
            self.index += 1
            if self.index >= len(self.npc.lines):
                self.close()
            return
        if self.tree:
            if self.current_id is None:
                self.close(); return
            node = self.nodes[self.current_id]
            if node.choices:
                self.choice_mode = True  # 스페이스 누르면 선택지 강조
            else:
                self.close()

    def choose(self, choice_idx: int):
        # choice_mode 없이도 즉시 선택 가능
        if not (self.active and self.tree and self.current_id):
            return
        node = self.nodes.get(self.current_id)
        if not node or not node.choices:
            return
        if not (0 <= choice_idx < len(node.choices)):
            return
        _, next_id = node.choices[choice_idx]
        if next_id in self.nodes:
            self.current_id = next_id
            self.choice_mode = False
            self.choice_hitboxes.clear()
        else:
            self.close()

    def handle_mouse(self, pos):
        # choice_mode 여부와 무관하게, 현재 노드에 선택지가 있으면 즉시 선택 허용
        if not (self.active and self.tree):
            return
        for rect, idx in self.choice_hitboxes:
            if rect.collidepoint(pos):
                self.choose(idx)
                break

    # ----- 렌더 -----
    def draw(self, surf, big_font, font):
        if not self.active or not self.npc:
            return

        box_h = 178 if (self.tree and self._current_has_choices()) else 130
        box = pygame.Surface((SCREEN_W, box_h), pygame.SRCALPHA)
        box.fill((18,20,24,235))
        surf.blit(box, (0, SCREEN_H - box_h))

        name_img = big_font.render(self.npc.name, True, (250,230,170))
        surf.blit(name_img, (20, SCREEN_H - box_h + 14))

        if self.linear:
            text = self.npc.lines[self.index] if self.index < len(self.npc.lines) else ""
            draw_multiline(surf, text, font, (235,235,240), (20, SCREEN_H - box_h + 48), SCREEN_W - 40)
            hint = font.render("스페이스: 다음 | ESC: 닫기", True, (200,200,210))
            surf.blit(hint, (SCREEN_W - hint.get_width() - 16, SCREEN_H - hint.get_height() - 10))
            return

        node = self.nodes.get(self.current_id)
        if not node:
            return

        draw_multiline(surf, node.text, font, (235,235,240),
                       (20, SCREEN_H - box_h + 48), SCREEN_W - 40)

        self.choice_hitboxes.clear()
        if node.choices:
            y0 = SCREEN_H - box_h + 48 + 70
            mouse_pos = pygame.mouse.get_pos()
            for i, (label, _) in enumerate(node.choices, start=1):
                line = f"{i}. {label}"
                img = font.render(line, True, (240, 240, 245))
                item_rect = pygame.Rect(28, y0 - 2, img.get_width() + 16, img.get_height() + 6)

                # choice_mode면 전체 강조, 아니면 호버만 강조
                if item_rect.collidepoint(mouse_pos) or self.choice_mode:
                    pygame.draw.rect(surf, (50, 62, 78), item_rect, border_radius=6)
                    pygame.draw.rect(surf, (90, 110, 140), item_rect, 1, border_radius=6)
                else:
                    pygame.draw.rect(surf, (36, 42, 52), item_rect, border_radius=6)
                    pygame.draw.rect(surf, (70, 80, 95), item_rect, 1, border_radius=6)

                surf.blit(img, (36, y0))
                self.choice_hitboxes.append((item_rect, i - 1))
                y0 += 28

            hint = font.render("마우스로 선택 | 1~9: 선택 | 스페이스: 본문→선택 | ESC: 닫기", True, (200,200,210))
            surf.blit(hint, (SCREEN_W - hint.get_width() - 16, SCREEN_H - hint.get_height() - 10))

    def _current_has_choices(self):
        if not (self.tree and self.current_id and self.current_id in self.nodes):
            return False
        return len(self.nodes[self.current_id].choices) > 0
