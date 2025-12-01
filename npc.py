# npc.py
import pygame
from pygame.math import Vector2 as V2
from settings import SCREEN_W, SCREEN_H, NPC_RADIUS, INTERACT_DISTANCE
from utils import draw_multiline  # ★ 모듈 상단에서 한 번만 임포트

# -------- 대화 노드 --------
class DialogueNode:
    def __init__(self, node_id: str, text: str, choices=None):
        self.id = node_id
        self.text = text
        self.choices = choices or []

SAMPLE_NODES = {
    "start": DialogueNode("start", "안녕. 무엇을 고를래?", choices=[("안녕", "hello")]),
    "hello": DialogueNode(
        "hello",
        "나도 안녕! 하늘섬에 온 걸 환영해.",
        choices=[("여기는 어디야?", "where"), ("넌 누구야?", "who")],
    ),
    "where": DialogueNode(
        "where",
        "여기는 엘테리아야. 세금이 너무 올라서 모두 힘들어하고 있지...",
        choices=[("다른 얘기도 들려줘", "hello"), ("그만 듣기", "bye")],
    ),
    "who": DialogueNode(
        "who",
        "나는 이곳에서 오래 산 사람이야. 요즘 세상이 험해졌지.",
        choices=[("반란군 얘기 좀 더", "where"), ("이만 가볼게", "bye")],
    ),
    "bye": DialogueNode("bye", "바람이 너의 길을 비출 거야.", choices=[]),
}

# -------- 사람형 NPC --------
class NPC:
    def __init__(self, name, world_pos, lines=None, color=(140,185,255),
                 dialog_nodes=None, start_node_id=None):
        self.name = name
        self.world_pos = V2(world_pos)
        self.lines = list(lines) if lines else []
        self.color = color
        self.radius = NPC_RADIUS
        self.dialog_nodes = dialog_nodes or {}
        self.start_node_id = start_node_id

    def draw(self, surf, camera_offset, font, player_pos: V2 | None = None):
        pos = self.world_pos + camera_offset
        pygame.draw.circle(surf, self.color, pos, self.radius)
        pygame.draw.circle(surf, (20,30,40), pos, self.radius, 2)

        name_img = font.render(self.name, True, (240,240,245))
        name_rect = name_img.get_rect(midbottom=(pos.x, pos.y-self.radius-6))
        bg = pygame.Rect(name_rect.x-6, name_rect.y-2, name_rect.width+12, name_rect.height+4)
        pygame.draw.rect(surf, (30,35,45), bg, border_radius=6)
        pygame.draw.rect(surf, (60,70,85), bg, 1, border_radius=6)
        surf.blit(name_img, name_rect)

        if player_pos is not None and (self.world_pos - player_pos).length() <= INTERACT_DISTANCE:
            hint = font.render("스페이스: 대화 / 마우스로 선택", True, (250,230,120))
            surf.blit(hint, hint.get_rect(midtop=(pos.x, pos.y+self.radius+6)))

# -------- 대화 매니저 --------
class DialogManager:
    def __init__(self, default_nodes=None, font=None, big_font=None):
        self.default_nodes = default_nodes or {}
        self.font = font
        self.big_font = big_font or font
        self.active = False
        self.npc: NPC | None = None

        self.linear = False
        self.index = 0

        self.tree = False
        self.nodes: dict[str, DialogueNode] = {}
        self.current_id: str | None = None
        self.choice_mode = False
        self.choice_hitboxes: list[tuple[pygame.Rect, int]] = []

    def open(self, npc: NPC):
        self.active, self.npc = True, npc
        if npc.dialog_nodes and npc.start_node_id in npc.dialog_nodes:
            self.tree, self.linear = True, False
            self.nodes, self.current_id = npc.dialog_nodes, npc.start_node_id
        elif self.default_nodes:
            self.tree, self.linear = True, False
            self.nodes, self.current_id = self.default_nodes, "start"
        else:
            self.tree, self.linear = False, True
            self.index = 0

    def close(self):
        self.active = False
        self.npc = None
        self.linear = self.tree = False
        self.index = 0
        self.nodes = {}
        self.current_id = None
        self.choice_mode = False
        self.choice_hitboxes.clear()

    def progress(self):
        if not (self.active and self.npc):
            return
        if self.linear:
            self.index += 1
            if self.index >= len(self.npc.lines):
                self.close()
            return
        if self.tree:
            if self.current_id is None:
                self.close()
                return
            node = self.nodes[self.current_id]
            self.choice_mode = bool(node.choices)
            if not node.choices:
                self.close()

    def choose(self, idx: int):
        if not (self.active and self.tree and self.current_id):
            return
        node = self.nodes.get(self.current_id)
        if not node or not node.choices:
            return
        if not (0 <= idx < len(node.choices)):
            return
        _, next_id = node.choices[idx]
        if next_id in self.nodes:
            self.current_id = next_id
            self.choice_mode = False
            self.choice_hitboxes.clear()
        else:
            self.close()

    def handle_mouse(self, pos):
        if not (self.active and self.tree):
            return
        for rect, idx in self.choice_hitboxes:
            if rect.collidepoint(pos):
                self.choose(idx)
                break

    def update(self, dt: float):
        pass

    def draw(self, surf):
        if not (self.active and self.npc):
            return

        font, big = self.font, self.big_font
        box_h = 178 if (self.tree and self._has_choices()) else 130
        box = pygame.Surface((SCREEN_W, box_h), pygame.SRCALPHA)
        box.fill((18,20,24,235))
        surf.blit(box, (0, SCREEN_H - box_h))

        surf.blit(big.render(self.npc.name, True, (250,230,170)), (20, SCREEN_H - box_h + 14))

        if self.linear:
            txt = self.npc.lines[self.index] if self.index < len(self.npc.lines) else ""
            draw_multiline(surf, txt, font, (235,235,240), (20, SCREEN_H - box_h + 48), SCREEN_W - 40)
            hint = font.render("스페이스: 다음 | ESC: 닫기", True, (200,200,210))
            surf.blit(hint, (SCREEN_H - hint.get_width() - 16, SCREEN_H - hint.get_height() - 10))
            return

        node = self.nodes.get(self.current_id)
        if not node:
            return

        draw_multiline(surf, node.text, font, (235,235,240), (20, SCREEN_H - box_h + 48), SCREEN_W - 40)

        self.choice_hitboxes.clear()
        if node.choices:
            y0 = SCREEN_H - box_h + 48 + 70
            mouse_pos = pygame.mouse.get_pos()
            for i, (label, _) in enumerate(node.choices, 1):
                line = f"{i}. {label}"
                img = font.render(line, True, (240,240,245))
                item = pygame.Rect(28, y0 - 2, img.get_width() + 16, img.get_height() + 6)

                if item.collidepoint(mouse_pos) or self.choice_mode:
                    pygame.draw.rect(surf, (50,62,78), item, border_radius=6)
                    pygame.draw.rect(surf, (90,110,140), item, 1, border_radius=6)
                else:
                    pygame.draw.rect(surf, (36,42,52), item, border_radius=6)
                    pygame.draw.rect(surf, (70,80,95), item, 1, border_radius=6)

                surf.blit(img, (36, y0))
                self.choice_hitboxes.append((item, i - 1))
                y0 += 28

            hint = font.render("마우스로 선택 | 1~9: 선택 | 스페이스: 본문→선택 | ESC: 닫기", True, (200,200,210))
            surf.blit(hint, (SCREEN_W - hint.get_width() - 16, SCREEN_H - hint.get_height() - 10))

    def _has_choices(self):
        return bool(
            self.tree and self.current_id and self.current_id in self.nodes
            and self.nodes[self.current_id].choices
        )

# -------- 은행 NPC (맵 전환) --------
class BankNPC:
    _SPRITE_CACHE: dict[str, pygame.Surface] = {}

    def __init__(self, world_pos, *, direction="enter", sprite_path="assets/sprites/bank_npc.png"):
        self.world_pos = V2(world_pos)
        self.direction = direction
        self.sprite_path = sprite_path
        self.image: pygame.Surface | None = None
        self.radius_for_interact = 80
        self._load_sprite()

    def _load_sprite(self):
        cached = BankNPC._SPRITE_CACHE.get(self.sprite_path)
        if cached is not None:
            self.image = cached
            return
        try:
            img = pygame.image.load(self.sprite_path).convert_alpha()
            img = pygame.transform.smoothscale(img, (128, 128))
            BankNPC._SPRITE_CACHE[self.sprite_path] = img
            self.image = img
        except Exception as e:
            print("[BankNPC] 스프라이트 로드 실패:", self.sprite_path, e)
            self.image = None

    def is_player_in_range(self, player_world: V2, r=None) -> bool:
        r = r or self.radius_for_interact
        return (self.world_pos - player_world).length_squared() <= r * r

    def draw(self, surf, camera_offset, font, player_pos: V2 | None = None):
        p = self.world_pos + camera_offset
        if self.image:
            rect = self.image.get_rect(midbottom=(p.x, p.y))
            surf.blit(self.image, rect)
            top_y = rect.top
        else:
            size = 80
            rect = pygame.Rect(0, 0, size, size)
            rect.center = (p.x, p.y - size // 2)
            pygame.draw.rect(surf, (200, 150, 190), rect)
            top_y = rect.top

        label = "은행 출입" if self.direction == "enter" else "은행 출구"
        lab_s = font.render(label, True, (255, 230, 240))
        lab_r = lab_s.get_rect(midbottom=(p.x, top_y - 4))
        bg = pygame.Surface((lab_r.width + 10, lab_r.height + 4), pygame.SRCALPHA)
        bg.fill((40, 0, 40, 150))
        surf.blit(bg, (lab_r.x - 5, lab_r.y - 2))
        surf.blit(lab_s, lab_r)

        if player_pos is not None and (self.world_pos - player_pos).length() <= self.radius_for_interact:
            hint = font.render("스페이스: 은행 출입", True, (250, 230, 120))
            surf.blit(hint, hint.get_rect(midtop=(p.x, rect.bottom + 4)))

    def on_interact(self) -> str:
        return "enter_bank" if self.direction == "enter" else "exit_bank"
