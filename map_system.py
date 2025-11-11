# map_system.py
import os
import json
import pygame
from pygame.math import Vector2 as V2

from settings import (
    SCREEN_W, SCREEN_H,
    BG_CLEAR_COLOR,
    TILE_SIZE, MAP_ROWS, MAP_COLS,
    WORLD_W, WORLD_H,
)

TILE_FOLDER = "assets/tiles"

# ---- 여러 맵 지원 ----
# 예: "city", "bank" ...
CURRENT_MAP = "city"

def get_save_path() -> str:
    """
    현재 맵 이름에 따라 저장 파일 이름을 결정
    - city  -> map_overrides.json (기본 도시)
    - bank  -> map_overrides_bank.json
    - 그 외 -> map_overrides_<이름>.json
    """
    if CURRENT_MAP == "city":
        return "map_overrides.json"
    else:
        return f"map_overrides_{CURRENT_MAP}.json"


# 이미지 캐시 & 오버라이드 딕셔너리
_image_cache: dict[str, pygame.Surface | None] = {}
TILE_OVERRIDE: dict[tuple[int, int], str] = {}
_logged_draw_cells: set[tuple[int, int]] = set()


def invalidate_cache(path: str | None = None):
    """이미지 캐시 무효화 (path=None이면 전체 삭제)"""
    global _image_cache
    if path is None:
        _image_cache.clear()
    else:
        _image_cache.pop(path, None)


def load_overrides():
    """
    현재 CURRENT_MAP에 해당하는 map_overrides*.json -> TILE_OVERRIDE 로 불러오기
    JSON 예:
    {
      "(1,1)": "assets/tiles/1-1.png",
      "(6,6)": "assets/maps/just_white.png"
    }
    """
    TILE_OVERRIDE.clear()

    path = get_save_path()
    if not os.path.exists(path):
        print(f"[map_system] {path} 없음 (맵 '{CURRENT_MAP}' 오버라이드 없음)")
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        parsed: dict[tuple[int, int], str] = {}
        for k, v in raw.items():
            key = str(k).strip()  # "(1,1)" or "1,1"
            if key.startswith("(") and key.endswith(")"):
                key = key[1:-1]    # "1,1"

            r, c = map(int, key.split(","))
            path_str = str(v).strip()
            if path_str:
                parsed[(r, c)] = path_str

        TILE_OVERRIDE.update(parsed)
        _image_cache.clear()
        _logged_draw_cells.clear()
        print(f"[map_system] overrides loaded for map '{CURRENT_MAP}':", TILE_OVERRIDE)
    except Exception as e:
        print("[map_system] load_overrides error:", e)
        TILE_OVERRIDE.clear()


def save_overrides():
    """
    TILE_OVERRIDE -> 현재 맵의 map_overrides*.json 저장
    """
    try:
        data = {f"({r},{c})": path
                for (r, c), path in TILE_OVERRIDE.items()}
        path = get_save_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[map_system] overrides saved for map '{CURRENT_MAP}':", len(TILE_OVERRIDE), "cells")
    except Exception as e:
        print("[map_system] save_overrides error:", e)


def set_current_map(name: str):
    """
    맵 전환 함수
    - CURRENT_MAP 값을 바꾸고
    - 해당 맵의 오버라이드 json을 다시 로드
    """
    global CURRENT_MAP, _logged_draw_cells
    if name == CURRENT_MAP:
        return
    CURRENT_MAP = name
    print(f"[map_system] switching map to '{CURRENT_MAP}'")
    load_overrides()
    _logged_draw_cells.clear()


def load_image_cached(path: str) -> pygame.Surface | None:
    """타일 이미지 캐시 로딩"""
    if path in _image_cache:
        return _image_cache[path]

    try:
        if not os.path.exists(path):
            print("[map_system] 이미지 파일 없음:", path)
            _image_cache[path] = None
            return None

        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (TILE_SIZE, TILE_SIZE))
        _image_cache[path] = img
        return img
    except Exception as e:
        print("[map_system] load_image_cached error:", path, e)
        _image_cache[path] = None
        return None


def get_cell_from_world(world_pos: V2) -> tuple[int, int] | None:
    """월드 좌표 -> (행, 열) 셀 (1부터 시작)"""
    c = int(world_pos.x // TILE_SIZE) + 1
    r = int(world_pos.y // TILE_SIZE) + 1
    if 1 <= r <= MAP_ROWS and 1 <= c <= MAP_COLS:
        return (r, c)
    return None


def clamp_to_world(pos: V2) -> V2:
    """플레이어 / 클릭 좌표를 월드 범위 안으로 클램프"""
    return V2(
        max(0, min(WORLD_W, pos.x)),
        max(0, min(WORLD_H, pos.y)),
    )


def draw_background(surf: pygame.Surface, camera_offset: V2):
    """
    배경 타일 그리기

    - TILE_OVERRIDE[(r,c)] 가 있으면:
        그 값을 그대로 경로로 사용 (예: "assets/tiles/1-1.png")
    - 없으면 기본:
        assets/tiles/{r}-{c}.png
    """
    surf.fill(BG_CLEAR_COLOR)

    top_left_world = -camera_offset
    bottom_right_world = V2(SCREEN_W, SCREEN_H) - camera_offset

    start_c = max(1, int(top_left_world.x // TILE_SIZE) + 1)
    end_c   = min(MAP_COLS, int(bottom_right_world.x // TILE_SIZE) + 1)
    start_r = max(1, int(top_left_world.y // TILE_SIZE) + 1)
    end_r   = min(MAP_ROWS, int(bottom_right_world.y // TILE_SIZE) + 1)

    for r in range(start_r, end_r + 1):
        for c in range(start_c, end_c + 1):
            override_path = TILE_OVERRIDE.get((r, c))

            if override_path:
                path = os.path.normpath(override_path)
                if (r, c) not in _logged_draw_cells:
                    print(f"[map_system] draw override {(r, c)} -> {path}")
                    _logged_draw_cells.add((r, c))
            else:
                filename = f"{r}-{c}.png"
                path = os.path.join(TILE_FOLDER, filename)

            img = load_image_cached(path)
            if img is None:
                continue

            world_x = (c - 1) * TILE_SIZE
            world_y = (r - 1) * TILE_SIZE
            if 0 <= world_x < WORLD_W and 0 <= world_y < WORLD_H:
                spos = V2(world_x, world_y) + camera_offset
                surf.blit(img, spos)

    rect_screen = pygame.Rect(0, 0, WORLD_W, WORLD_H)
    rect_screen.topleft = camera_offset
    pygame.draw.rect(surf, (50, 58, 70), rect_screen, 1)
