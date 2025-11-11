# buck_city.py
from pygame.math import Vector2 as V2
from settings import WORLD_W, WORLD_H, TILE_SIZE
import map_system

# 이 맵의 내부 이름 (json 파일 구분용)
MAP_NAME = "city"

# 도시에서 은행 입구가 있는 셀 (예시: 6행 6열)
BANK_DOOR_CELL = (6, 6)


def _cell_center(row: int, col: int) -> V2:
    return V2((col - 0.5) * TILE_SIZE, (row - 0.5) * TILE_SIZE)


# 도시에서 게임 시작할 때 스폰 위치
DEFAULT_SPAWN = V2(WORLD_W / 2, WORLD_H / 2)

# 은행 내부에서 나와서 도시로 돌아올 때 설 위치
SPAWN_FROM_BANK = _cell_center(7, 6)


def load_default() -> V2:
    """
    게임 시작 시 도시 맵 로딩.
    - CURRENT_MAP을 "city"로 바꾸고
    - map_overrides.json을 읽어서 TILE_OVERRIDE 채움
    - 플레이어 시작 위치 반환
    """
    map_system.set_current_map(MAP_NAME)
    return DEFAULT_SPAWN.copy()


def load_from_bank() -> V2:
    """
    은행 내부에서 도시로 나올 때.
    - CURRENT_MAP을 "city"로 바꾸고
    - 도시 오버라이드 로딩
    - 은행 출구 근처 위치 반환
    """
    map_system.set_current_map(MAP_NAME)
    return SPAWN_FROM_BANK.copy()
