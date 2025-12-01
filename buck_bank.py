# buck_bank.py
from pygame.math import Vector2 as V2
from settings import TILE_SIZE
import map_system
from npc import NPC, BankNPC, SAMPLE_NODES

def _cc(r, c) -> V2:
    return V2((c - 0.5) * TILE_SIZE, (r - 0.5) * TILE_SIZE)

def load_from_city():
    map_system.set_current_map("bank")
    spawn = _cc(6, 4)  # 은행 내부 스폰
    npcs = [
        NPC("은행원", _cc(6, 6), color=(185,160,255),
            dialog_nodes=SAMPLE_NODES, start_node_id="start"),
        BankNPC(_cc(6, 3), direction="exit"),  # 도시로 나가는 출구
    ]
    return spawn, npcs
