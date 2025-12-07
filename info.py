# map_text_viewer.py
# ✅ 맵/대사 빠른 확인용 두 번째 파이게임
#
# 조작
# - 1: casino_map.json 보기
# - 2: map_lab.json 보기
# - N: NPC 키 순환(대사 프리뷰)
# - ESC: 종료

import pygame
from settings import SCREEN_W, SCREEN_H, FONT_NAME, FPS
from level import Level

# npc.py의 DB를 그대로 가져와 글자 확인
try:
    from npc import DIALOGUE_DB
except Exception:
    DIALOGUE_DB = {}

def _sysfont(name, size):
    try:
        return pygame.font.SysFont(name, size)
    except Exception:
        return pygame.font.SysFont(None, size)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    font = _sysfont(FONT_NAME, 18)
    big = _sysfont(FONT_NAME, 22)

    map_files = ["casino_map.json", "map_lab.json"]
    map_index = 0

    level = Level(map_files[map_index])

    npc_keys = list(DIALOGUE_DB.keys())
    npc_i = 0 if npc_keys else -1

    camera_x = 0.0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False

                if e.key == pygame.K_1:
                    map_index = 0
                    level = Level(map_files[map_index])
                    camera_x = 0.0

                if e.key == pygame.K_2:
                    map_index = 1
                    level = Level(map_files[map_index])
                    camera_x = 0.0

                if e.key == pygame.K_n and npc_keys:
                    npc_i = (npc_i + 1) % len(npc_keys)

        # 간단 카메라 자동 스크롤(맵 전체 분위기 확인용)
        camera_x += 60 * dt
        if camera_x > max(0, level.world_w - SCREEN_W):
            camera_x = 0.0

        # ---- 렌더 ----
        level.draw(screen, camera_x)

        # ---- UI 패널 ----
        panel_h = 170
        panel = pygame.Surface((SCREEN_W, panel_h), pygame.SRCALPHA)
        panel.fill((10, 12, 18, 220))
        screen.blit(panel, (0, 0))

        # 맵 정보
        title = big.render("MAP + TEXT VIEWER", True, (250, 230, 170))
        screen.blit(title, (14, 10))

        info = [
            f"MAP FILE: {level.map_file}",
            f"Segments: {len(level.ground_segments)}",
            f"Walls: {len(level.walls)}",
            f"Props: {len(level.props)}",
            f"Photos: {len(level.photos)}",
            "Keys: 1 casino / 2 lab / N NPC text / ESC quit",
        ]

        for i, s in enumerate(info):
            img = font.render(s, True, (230, 230, 240))
            screen.blit(img, (14, 44 + i * 20))

        # NPC 대사 프리뷰
        if npc_i != -1:
            key = npc_keys[npc_i]
            cfg = DIALOGUE_DB.get(key, {})
            lbv = cfg.get("lines_by_visit", [])

            # 방문 1세트 앞부분만 미리보기
            preview_lines = []
            if isinstance(lbv, list) and lbv:
                for x in lbv[0][:4]:
                    if isinstance(x, str):
                        preview_lines.append(x)
            elif isinstance(lbv, dict) and 1 in lbv:
                for x in lbv[1][:4]:
                    if isinstance(x, str):
                        preview_lines.append(x)

            npc_title = font.render(f"NPC TEXT PREVIEW: {key}", True, (250, 230, 170))
            screen.blit(npc_title, (360, 44))

            for i, s in enumerate(preview_lines):
                img = font.render(f"- {s}", True, (220, 220, 230))
                screen.blit(img, (360, 70 + i * 20))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
