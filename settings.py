# settings.py — 사이드뷰 공용 설정

SCREEN_W, SCREEN_H = 960, 540
FPS = 60

# 월드 크기(가로로 긴 사이드뷰)
WORLD_W = 4800
WORLD_H = SCREEN_H

# 플레이어/물리
PLAYER_SIZE = (36, 52)
PLAYER_MAX_SPEED = 320.0      # 좌우 최고 속도(px/s)
PLAYER_ACCEL = 2000.0         # 가속도
PLAYER_FRICTION = 1800.0      # 가속 입력이 없을 때 감속

# 지면
GROUND_Y = SCREEN_H - 120     # 기본 지면 높이(px)

# 색상 팔레트(따뜻한 핑크 하늘 느낌)
SKY_TOP = (255, 190, 210)
SKY_BOTTOM = (255, 220, 230)
CLOUD = (255, 245, 250)
GROUND_DARK = (90, 76, 88)
GROUND_LIGHT = (120, 102, 118)

FONT_NAME = "malgungothic"    # 윈도우라면 말굿고딕, 없으면 자동 대체
