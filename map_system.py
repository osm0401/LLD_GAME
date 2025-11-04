# map_system.py
import os, json, pygame
from pygame.math import Vector2 as V2
from settings import *

_image_cache = {}
TILE_OVERRIDE = {}

def load_overrides():
    global TILE_OVERRIDE
    if not os.path.exists(MAP_SAVE_PATH):
        return
    try:
        with open(MAP_SAVE_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        parsed = {}
        for k, v in raw.items():
            try:
                r, c = map(int, k.split(","))
                parsed[(r, c)] = v
            except:
                pass
        TILE_OVERRIDE = parsed
        _image_cache.clear()
    except:
        pass

def save_overrides():
    try:
        data = {f"{r},{c}": p for (r,c), p in TILE_OVERRIDE.items()}
        with open(MAP_SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def invalidate_cache(path: str):
    _image_cache.pop(path, None)

def load_image_cached(path: str):
    if path in _image_cache:
        return _image_cache[path]
    try:
        if not os.path.exists(path):
            _image_cache[path] = None
            return None
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (TILE_SIZE, TILE_SIZE))
        _image_cache[path] = img
        return img
    except:
        _image_cache[path] = None
        return None

def get_cell_from_world(world_pos: V2):
    c = int(world_pos.x // TILE_SIZE) + 1
    r = int(world_pos.y // TILE_SIZE) + 1
    if 1 <= r <= MAP_ROWS and 1 <= c <= MAP_COLS:
        return (r, c)
    return None

def draw_background(surf: pygame.Surface, camera_offset: V2):
    """에셋이 없어도 체크무늬를 그려서 빈 화면 방지"""
    surf.fill(BG_CLEAR_COLOR)

    top_left_world = -camera_offset
    bottom_right_world = V2(SCREEN_W, SCREEN_H) - camera_offset

    start_c = max(1, int(top_left_world.x // TILE_SIZE) + 1)
    end_c   = min(MAP_COLS, int(bottom_right_world.x // TILE_SIZE) + 1)
    start_r = max(1, int(top_left_world.y // TILE_SIZE) + 1)
    end_r   = min(MAP_ROWS, int(bottom_right_world.y // TILE_SIZE) + 1)

    for r in range(start_r, end_r + 1):
        for c in range(start_c, end_c + 1):
            path = TILE_OVERRIDE.get((r, c))
            if not path:
                path = os.path.join(TILE_FOLDER, f"{r}-{c}.png")
            img = load_image_cached(path)
            world_x = (c - 1) * TILE_SIZE
            world_y = (r - 1) * TILE_SIZE
            spos = V2(world_x, world_y) + camera_offset

            if img is not None:
                surf.blit(img, spos)
            else:
                # 체크무늬(에셋 없는 칸)
                rect = pygame.Rect(spos.x, spos.y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(surf, (28, 32, 40), rect)
                # 얇은 그리드
                pygame.draw.rect(surf, (50, 58, 70), rect, 1)

    # 월드 경계선
    rect_screen = pygame.Rect(0, 0, WORLD_W, WORLD_H)
    rect_screen.topleft = camera_offset
    pygame.draw.rect(surf, (80, 90, 105), rect_screen, 1)

def clamp_to_world(pos: V2) -> V2:
    return V2(max(0, min(WORLD_W, pos.x)), max(0, min(WORLD_H, pos.y)))
