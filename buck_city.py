# buck_city.py
from pygame.math import Vector2 as V2

import map_system
from settings import WORLD_W, WORLD_H, TILE_SIZE
from npc import NPC, BankNPC, SAMPLE_NODES


MAP_NAME = "city"

# 도시에서 은행 입구가 있는 셀 (예시)
BANK_DOOR_CELL = (6, 6)


def _cell_center(row: int, col: int) -> V2:
    """(행, 열) 셀의 중앙 월드 좌표."""
    return V2((col - 0.5) * TILE_SIZE, (row - 0.5) * TILE_SIZE)


# 플레이어 스폰 위치들
CITY_SPAWN_DEFAULT = V2(WORLD_W / 2, WORLD_H / 2)       # 게임 처음 시작 위치
CITY_SPAWN_FROM_BANK = _cell_center(7, 6)               # 은행에서 나왔을 때 설 자리


def _create_npcs_for_city() -> list:
    """
    도시 맵에서 사용할 NPC들을 만들어 반환.
    - 사람 NPC 예시 1명
    - 은행 입구 BankNPC 1개
    """
    npcs: list = []

    # 예시: 이야기해주는 시민 NPC
    citizen_pos = _cell_center(5, 5)
    citizen = NPC(
        name="엘테리아 시민",
        world_pos=citizen_pos,
        dialog_nodes=SAMPLE_NODES,
        start_node_id="start",
    )
    npcs.append(citizen)

    # 은행 입구 NPC (은행 건물)
    bank_pos = _cell_center(*BANK_DOOR_CELL)
    bank_npc = BankNPC(bank_pos, direction="enter",
                       sprite_path="assets/sprites/bank_npc.png")
    npcs.append(bank_npc)

    return npcs


def load_default() -> tuple[V2, list]:
    """
    게임 처음 시작할 때 도시 맵 로딩.
    - CURRENT_MAP = "city"
    - 도시 오버라이드 로딩
    - 플레이어 스폰 위치 + 도시 NPC 리스트 반환
    """
    map_system.set_current_map(MAP_NAME)
    # set_current_map 안에서 load_overrides() 호출된다고 가정
    spawn = CITY_SPAWN_DEFAULT
    npcs = _create_npcs_for_city()
    return spawn, npcs


def load_from_bank() -> tuple[V2, list]:
    """
    은행 내부에서 도시로 돌아올 때 호출.
    - CURRENT_MAP = "city"
    - 도시 오버라이드 로딩
    - 은행 출구 근처 스폰 위치 + 도시 NPC 리스트 반환
    """
    map_system.set_current_map(MAP_NAME)
    spawn = CITY_SPAWN_FROM_BANK
    npcs = _create_npcs_for_city()
    return spawn, npcs
