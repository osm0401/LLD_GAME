# buck_bank.py
from pygame.math import Vector2 as V2

import map_system
from settings import TILE_SIZE
from npc import BankNPC


MAP_NAME = "bank"

# 은행 내부에서 '도시로 나가는 문'이 있는 셀
EXIT_DOOR_CELL = (6, 6)


def _cell_center(row: int, col: int) -> V2:
    return V2((col - 0.5) * TILE_SIZE, (row - 0.5) * TILE_SIZE)


# 도시에서 은행으로 들어왔을 때 설 위치
BANK_SPAWN_FROM_CITY = _cell_center(7, 6)


def _create_npcs_for_bank() -> list:
    """
    은행 내부 맵에서 사용할 NPC 리스트.
    - 출구 BankNPC 1개
    """
    npcs: list = []

    exit_pos = _cell_center(*EXIT_DOOR_CELL)
    exit_npc = BankNPC(exit_pos, direction="exit",
                       sprite_path="assets/sprites/bank_npc.png")
    npcs.append(exit_npc)

    return npcs


def load_from_city() -> tuple[V2, list]:
    """
    도시에서 은행으로 들어올 때 호출.
    - CURRENT_MAP = "bank"
    - 은행 내부 오버라이드 로딩
    - 은행 내부 스폰 위치 + 은행 내부 NPC 리스트 반환
    """
    map_system.set_current_map(MAP_NAME)
    spawn = BANK_SPAWN_FROM_CITY
    npcs = _create_npcs_for_bank()
    return spawn, npcs
