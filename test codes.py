import sys
import math
import pygame
import os
from typing import Callable, Optional

# ===== 한글 폰트 로더 =====
def load_korean_font(size: int):
    """시스템 한글 폰트 탐색 → 실패 시 asset/NanumGothic.ttf 사용"""
    candidates = [
        "Malgun Gothic", "MalgunGothic",         # Windows
        "Apple SD Gothic Neo", "AppleGothic",    # macOS
        "NanumGothic", "Noto Sans CJK KR", "Noto Sans KR"  # Linux/공통
    ]
    try:
        path = pygame.font.match_font(candidates, bold=False, italic=False)
    except Exception:
        path = None

    if not path:
        asset_dir = os.path.join(os.path.dirname(__file__), "asset")
        fallback = os.path.join(asset_dir, "NanumGothic.ttf")
        if os.path.exists(fallback):
            path = fallback

    if not path:
        return pygame.font.SysFont(None, size)

    return pygame.font.Font(path, size)

# ===== ToggleSwitch 클래스 =====
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
        border_color=(0, 0, 0),
        font: Optional[pygame.font.Font] = None,
        on_change: Optional[Callable[[bool], None]] = None,
        animation_duration: float = 0.12,  # 초
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.on_color = on_color
        self.off_color = off_color
        self.knob_color = knob_color
        self.border_color = border_color
        self.on_change = on_change
        self.animation_duration = max(0.01, animation_duration)

        self.font = font or load_korean_font(14)

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

    @staticmethod
    def _lerp(a, b, t):
        return a + (b - a) * t

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

        if t >= 0.95:
            label_surf = self.font.render("On", True, self.on_color)
            lx = self.rect.topright[0] + self.label_offset[0] - label_surf.get_width()
            ly = self.rect.topright[1] + self.label_offset[1] - label_surf.get_height()
            surf.blit(label_surf, (lx, ly))

# ===== 메인 =====
def main():
    pygame.init()

    WIDTH, HEIGHT = 1200, 800
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("설정 패널 + ToggleSwitch + 한글폰트")

    clock = pygame.time.Clock()

    # --- asset/settings.png ---
    ASSET_DIR = os.path.join(os.path.dirname(__file__), "asset")
    settings_img = pygame.image.load(os.path.join(ASSET_DIR, "settings.png")).convert_alpha()
    button_size = 48
    settings_img = pygame.transform.scale(settings_img, (button_size, button_size))
    button_rect = settings_img.get_rect()
    button_rect.topright = (WIDTH - 10, 10)

    # mouse_grab 초기화
    mouse_grab = True
    pygame.event.set_grab(mouse_grab)

    # 설정 패널 상태
    settings_open = False
    font = load_korean_font(28)
    title_font = load_korean_font(36)

    # 패널 레이아웃
    panel_w, panel_h = 420, 220
    panel_x = (WIDTH - panel_w) // 2
    panel_y = (HEIGHT - panel_h) // 2
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

    def on_toggle_mouse_grab(state: bool):
        nonlocal mouse_grab
        mouse_grab = state
        pygame.event.set_grab(mouse_grab)

    grab_toggle = ToggleSwitch(
        x=panel_x + 24,
        y=panel_y + 90,
        width=92,
        height=44,
        initial=mouse_grab,
        on_change=on_toggle_mouse_grab,
        font=load_korean_font(14)
    )

    # 캐릭터
    size = 36
    pos_x = float(WIDTH // 2 - size // 2)
    pos_y = float(HEIGHT // 2 - size // 2)
    speed = 240.0
    target = None

    circles = []

    running = True
    while running:
        dt = clock.tick(0) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if settings_open:
                    settings_open = False
                else:
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and button_rect.collidepoint(event.pos):
                    settings_open = not settings_open

                if settings_open:
                    grab_toggle.handle_event(event)

                elif event.button == 3:
                    mx, my = event.pos
                    target = (float(mx - size / 2), float(my - size / 2))
                    circles.append((mx, my, pygame.time.get_ticks()))

        if settings_open:
            grab_toggle.update(dt)

        # 캐릭터 이동
        if target is not None:
            dx = target[0] - pos_x
            dy = target[1] - pos_y
            dist = math.hypot(dx, dy)
            if dist > 1e-3:
                step = speed * dt
                if step >= dist:
                    pos_x, pos_y = target
                    target = None
                else:
                    ux, uy = dx / dist, dy / dist
                    pos_x += ux * step
                    pos_y += uy * step
            else:
                pos_x, pos_y = target
                target = None

        # --- 그리기 ---
        screen.fill((25, 28, 35))

        # 캐릭터
        pygame.draw.rect(screen, (255, 200, 60), (int(pos_x), int(pos_y), size, size))

        # 원 (0.5초 축소+페이드)
        now = pygame.time.get_ticks()
        new_circles = []
        start_radius = 20
        duration = 0.5
        for (cx, cy, st) in circles:
            elapsed = (now - st) / 1000.0
            if elapsed < duration:
                ratio = 1 - elapsed / duration
                radius = max(1, int(start_radius * ratio))
                alpha = int(255 * ratio)
                circle_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(circle_surf, (120, 200, 255, alpha),
                                   (radius, radius), radius, width=2)
                screen.blit(circle_surf, (cx - radius, cy - radius))
                new_circles.append((cx, cy, st))
        circles = new_circles

        # 설정 버튼
        screen.blit(settings_img, button_rect)

        # 설정 패널
        if settings_open:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))

            pygame.draw.rect(screen, (32, 36, 44), panel_rect, border_radius=14)
            pygame.draw.rect(screen, (90, 120, 160), panel_rect, width=2, border_radius=14)

            title_surf = title_font.render("설정", True, (240, 240, 240))
            screen.blit(title_surf, (panel_x + 20, panel_y + 16))

            label = "마우스 창 고정 (set_grab)"
            label_surf = font.render(label, True, (230, 230, 230))
            screen.blit(label_surf, (panel_x + 24 + 110, panel_y + 90 + 10))

            grab_toggle.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
