# settings.py
# ---------------------------------------------------------
# 프로젝트 전체에서 공유하는 설정 값.
# 다른 파일들이 이 값을 임포트해 사용하므로
# "이름/의미"를 명확히 유지하는 게 중요하다.
# ---------------------------------------------------------

SCREEN_W = 960
SCREEN_H = 540
FPS = 60
FONT_NAME = "malgungothic"  # 또는 너가 쓰는 폰트 이름
PLAYER_SIZE = (32, 56)

# 폰트 이름(시스템에 없을 경우 None 폰트로 fallback)
FONT_NAME = "Malgun Gothic"

# 월드 크기(사이드뷰이므로 가로만 길게)
WORLD_W = 4800
WORLD_H = SCREEN_H

# 하늘/지면 색
SKY_TOP = (255, 210, 225)
SKY_BOTTOM = (255, 230, 240)
CLOUD = (250, 250, 255)

GROUND_LIGHT = (120, 110, 125)
GROUND_DARK = (90, 85, 98)
GROUND_Y = int(SCREEN_H * 0.78)

# 플레이어 이동
PLAYER_SIZE = (72,90)
PLAYER_MAX_SPEED = 260
PLAYER_ACCEL = 1200
PLAYER_FRICTION = 1600
# settings.py

PLAYER_SPRITE = "assets/characters/player.png"