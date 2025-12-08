# map_system.py
"""
타일맵 렌더링 + 맵별 오버라이드 + 충돌(벽) 블록 관리 모듈

섹션 순서
1) 설정/전역상태 (settings 안전 임포트 포함)
2) 경로 유틸 (_norm, _override_path, _blocks_path)
3) 맵 전환 API (set_current_map, get_current_map)
4) 타일 오버라이드 API (load_overrides, save_overrides, get_override_meta)
5) 벽(충돌) API (load_blocks, save_blocks, toggle_block_at_world 등)
6) 좌표/그리드 유틸 (get_cell_from_world, clamp_to_world)
7) 렌더링 (load_image_cached, draw_background, draw_blocks_overlay)
8) 충돌 (_circle_rect_intersect, collides_circle)
"""

from __future__ import annotations
import os, json
from typing import Dict, Tuple, Optional, Set

import pygame
from pygame.math import Vector2 as V2

# ============================================================================
# 1) 설정/전역상태: settings 안전 임포트 + 기본값
# ============================================================================
try:
    import settings as S
except Exception as e:
    raise RuntimeError("settings.py 임포트 실패") from e

SCREEN_W   = getattr(S, "SCREEN_W", 960)
SCREEN_H   = getattr(S, "SCREEN_H", 540)
TILE_SIZE  = getattr(S, "TILE_SIZE", 256)
MAP_ROWS   = getattr(S, "MAP_ROWS", 12)
MAP_COLS   = getattr(S, "MAP_COLS", 12)
WORLD_W    = getattr(S, "WORLD_W", MAP_COLS * TILE_SIZE)
WORLD_H    = getattr(S, "WORLD_H", MAP_ROWS * TILE_SIZE)
BG_CLEAR_COLOR = getattr(S, "BG_CLEAR_COLOR", (17, 19, 24))
BLOCK_SIZE = getattr(S, "BLOCK_SIZE", 32)
TILE_FOLDER = getattr(S, "TILE_FOLDER", "assets/tiles")  # 기본 타일 폴더

# 현재 맵 id / 활성 타일 폴더
CURRENT_MAP_ID: str = "city"
ACTIVE_TILE_FOLDER: str = TILE_FOLDER

# 타일 오버라이드, 이미지 캐시, 벽 블록, 오버라이드 메타
TILE_OVERRIDE: Dict[Tuple[int, int], str] = {}
_image_cache: Dict[str, Optional[pygame.Surface]] = {}
BLOCKS: Set[Tuple[int, int]] = set()
OVERRIDE_META: dict = {}  # {"map":..., "override_file":..., "tile_folder":...}


# ============================================================================
# 2) 경로 유틸
# ============================================================================
def _norm(path: str) -> str:
    """경로 구분자를 / 로 통일."""
    return path.replace("\\", "/")

def _override_path(map_id: str) -> str:
    """오버라이드 JSON 경로."""
    return f"map_overrides_{map_id}.json"

def _blocks_path(map_id: str) -> str:
    """벽(블록) JSON 경로."""
    return f"map_blocks_{map_id}.json"

# ============================================================================
# 3) 맵 전환 API
# ============================================================================
def set_current_map(map_id: str, *, tile_folder: Optional[str] = None, autoload: bool = True) -> None:
    """
    현재 맵 지정 + 필요 시 데이터 자동 로드.
    """
    global CURRENT_MAP_ID, ACTIVE_TILE_FOLDER, TILE_OVERRIDE, BLOCKS, _image_cache, OVERRIDE_META
    CURRENT_MAP_ID = map_id
    if tile_folder is not None:
        ACTIVE_TILE_FOLDER = tile_folder

    # 캐시/상태 초기화
    TILE_OVERRIDE.clear()
    _image_cache.clear()
    BLOCKS.clear()
    OVERRIDE_META.clear()

    if autoload:
        load_overrides(CURRENT_MAP_ID)
        load_blocks(CURRENT_MAP_ID)

    print(f"[map_system] current map -> {CURRENT_MAP_ID}, tiles={ACTIVE_TILE_FOLDER}")

def get_current_map() -> str:
    return CURRENT_MAP_ID


# ============================================================================
# 4) 타일 오버라이드 API
# ============================================================================
def _ensure_meta_defaults(map_id: str, meta: dict | None) -> dict:
    """오버라이드 메타 누락 필드 기본값 + 호환 키(file) + count 채우기."""
    m = dict(meta or {})
    if "map" not in m:
        m["map"] = map_id
    if "override_file" not in m:
        m["override_file"] = _override_path(map_id)
    if "tile_folder" not in m:
        m["tile_folder"] = ACTIVE_TILE_FOLDER

    # ▼ main.py 호환을 위한 alias와 카운트 추가
    if "file" not in m:
        m["file"] = m["override_file"]          # alias
    m["count"] = len(TILE_OVERRIDE)             # 현재 로드된 셀 수

    return m

def get_override_meta(map_id: str | None = None) -> dict:
    """
    현재 메모리에 로드된 오버라이드 메타 반환.
    파일이 없거나 아직 로드 전이어도 기본값으로 반환.
    """
    if OVERRIDE_META:
        return dict(OVERRIDE_META)
    mid = map_id or CURRENT_MAP_ID
    return _ensure_meta_defaults(mid, None)

def load_overrides(map_id: Optional[str] = None) -> None:
    """
    오버라이드 JSON 로드. 최신 포맷:
    {"_meta": {...}, "overrides": {"r,c": "assets/.../x.png", ...}}
    구형 포맷도 호환 처리.
    """
    global TILE_OVERRIDE, _image_cache, OVERRIDE_META
    TILE_OVERRIDE.clear()
    _image_cache.clear()

    mid = map_id or CURRENT_MAP_ID
    path = _override_path(mid)
    if not os.path.exists(path):
        print(f"[map_system] {path} 없음 (오버라이드 없음)")
        OVERRIDE_META = _ensure_meta_defaults(mid, None)
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        data = raw.get("overrides", raw)  # 구형 호환
        cnt = 0
        for k, v in data.items():
            try:
                r, c = map(int, k.split(","))
                TILE_OVERRIDE[(r, c)] = _norm(v)
                cnt += 1
            except Exception:
                pass

        meta_in = raw.get("_meta", {})
        OVERRIDE_META = _ensure_meta_defaults(mid, meta_in)
        print(f"[map_system] overrides loaded: {cnt}")
    except Exception as e:
        print("[map_system] overrides load error:", e)
        OVERRIDE_META = _ensure_meta_defaults(mid, None)

def save_overrides(map_id: Optional[str] = None) -> None:
    """현재 오버라이드 상태를 JSON으로 저장(메타 동기화 포함)."""
    global OVERRIDE_META
    mid = map_id or CURRENT_MAP_ID
    out_map = {f"{r},{c}": _norm(p) for (r, c), p in TILE_OVERRIDE.items()}

    meta = _ensure_meta_defaults(mid, {
        "map": mid,
        "override_file": _override_path(mid),
        "tile_folder": ACTIVE_TILE_FOLDER,
    })
    payload = {"_meta": meta, "overrides": out_map}

    try:
        with open(_override_path(mid), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        OVERRIDE_META = dict(meta)
        print(f"[map_system] overrides saved: {len(out_map)} cells -> {_override_path(mid)}")
    except Exception as e:
        print("[map_system] overrides save error:", e)


# ============================================================================
# 5) 벽(충돌) API
# ============================================================================
def load_blocks(map_id: Optional[str] = None) -> None:
    """벽(충돌) JSON 로드. 포맷: {"blocks":[[bx,by],...], "_meta":{...}}"""
    global BLOCKS
    BLOCKS.clear()
    mid = map_id or CURRENT_MAP_ID
    path = _blocks_path(mid)
    if not os.path.exists(path):
        print(f"[map_system] {path} 없음 (블록 없음)")
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        for pair in raw.get("blocks", []):
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                bx, by = int(pair[0]), int(pair[1])
                BLOCKS.add((bx, by))
        print(f"[map_system] blocks loaded: {len(BLOCKS)}")
    except Exception as e:
        print("[map_system] blocks load error:", e)

def save_blocks(map_id: Optional[str] = None) -> None:
    """벽(충돌) JSON 저장."""
    mid = map_id or CURRENT_MAP_ID
    data = {
        "_meta": {"map": mid, "block_size": BLOCK_SIZE},
        "blocks": [[bx, by] for (bx, by) in sorted(BLOCKS)],
    }
    try:
        with open(_blocks_path(mid), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[map_system] blocks saved: {len(BLOCKS)} -> {_blocks_path(mid)}")
    except Exception as e:
        print("[map_system] blocks save error:", e)

def world_to_block(world_pos: V2) -> Tuple[int, int]:
    """월드 좌표 → 블록 격자(bx,by)."""
    bx = int(world_pos.x // BLOCK_SIZE)
    by = int(world_pos.y // BLOCK_SIZE)
    return (bx, by)

def toggle_block_at_world(world_pos: V2, set_to: Optional[bool] = None) -> None:
    """
    에디터에서 클릭 시 블록 토글/설정.
    set_to=None: 토글, True: 강제 추가, False: 강제 제거
    """
    bx, by = world_to_block(world_pos)
    if set_to is None:
        if (bx, by) in BLOCKS:
            BLOCKS.remove((bx, by))
        else:
            BLOCKS.add((bx, by))
    else:
        if set_to:
            BLOCKS.add((bx, by))
        else:
            BLOCKS.discard((bx, by))


# ============================================================================
# 6) 좌표/그리드 유틸
# ============================================================================
def get_cell_from_world(world_pos: V2) -> Optional[Tuple[int, int]]:
    """월드 좌표 → 타일 셀 (r,c) (1-base). 범위 밖이면 None."""
    c = int(world_pos.x // TILE_SIZE) + 1
    r = int(world_pos.y // TILE_SIZE) + 1
    if 1 <= r <= MAP_ROWS and 1 <= c <= MAP_COLS:
        return (r, c)
    return None

def clamp_to_world(pos: V2) -> V2:
    """월드 영역(0~WORLD_W/H) 내부로 위치 클램프."""
    return V2(max(0, min(WORLD_W, pos.x)), max(0, min(WORLD_H, pos.y)))


# ============================================================================
# 7) 렌더링
# ============================================================================
def load_image_cached(path: str) -> Optional[pygame.Surface]:
    """
    경로의 이미지를 캐시 후 반환. 없거나 에러면 None 캐싱.
    로드 시 TILE_SIZE로 리샘플링(smoothscale).
    """
    path = _norm(path)
    if path in _image_cache:
        return _image_cache[path]

    if not os.path.exists(path):
        print(f"[map_system] 이미지 파일 없음: {path}")
        _image_cache[path] = None
        return None

    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (TILE_SIZE, TILE_SIZE))
        _image_cache[path] = img
        return img
    except Exception as e:
        print("[map_system] load image err:", path, e)
        _image_cache[path] = None
        return None

def draw_background(surf: pygame.Surface, camera_offset: V2) -> None:
    """
    화면에 보이는 범위만 타일을 그린다.
    - 오버라이드 우선, 없으면 ACTIVE_TILE_FOLDER/{r}-{c}.png
    - 월드 외곽 라인 렌더
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
            path = TILE_OVERRIDE.get((r, c))
            if not path:
                path = os.path.join(ACTIVE_TILE_FOLDER, f"{r}-{c}.png")
            img = load_image_cached(path)
            if img is None:
                continue
            world_x = (c - 1) * TILE_SIZE
            world_y = (r - 1) * TILE_SIZE
            surf.blit(img, V2(world_x, world_y) + camera_offset)

    # 월드 외곽 테두리
    rect_screen = pygame.Rect(0, 0, WORLD_W, WORLD_H)
    rect_screen.topleft = camera_offset
    pygame.draw.rect(surf, (50, 58, 70), rect_screen, 1)

def draw_blocks_overlay(surf: pygame.Surface, camera_offset: V2, *, alpha: int = 120) -> None:
    """에디터: 화면에 보이는 블록(벽)만 붉은 반투명으로 오버레이."""
    view = pygame.Rect(-camera_offset.x, -camera_offset.y, SCREEN_W, SCREEN_H)
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    color_fill = (220, 60, 60, alpha)
    color_line = (240, 90, 90)

    bx0 = max(0, int(view.left  // BLOCK_SIZE))
    by0 = max(0, int(view.top   // BLOCK_SIZE))
    bx1 = min(int(WORLD_W // BLOCK_SIZE), int(view.right  // BLOCK_SIZE))
    by1 = min(int(WORLD_H // BLOCK_SIZE), int(view.bottom // BLOCK_SIZE))

    for by in range(by0, by1 + 1):
        for bx in range(bx0, bx1 + 1):
            if (bx, by) in BLOCKS:
                rx = bx * BLOCK_SIZE + camera_offset.x
                ry = by * BLOCK_SIZE + camera_offset.y
                rect = pygame.Rect(rx, ry, BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(overlay, color_fill, rect)
                pygame.draw.rect(overlay, color_line, rect, 1)

    surf.blit(overlay, (0, 0))


# ============================================================================
# 8) 충돌
# ============================================================================
def _circle_rect_intersect(cx: float, cy: float, cr: float,
                           rx: float, ry: float, rw: float, rh: float) -> bool:
    """원(플레이어) - 사각형(벽블록) 충돌 판정."""
    nx = max(rx, min(cx, rx + rw))
    ny = max(ry, min(cy, ry + rh))
    dx, dy = cx - nx, cy - ny
    return (dx * dx + dy * dy) <= (cr * cr)

def collides_circle(pos: V2, radius: float) -> bool:
    """
    현재 원(pos, radius)이 BLOCKS 중 하나와 교차하는지 검사.
    가까운 후보 블록만 검사하여 성능 유지.
    """
    bx0 = max(0, int((pos.x - radius) // BLOCK_SIZE))
    by0 = max(0, int((pos.y - radius) // BLOCK_SIZE))
    bx1 = min(int(WORLD_W // BLOCK_SIZE), int((pos.x + radius) // BLOCK_SIZE))
    by1 = min(int(WORLD_H // BLOCK_SIZE), int((pos.y + radius) // BLOCK_SIZE))

    for by in range(by0, by1 + 1):
        for bx in range(bx0, bx1 + 1):
            if (bx, by) in BLOCKS:
                rx, ry = bx * BLOCK_SIZE, by * BLOCK_SIZE
                if _circle_rect_intersect(pos.x, pos.y, radius, rx, ry, BLOCK_SIZE, BLOCK_SIZE):
                    return True
    return False
