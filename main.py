# main.py
# -----------------------------------------
# 전체 게임 실행 진입점
# - click_ring 모듈 제거 → Player가 자체 이펙트 관리
# -----------------------------------------
import os, pygame
from config import WIDTH, HEIGHT, TITLE, BG_COLOR, BUTTON_SIZE, BUTTON_MARGIN, PANEL_SIZE
from game.player import Player
from ui.settings_panel import SettingsPanel
import sys, os
sys.path.append(os.path.dirname(__file__))
def resource_path(*parts):
    base = os.path.dirname(__file__)
    return os.path.join(base, *parts)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # 설정 아이콘
    settings_img = pygame.image.load(resource_path("assets", "settings.png")).convert_alpha()
    settings_img = pygame.transform.scale(settings_img, (BUTTON_SIZE, BUTTON_SIZE))
    button_rect = settings_img.get_rect()
    button_rect.topright = (WIDTH - BUTTON_MARGIN, BUTTON_MARGIN)

    # 마우스 창 고정 초기값
    mouse_grab = True
    pygame.event.set_grab(mouse_grab)

    # 설정 패널: mouse_grab 토글 콜백
    def on_toggle_mouse_grab(state: bool):
        nonlocal mouse_grab
        mouse_grab = state
        pygame.event.set_grab(mouse_grab)

    settings = SettingsPanel((WIDTH, HEIGHT), PANEL_SIZE, on_toggle_mouse_grab)

    # 플레이어 (이제 내부에서 클릭 링 이펙트도 함께 관리)
    player = Player(start_pos=(WIDTH // 2 - 18, HEIGHT // 2 - 18))

    running = True
    while running:
        dt = clock.tick(0) / 1000.0  # FPS 제한 없음

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if settings.open:
                    settings.open = False
                else:
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 설정 버튼
                if event.button == 1 and button_rect.collidepoint(event.pos):
                    settings.open = not settings.open

                # 설정 열려있으면 UI에 이벤트 전달
                if settings.open:
                    settings.handle_event(event)

                # 우클릭 이동 + (플레이어 내부) 링 이펙트 생성
                elif event.button == 3:
                    mx, my = event.pos
                    player.set_target((mx, my))
                    player.spawn_click_ring(mx, my)

        if settings.open:
            settings.update(dt)

        player.update(dt)

        # 렌더링
        screen.fill(BG_COLOR)
        player.draw(screen)
        player.update_and_draw_click_rings(screen)  # ← 이 줄로 이펙트 그리기

        # 설정 버튼/패널
        screen.blit(settings_img, button_rect)
        settings.draw(screen)

        pygame.display.flip()

    pygame.quit()
main()