# npc.py
import pygame
from pygame.math import Vector2 as V2

from settings import SCREEN_W, SCREEN_H, NPC_RADIUS, INTERACT_DISTANCE
from utils import draw_multiline


# ============================================================
#  대화 트리 구조
# ============================================================
class DialogueNode:
    def __init__(self, node_id: str, text: str, choices=None):
        """
        node_id: 고유 id (str)
        text   : 본문 (str)
        choices: [(라벨(str), next_id(str))]  # 없으면 [] 처리
        """
        self.id = node_id
        self.text = text
        self.choices = choices or []


# ===== 예시 트리 =====
SAMPLE_NODES: dict[str, DialogueNode] = {
    "start": DialogueNode(
        "start",
        "안녕. 무엇을 고를래?",
        choices=[("안녕", "hello")]
    ),
    "hello": DialogueNode(
        "hello",
        "나도 안녕! 하늘섬에 온 걸 환영해.",
        choices=[("여기는 어디야?", "where"), ("넌 누구야?", "who")]
    ),
    "where": DialogueNode(
        "where",
        "여기는 엘테리아야. 세금이 너무 올라서 모두 힘들어하고 있지...",
        choices=[("다른 얘기도 들려줘", "hello"), ("그만 듣기", "bye")]
    ),
    "who": DialogueNode(
        "who",
        "나는 이곳에서 오래 산 사람이야. 요즘 세상이 참 험해졌지.",
        choices=[("반란군에 대해 알고 있어?", "where"), ("이만 가볼게", "bye")]
    ),
    "bye": DialogueNode("bye", "바람이 너의 길을 비출 거야.", choices=[]),
}


# ============================================================
#  일반 사람형 NPC
# ============================================================
class NPC:
    def __init__(self, name, world_pos, lines=None, color=(140, 185, 255),
                 dialog_nodes=None, start_node_id=None):
        """
        name          : NPC 이름
        world_pos     : 월드 좌표(Vector2 or (x, y))
        lines         : 단순 선형 대사 리스트 (["...", "..."])
        dialog_nodes  : 트리형 대화 노드 딕셔너리 (id -> DialogueNode)
        start_node_id : 시작 노드 id
        """
        self.name = name
        self.world_pos = V2(world_pos)
        self.lines = list(lines) if lines else []
        self.color = color
        self.radius = NPC_RADIUS

        # 트리형 대화
        self.dialog_nodes: dict[str, DialogueNode] = dialog_nodes or {}
        self.start_node_id: str | None = start_node_id

    def draw(self, surf: pygame.Surface, camera_offset: V2, font, player_pos: V2 | None = None):
        """화면에 NPC와 이름, 힌트까지 그리기."""
        pos = self.world_pos + camera_offset

        # 몸통 (동그라미)
        pygame.draw.circle(surf, self.color, pos, self.radius)
        pygame.draw.circle(surf, (20, 30, 40), pos, self.radius, 2)

        # 이름 라벨
        name_img = font.render(self.name, True, (240, 240, 245))
        name_rect = name_img.get_rect(midbottom=(pos.x, pos.y - self.radius - 6))
        bg_rect = pygame.Rect(
            name_rect.x - 6,
            name_rect.y - 2,
            name_rect.width + 12,
            name_rect.height + 4,
        )
        pygame.draw.rect(surf, (30, 35, 45), bg_rect, border_radius=6)
        pygame.draw.rect(surf, (60, 70, 85), bg_rect, 1, border_radius=6)
        surf.blit(name_img, name_rect)

        # 상호작용 힌트
        if player_pos is not None:
            if (self.world_pos - player_pos).length() <= INTERACT_DISTANCE:
                hint = font.render("스페이스: 대화 / 마우스로 선택", True, (250, 230, 120))
                hint_rect = hint.get_rect(midtop=(pos.x, pos.y + self.radius + 6))
                surf.blit(hint, hint_rect)

    def distance_to(self, player_pos: V2) -> float:
        return (self.world_pos - player_pos).length()


# ============================================================
#  대화 매니저
# ============================================================
class DialogManager:
    """
    대화창 열기 / 닫기 / 진행 / 선택 / 렌더링 관리
    main.py에서는:
        dialog = DialogManager(SAMPLE_NODES, font, big_font)
        dialog.open(npc)
        dialog.draw(screen)
    이런 식으로 사용.
    """
    def __init__(self, default_nodes=None, font=None, big_font=None):
        self.default_nodes: dict[str, DialogueNode] = default_nodes or {}
        self.font = font
        self.big_font = big_font or font

        self.active = False
        self.npc: NPC | None = None

        # 선형 모드
        self.linear = False
        self.index = 0

        # 트리 모드
        self.tree = False
        self.nodes: dict[str, DialogueNode] = {}
        self.current_id: str | None = None
        self.choice_mode = False  # 스페이스로 '선택지 모드' 들어갔는지

        # 마우스 선택 히트박스
        self.choice_hitboxes: list[tuple[pygame.Rect, int]] = []

    # ----- 열기/닫기 -----
    def open(self, npc: NPC):
        """해당 NPC와의 대화를 시작."""
        self.active = True        # 대화 활성화
        self.npc = npc

        # NPC가 자신만의 트리형 대사를 갖고 있다면 우선 사용
        if npc.dialog_nodes and npc.start_node_id in npc.dialog_nodes:
            self.tree = True
            self.linear = False
            self.nodes = npc.dialog_nodes
            self.current_id = npc.start_node_id
            self.choice_mode = False
        # 아니면 기본 샘플 노드 사용
        elif self.default_nodes:
            self.tree = True
            self.linear = False
            self.nodes = self.default_nodes
            self.current_id = "start"
            self.choice_mode = False
        # 아무 트리도 없으면 선형 대사 모드
        else:
            self.tree = False
            self.linear = True
            self.index = 0

    def close(self):
        """대화 종료."""
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
        """스페이스로 '다음'을 눌렀을 때 호출."""
        if not self.active or not self.npc:
            return

        # 선형 대사
        if self.linear:
            self.index += 1
            if self.index >= len(self.npc.lines):
                self.close()
            return

        # 트리형 대사
        if self.tree:
            if self.current_id is None:
                self.close()
                return
            node = self.nodes[self.current_id]
            if node.choices:
                # 본문을 읽은 뒤 선택지 강조 모드로 전환
                self.choice_mode = True
            else:
                self.close()

    def choose(self, choice_idx: int):
        """선택지 번호(0 기반)를 전달하면 해당 선택을 수행."""
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

    def handle_mouse(self, pos: tuple[int, int]):
        """마우스로 선택지 클릭 처리."""
        if not (self.active and self.tree):
            return
        for rect, idx in self.choice_hitboxes:
            if rect.collidepoint(pos):
                self.choose(idx)
                break

    # ----- 업데이트/렌더 -----
    def update(self, dt: float):
        """필요하면 나중에 애니메이션용으로 사용. 지금은 비어 있음."""
        pass

    def draw(self, surf: pygame.Surface):
        """대화창 전체 그리기."""
        if not self.active or not self.npc:
            return

        font = self.font
        big_font = self.big_font

        box_h = 178 if (self.tree and self._current_has_choices()) else 130
        box = pygame.Surface((SCREEN_W, box_h), pygame.SRCALPHA)
        box.fill((18, 20, 24, 235))
        surf.blit(box, (0, SCREEN_H - box_h))

        # 이름
        name_img = big_font.render(self.npc.name, True, (250, 230, 170))
        surf.blit(name_img, (20, SCREEN_H - box_h + 14))

        # 선형 모드
        if self.linear:
            text = self.npc.lines[self.index] if self.index < len(self.npc.lines) else ""
            draw_multiline(
                surf, text, font, (235, 235, 240),
                (20, SCREEN_H - box_h + 48), SCREEN_W - 40
            )
            hint = font.render("스페이스: 다음 | ESC: 닫기", True, (200, 200, 210))
            surf.blit(hint, (SCREEN_W - hint.get_width() - 16,
                             SCREEN_H - hint.get_height() - 10))
            return

        # 트리 모드
        node = self.nodes.get(self.current_id)
        if not node:
            return

        draw_multiline(
            surf, node.text, font, (235, 235, 240),
            (20, SCREEN_H - box_h + 48), SCREEN_W - 40
        )

        self.choice_hitboxes.clear()
        if node.choices:
            y0 = SCREEN_H - box_h + 48 + 70
            mouse_pos = pygame.mouse.get_pos()

            for i, (label, _) in enumerate(node.choices, start=1):
                line = f"{i}. {label}"
                img = font.render(line, True, (240, 240, 245))
                item_rect = pygame.Rect(
                    28, y0 - 2,
                    img.get_width() + 16,
                    img.get_height() + 6
                )

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

            hint = font.render(
                "마우스로 선택 | 1~9: 선택 | 스페이스: 본문→선택 | ESC: 닫기",
                True, (200, 200, 210)
            )
            surf.blit(hint, (SCREEN_W - hint.get_width() - 16,
                             SCREEN_H - hint.get_height() - 10))

    def _current_has_choices(self) -> bool:
        if not (self.tree and self.current_id and self.current_id in self.nodes):
            return False
        return len(self.nodes[self.current_id].choices) > 0


# ============================================================
#  은행 건물 NPC (맵 전환용)
# ============================================================
class BankNPC:
    """
    은행 건물 모양의 NPC.
    - draw()는 은행 이미지를 그린다.
    - on_interact()는 대화 대신 'enter_bank' 또는 'exit_bank' 같은 액션 문자열을 반환한다.
    """

    def __init__(self, world_pos, *, direction="enter",
                 sprite_path="assets/sprites/bank_npc.png"):
        """
        world_pos : 월드 좌표 (타일 중앙에 두고 싶으면 (c-0.5)*TILE_SIZE 이런 식으로)
        direction : "enter"  -> 도시에서 은행 안으로 들어가는 용도
                    "exit"   -> 은행 안에서 도시로 나가는 용도
        """
        self.world_pos = V2(world_pos)
        self.direction = direction
        self.sprite_path = sprite_path

        self.image: pygame.Surface | None = None
        self.radius_for_interact = 80  # 얼마나 가까이 가야 상호작용 되는지
        self._load_sprite()

    def _load_sprite(self):
        try:
            img = pygame.image.load(self.sprite_path).convert_alpha()
            # 은행 건물은 조금 크게 보이도록 128x128 정도로 축소
            self.image = pygame.transform.smoothscale(img, (128, 128))
            print("[BankNPC] 스프라이트 로드:", self.sprite_path)
        except Exception as e:
            print("[BankNPC] 스프라이트 로드 실패:", self.sprite_path, e)
            self.image = None

    def is_player_in_range(self, player_world: V2, range_px=None) -> bool:
        """플레이어가 근처에 있는지 체크."""
        r = range_px if range_px is not None else self.radius_for_interact
        return (self.world_pos - player_world).length_squared() <= r * r

    def draw(self, surf: pygame.Surface, camera_offset: V2, font, player_pos: V2 | None = None):
        """은행 건물 그리기 + 이름 라벨 + 가까이 오면 힌트."""
        screen_pos = self.world_pos + camera_offset

        # 은행 건물 이미지
        if self.image:
            rect = self.image.get_rect(midbottom=(screen_pos.x, screen_pos.y))
            surf.blit(self.image, rect)
            top_y = rect.top
        else:
            # 이미지 없으면 임시 사각형
            size = 80
            rect = pygame.Rect(0, 0, size, size)
            rect.center = (screen_pos.x, screen_pos.y - size // 2)
            pygame.draw.rect(surf, (200, 150, 190), rect)
            top_y = rect.top

        # 이름 라벨
        label_text = "은행 출입" if self.direction == "enter" else "은행 출구"
        text_surf = font.render(label_text, True, (255, 230, 240))
        text_rect = text_surf.get_rect(midbottom=(screen_pos.x, top_y - 4))

        bg = pygame.Surface((text_rect.width + 10, text_rect.height + 4), pygame.SRCALPHA)
        bg.fill((40, 0, 40, 150))
        surf.blit(bg, (text_rect.x - 5, text_rect.y - 2))
        surf.blit(text_surf, text_rect)

        # 플레이어가 근처에 있으면 힌트
        if player_pos is not None:
            if (self.world_pos - player_pos).length() <= self.radius_for_interact:
                hint_surf = font.render("스페이스: 은행 출입", True, (250, 230, 120))
                hint_rect = hint_surf.get_rect(midtop=(screen_pos.x, rect.bottom + 4))
                surf.blit(hint_surf, hint_rect)

    def on_interact(self) -> str:
        """
        상호작용 요청. 대화 대신 '어떤 맵으로 갈지'를 문자열로 알려준다.
        main.py가 이 리턴값을 보고 실제 맵을 바꿔준다.
        """
        return "enter_bank" if self.direction == "enter" else "exit_bank"
