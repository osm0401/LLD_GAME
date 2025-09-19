# ui/settings_panel.py
# -----------------------------------------
# 설정 패널(오버레이) - JUA.ttf로 텍스트 고정
# -----------------------------------------
import os, sys, pygame
# (필요 시) 경로 부트스트랩: util/fonts 임포트 보장
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from util.fonts import load_font_jua
from ui.toggle_switch import ToggleSwitch

class SettingsPanel:
    def __init__(self, screen_size, panel_size, on_toggle_mouse_grab):
        self.W, self.H = screen_size
        self.panel_w, self.panel_h = panel_size
        self.panel_x = (self.W - self.panel_w) // 2
        self.panel_y = (self.H - self.panel_h) // 2
        self.panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_w, self.panel_h)

        # ↓↓↓ JUA.ttf 사용
        self.font = load_font_jua(28)
        self.title_font = load_font_jua(36)

        self.grab_toggle = ToggleSwitch(
            x=self.panel_x + 24,
            y=self.panel_y + 90,
            width=92, height=44,
            initial=True,
            on_change=on_toggle_mouse_grab,
            font=load_font_jua(14),  # 스위치 내부 라벨도 JUA로
        )
        self.open = False

    def handle_event(self, event):
        if self.open:
            self.grab_toggle.handle_event(event)

    def update(self, dt):
        if self.open:
            self.grab_toggle.update(dt)

    def draw(self, surface):
        if not self.open:
            return

        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (32, 36, 44), self.panel_rect, border_radius=14)
        pygame.draw.rect(surface, (90, 120, 160), self.panel_rect, width=2, border_radius=14)

        title_surf = self.title_font.render("설정", True, (240, 240, 240))
        surface.blit(title_surf, (self.panel_x + 20, self.panel_y + 16))

        label = "마우스 창안 고정"
        label_surf = self.font.render(label, True, (230, 230, 230))
        surface.blit(label_surf, (self.panel_x + 24 + 110, self.panel_y + 90 + 10))

        self.grab_toggle.draw(surface)
