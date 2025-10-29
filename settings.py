# settings.py
import math
from pygame.math import Vector2 as V2

# ---- 디버그 ----
DEBUG = True  # True면 키 입력/이벤트/경로 등 콘솔에 로그

# ---- 화면/플레이어 ----
SCREEN_W, SCREEN_H = 960, 540
CENTER = V2(SCREEN_W // 2, SCREEN_H // 2)
FPS = 60

PLAYER_SPEED = 240.0
PLAYER_RADIUS = 14

BG_CLEAR_COLOR = (17, 19, 24)
# 폰트 이름이 없거나 OS에 없으면 기본 폰트로 대체
FONT_NAME = "malgungothic"  # 없으면 main에서 fallback 사용

# ---- 타일/맵 ----
TILE_SIZE = 256
MAP_ROWS = 12
MAP_COLS = 12
TILE_FOLDER = "assets/tiles"
WORLD_W, WORLD_H = MAP_COLS * TILE_SIZE, MAP_ROWS * TILE_SIZE
MAP_SAVE_PATH = "map_overrides.json"

# ---- NPC/상호작용 ----
INTERACT_DISTANCE = 90          # 근접 판정 넉넉히
INTERACT_FOV_DEG = 70
INTERACT_FOV_COS = math.cos(math.radians(INTERACT_FOV_DEG))
NPC_RADIUS = 16
