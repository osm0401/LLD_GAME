# buck_city.py
from pygame.math import Vector2 as V2
from settings import TILE_SIZE
import map_system
from npc import NPC, BankNPC, SAMPLE_NODES

def _cc(r, c) -> V2:
    return V2((c - 0.5) * TILE_SIZE, (r - 0.5) * TILE_SIZE)

def load_default():
    map_system.set_current_map("city")
    spawn = _cc(6, 6)

    npcs = [
        NPC("연맹 파수꾼", _cc(6, 7), color=(120,170,255),
            dialog_nodes=SAMPLE_NODES, start_node_id="start"),
        NPC("상인 로웰", _cc(10, 4), color=(160,200,255),
            dialog_nodes=SAMPLE_NODES, start_node_id="start"),
        BankNPC(_cc(6, 8), direction="enter"),  # 은행으로 들어가는 NPC
    ]
    return spawn, npcs

def load_from_bank():
    # 은행 내부에서 나와서 도시로 복귀
    return load_default()
