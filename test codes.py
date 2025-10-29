import pygame
from pygame.math import Vector2 as V2

"""
LoL‑style 카메라 고정: 플레이어는 화면 중앙에 고정, 우클릭으로 월드 좌표 타겟을 찍고
플레이어가 그 월드 타겟으로 이동. 배경(월드)이 반대로 움직이는 것처럼 보임.

실행 방법:
  pip install pygame
  python main.py

조작:
  마우스 오른쪽 버튼: 이동 목표 설정 (타깃 표시)
  ESC / 창 닫기: 종료

핵심 아이디어:
  - 플레이어의 위치는 "월드 좌표" (player_world_pos)
  - 카메라 오프셋 = 화면중심 - 플레이어월드좌표
  - 모든 그리기는 screen_pos = world_pos + camera_offset 으로 변환해서 그림
  - 이렇게 하면 플레이어는 항상 화면 중앙에 보이고, 배경/오브젝트가 반대로 움직이는 것처럼 보임
"""

# ===== 기본 설정 =====
SCREEN_W, SCREEN_H = 960, 540
CENTER = V2(SCREEN_W // 2, SCREEN_H // 2)
FPS = 60

# 월드 크기 (배경을 크게 잡아 카메라 이동감을 살림)
WORLD_W, WORLD_H = 3000, 3000

# 플레이어 파라미터
PLAYER_SPEED = 240.0  # px/sec
PLAYER_RADIUS = 14

# 타일/그리드 비주얼용
GRID_SPACING = 120


def draw_world_grid(surf: pygame.Surface, camera_offset: V2):
    """심플 월드 그리드(배경). 카메라 오프셋을 반영해 스크린에 그림."""
    # 월드 바탕
    surf.fill((17, 19, 24))

    # 그리드 라인들을 화면 범위에 맞춰 그리기
    # 화면 경계의 월드좌표
    top_left_world = -camera_offset
    bottom_right_world = V2(SCREEN_W, SCREEN_H) - camera_offset

    # 수직선
    start_x = int(top_left_world.x // GRID_SPACING * GRID_SPACING)
    end_x = int(bottom_right_world.x // GRID_SPACING * GRID_SPACING) + GRID_SPACING
    for x in range(start_x, end_x, GRID_SPACING):
        p1 = V2(x, top_left_world.y) + camera_offset
        p2 = V2(x, bottom_right_world.y) + camera_offset
        pygame.draw.line(surf, (36, 42, 52), p1, p2, 1)

    # 수평선
    start_y = int(top_left_world.y // GRID_SPACING * GRID_SPACING)
    end_y = int(bottom_right_world.y // GRID_SPACING * GRID_SPACING) + GRID_SPACING
    for y in range(start_y, end_y, GRID_SPACING):
        p1 = V2(top_left_world.x, y) + camera_offset
        p2 = V2(bottom_right_world.x, y) + camera_offset
        pygame.draw.line(surf, (36, 42, 52), p1, p2, 1)

    # 월드 경계(디버그 시각화)
    rect_screen = pygame.Rect(0, 0, WORLD_W, WORLD_H)
    rect_screen.topleft = camera_offset
    pygame.draw.rect(surf, (70, 80, 95), rect_screen, 2)


def clamp_to_world(pos: V2) -> V2:
    return V2(
        max(0, min(WORLD_W, pos.x)),
        max(0, min(WORLD_H, pos.y)),
    )


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("LoL‑style Camera | Right‑Click Move")
    clock = pygame.time.Clock()

    # 플레이어 월드 좌표 (초기: 월드 중앙 근처)
    player_world = V2(WORLD_W / 2, WORLD_H / 2)
    # 이동 목표(월드 좌표), None이면 정지
    move_target = None

    font = pygame.font.SysFont("consolas", 18)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # 우클릭
                mouse_screen = V2(event.pos)
                # 현재 카메라 오프셋을 사용해 스크린좌표 -> 월드좌표로 변환
                camera_offset = CENTER - player_world
                move_target = clamp_to_world(mouse_screen - camera_offset)

        # ===== 로직: 플레이어 월드 이동 =====
        if move_target is not None:
            to_target = move_target - player_world
            dist = to_target.length()
            if dist < 2:
                move_target = None  # 도착
            else:
                dir_vec = to_target.normalize()
                player_world += dir_vec * PLAYER_SPEED * dt
                player_world = clamp_to_world(player_world)

        # ===== 카메라 오프셋 계산 (플레이어를 화면 중앙에 고정) =====
        camera_offset = CENTER - player_world

        # ===== 그리기 =====
        # 1) 배경/월드
        draw_world_grid(screen, camera_offset)

        # 2) 디코용 오브젝트 몇 개 (나무/바위 느낌) – 월드좌표에 배치 후 오프셋 적용
        deco_world_positions = [
            V2(800, 900), V2(1200, 1500), V2(1900, 1000), V2(2400, 2200), V2(600, 2100),
        ]
        for i, wpos in enumerate(deco_world_positions):
            spos = wpos + camera_offset
            pygame.draw.circle(screen, (60, 120, 90), spos, 22)
            pygame.draw.circle(screen, (35, 80, 65), spos + V2(0, 2), 22, 2)

        # 3) 타깃 마커 (월드 -> 스크린 변환 후 표시)
        if move_target is not None:
            tpos = move_target + camera_offset
            pygame.draw.circle(screen, (200, 120, 40), tpos, 8, 2)
            pygame.draw.circle(screen, (200, 160, 60), tpos, 14, 1)

        # 4) 플레이어 (항상 화면 중앙에 고정 표현)
        # 실제로는 player_world를 쓰지만, 그릴 때는 CENTER를 사용
        pygame.draw.circle(screen, (220, 220, 235), CENTER, PLAYER_RADIUS)
        pygame.draw.circle(screen, (90, 100, 120), CENTER, PLAYER_RADIUS, 2)
        # 진행방향 표시 (작은 라인)
        mouse_screen = V2(pygame.mouse.get_pos())
        look_dir = (mouse_screen - CENTER)
        if look_dir.length_squared() > 1:
            look_dir = look_dir.normalize() * (PLAYER_RADIUS + 6)
            pygame.draw.line(screen, (160, 170, 190), CENTER, CENTER + look_dir, 2)

        # 5) UI 텍스트
        info_lines = [
            "우클릭: 이동 / ESC: 종료",
            f"player_world=({int(player_world.x)}, {int(player_world.y)})",
            f"target={'None' if move_target is None else (int(move_target.x), int(move_target.y))}",
        ]
        for i, s in enumerate(info_lines):
            img = font.render(s, True, (230, 230, 235))
            screen.blit(img, (12, 10 + i * 20))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
