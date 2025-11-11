# buck_bank.py
from pygame.math import Vector2 as V2
from settings import TILE_SIZE
import map_system

# 이 맵의 내부 이름 (json 파일 구분용)
MAP_NAME = "bank"

# 은행 내부에서 출구 문이 있는 셀 (은행 안 기준)
EXIT_DOOR_CELL = (6, 6)


def _cell_center(row: int, col: int) -> V2:
    return V2((col - 0.5) * TILE_SIZE, (row - 0.5) * TILE_SIZE)


# 도시에서 은행으로 들어왔을 때, 은행 내부 스폰 위치
SPAWN_FROM_CITY = _cell_center(7, 6)


def load_from_city() -> V2:
    """
    도시에서 은행으로 들어올 때.
    - CURRENT_MAP을 "bank"로 바꾸고
    - map_overrides_bank.json을 읽어서 TILE_OVERRIDE 채움
    - 은행 내부 스폰 위치 반환
    """
    map_system.set_current_map(MAP_NAME)
    return SPAWN_FROM_CITY.copy()
