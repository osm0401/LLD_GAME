# settings.py
from pygame.math import Vector2 as V2

# -------- 화면/성능 --------
SCREEN_W, SCREEN_H = 960, 540
CENTER = V2(SCREEN_W // 2, SCREEN_H // 2)
FPS = 60

# -------- 플레이어 --------
PLAYER_SPEED = 240.0
PLAYER_RADIUS = 14
FONT_NAME = "malgungothic"     # 대체 폰트 자동 적용됨

# -------- 타일/맵 --------
TILE_SIZE = 256
MAP_ROWS = 12
MAP_COLS = 12
WORLD_W, WORLD_H = MAP_COLS * TILE_SIZE, MAP_ROWS * TILE_SIZE

# -------- NPC/상호작용 --------
NPC_RADIUS = 14
INTERACT_DISTANCE = 90.0

# -------- 에디터 UI (작게) --------
EDITOR_INPUT_HEIGHT = 28
EDITOR_INPUT_PADDING = 8
EDITOR_SELECT_INSET = 6
EDITOR_SELECT_BORDER = 2
