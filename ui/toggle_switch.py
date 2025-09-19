# ui/toggle_switch.py
# -----------------------------------------
# ToggleSwitch 위젯 - 폰트를 JUA.ttf로 고정
# -----------------------------------------
import pygame
from typing import Callable, Optional
from util.fonts import load_font_jua   # ← 변경 포인트

class ToggleSwitch:
    def __init__(
        self,
        x: int,
        y: int,
        width: int = 80,
        height: int = 40,
        initial: bool = False,
        on_color=(5, 196, 107),
        off_color=(221, 221, 221),
        knob_color=(255, 255, 255),
        font: Optional[pygame.font.Font] = None,
        on_change: Optional[Callable[[bool], None]] = None,
        animation_duration: float = 0.12,
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.on_color, self.off_color = on_color, off_color
        self.knob_color = knob_color
        self.on_change = on_change
        self.animation_duration = max(0.01, animation_duration)

        # ↓↓↓ JUA.ttf 사용
        self.font = font or load_font_jua(14)

        self._state = bool(initial)
        self._anim = float(1.0 if initial else 0.0)
        self._anim_target = float(self._state)
        self._anim_speed = 1.0 / self.animation_duration

        self.pad = 5
        self.knob_size = height - self.pad * 2
        self.left_x = x + self.pad
        self.right_x = x + width - self.pad - self.knob_size
        self.border_radius = height // 2
        self.label_offset = (-6, -10)

    @property
    def value(self) -> bool:
        return self._state

    def set(self, v: bool, animate: bool = True):
        v = bool(v)
        if v == self._state and ((self._anim_target == float(v)) or not animate):
            return
        self._state = v
        self._anim_target = float(v)
        if not animate:
            self._anim = self._anim_target
        if self.on_change:
            self.on_change(self._state)

    def toggle(self, animate: bool = True):
        self.set(not self._state, animate=animate)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.toggle(animate=True)

    def update(self, dt: float):
        if self._anim == self._anim_target:
            return
        direction = 1.0 if self._anim_target > self._anim else -1.0
        self._anim += direction * self._anim_speed * dt
        if (direction > 0 and self._anim >= self._anim_target) or (direction < 0 and self._anim <= self._anim_target):
            self._anim = self._anim_target

    def _lerp(self, a, b, t): return a + (b - a) * t

    def draw(self, surf: pygame.Surface):
        t = self._anim
        bg = (
            int(self._lerp(self.off_color[0], self.on_color[0], t)),
            int(self._lerp(self.off_color[1], self.on_color[1], t)),
            int(self._lerp(self.off_color[2], self.on_color[2], t)),
        )
        border_w = 2 if t > 0.5 else 0
        pygame.draw.rect(surf, bg, self.rect, border_radius=self.border_radius)
        if border_w:
            pygame.draw.rect(surf, (0, 0, 0), self.rect, width=border_w, border_radius=self.border_radius)

        knob_x = int(self._lerp(self.left_x, self.right_x, t))
        knob_rect = pygame.Rect(knob_x, self.rect.y + self.pad, self.knob_size, self.knob_size)
        pygame.draw.ellipse(surf, self.knob_color, knob_rect)

        # 'On' 라벨도 JUA.ttf로 렌더
        if t >= 0.95:
            label_surf = self.font.render("On", True, self.on_color)
            lx = self.rect.topright[0] + self.label_offset[0] - label_surf.get_width()
            ly = self.rect.topright[1] + self.label_offset[1] - label_surf.get_height()
            surf.blit(label_surf, (lx, ly))
