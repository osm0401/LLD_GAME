# key.py
# ---------------------------------------------------------
# 게임 전체에서 쓰는 키 설정을 한 곳에서 관리하는 모듈.
#
# 방법:
#   - *_NAME 부분만 고치면 키를 바꿀 수 있음
#   - 코드에서는 아래 정의된 상수 (INTERACT, JUMP, INVENTORY 등)를 사용
# ---------------------------------------------------------

import pygame

# -----------------------------
# 1) 사람이 보기 좋은 이름(문자열)
#    → 여기만 바꿔도 전체 키가 바뀜
# -----------------------------
MOVE_LEFT_NAME = "A"
MOVE_RIGHT_NAME = "D"
MOVE_UP_NAME = "W"      # 탑다운 위로
MOVE_DOWN_NAME = "S"    # 탑다운 아래로

CONTINUE_TALK_NAME = "SPACE"
INTERACT_NAME = "F"     # 상호작용(대화, 워프 등)
JUMP_SPACE_NAME = "SPACE"     # 점프
JUMP_W_NAME = "W"
INVENTORY_NAME = "E"    # 인벤토리

# 필요하면 나중에 추가 가능:
# PAUSE_NAME = "ESC"
# etc.

# -----------------------------
# 2) 문자열 → pygame 키코드 매핑
# -----------------------------
_NAME_TO_KEY = {
    "A": pygame.K_a,
    "B": pygame.K_b,
    "C": pygame.K_c,
    "D": pygame.K_d,
    "E": pygame.K_e,
    "F": pygame.K_f,
    "G": pygame.K_g,
    "H": pygame.K_h,
    "I": pygame.K_i,
    "J": pygame.K_j,
    "K": pygame.K_k,
    "L": pygame.K_l,
    "M": pygame.K_m,
    "N": pygame.K_n,
    "O": pygame.K_o,
    "P": pygame.K_p,
    "Q": pygame.K_q,
    "R": pygame.K_r,
    "S": pygame.K_s,
    "T": pygame.K_t,
    "U": pygame.K_u,
    "V": pygame.K_v,
    "W": pygame.K_w,
    "X": pygame.K_x,
    "Y": pygame.K_y,
    "Z": pygame.K_z,

    "SPACE": pygame.K_SPACE,
    "ESC": pygame.K_ESCAPE,

    "UP": pygame.K_UP,
    "DOWN": pygame.K_DOWN,
    "LEFT": pygame.K_LEFT,
    "RIGHT": pygame.K_RIGHT,

}

def _key(name: str, fallback):
    """문자열 이름을 pygame 키코드로 변환. 실패하면 fallback 사용."""
    if not isinstance(name, str):
        return fallback
    return _NAME_TO_KEY.get(name.upper(), fallback)

# -----------------------------
# 3) 실제로 코드에서 쓸 상수들
# -----------------------------
MOVE_LEFT = _key(MOVE_LEFT_NAME, pygame.K_a)
MOVE_RIGHT = _key(MOVE_RIGHT_NAME, pygame.K_d)
MOVE_UP = _key(MOVE_UP_NAME, pygame.K_w)
MOVE_DOWN = _key(MOVE_DOWN_NAME, pygame.K_s)

INTERACT = _key(INTERACT_NAME, pygame.K_f)
CONTINUE_TALK = _key(CONTINUE_TALK_NAME, pygame.K_SPACE)
JUMP_SPACE = _key(JUMP_SPACE_NAME, pygame.K_SPACE)
JUMP_W = _key(JUMP_W_NAME, pygame.K_w)

INVENTORY = _key(INVENTORY_NAME, pygame.K_e)

# 이름 문자열도 UI에 쓸 수 있게 공개
"""__all__ = [
    "MOVE_LEFT", "MOVE_RIGHT", "MOVE_UP", "MOVE_DOWN",
    "INTERACT", "JUMP_SPACE", "INVENTORY",
    "MOVE_LEFT_NAME", "MOVE_RIGHT_NAME", "MOVE_UP_NAME", "MOVE_DOWN_NAME",
    "INTERACT_NAME", "JUMP_SPACE_NAME", "INVENTORY_NAME","JUMP_W_NAME",
]
"""