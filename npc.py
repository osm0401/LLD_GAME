# npc.py
import pygame
from pygame.math import Vector2 as V2
from settings import *
from utils import draw_multiline

class NPC:
    def __init__(self, name, world_pos, lines, color=(140,185,255)):
        self.name = name
        self.world_pos = V2(world_pos)
        self.lines = list(lines)
        self.color = color
        self.radius = NPC_RADIUS

    def draw(self, surf, camera_offset, font, player_pos=None):
        pos = self.world_pos + camera_offset
        pygame.draw.circle(surf, self.color, pos, self.radius)
        pygame.draw.circle(surf, (20,30,40), pos, self.radius, 2)

        # 이름 라벨
        name_img = font.render(self.name, True, (240,240,245))
        name_rect = name_img.get_rect(midbottom=(pos.x, pos.y-self.radius-6))
        bg_rect = pygame.Rect(name_rect.x-6, name_rect.y-2, name_rect.width+12, name_rect.height+4)
        pygame.draw.rect(surf, (30,35,45), bg_rect, border_radius=6)
        pygame.draw.rect(surf, (60,70,85), bg_rect, 1, border_radius=6)
        surf.blit(name_img, name_rect)

        # 근접 상호작용 힌트
        if player_pos is not None:
            if (self.world_pos - player_pos).length() <= INTERACT_DISTANCE:
                hint = font.render("스페이스: 대화", True, (250, 230, 120))
                hint_rect = hint.get_rect(midtop=(pos.x, pos.y + self.radius + 6))
                surf.blit(hint, hint_rect)

    def distance_to(self, player_pos: V2) -> float:
        return (self.world_pos - player_pos).length()

class DialogManager:
    def __init__(self):
        self.active = False
        self.npc = None
        self.index = 0

    def open(self, npc):
        self.active, self.npc, self.index = True, npc, 0

    def close(self):
        self.active, self.npc, self.index = False, None, 0

    def progress(self):
        if not self.active or not self.npc:
            return
        self.index += 1
        if self.index >= len(self.npc.lines):
            self.close()

    def draw(self, surf, big_font, font):
        if not self.active or not self.npc:
            return
        box_h = 130
        box = pygame.Surface((SCREEN_W, box_h), pygame.SRCALPHA)
        box.fill((18,20,24,235))
        surf.blit(box, (0, SCREEN_H - box_h))

        name_img = big_font.render(self.npc.name, True, (250,230,170))
        surf.blit(name_img, (20, SCREEN_H - box_h + 14))

        text = self.npc.lines[self.index]
        draw_multiline(surf, text, font, (235,235,240), (20, SCREEN_H - box_h + 48), SCREEN_W - 40)
        hint = font.render("스페이스: 다음 | ESC: 닫기", True, (200,200,210))
        surf.blit(hint, (SCREEN_W - hint.get_width() - 16, SCREEN_H - hint.get_height() - 10))
