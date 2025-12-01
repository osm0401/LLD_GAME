# map_system.py
import os, json, pygame
from pygame.math import Vector2 as V2
from settings import (
    SCREEN_W, SCREEN_H,
    TILE_SIZE, MAP_ROWS, MAP_COLS,
    WORLD_W, WORLD_H,
)

TILE_FOLDER = os.path.join("assets", "tiles")

CURRENT_MAP: str = "city"                   # set_current_map() 로 갱신
TILE_OVERRIDE: dict[tuple[int, int], str] = {}  # (r,c) -> path

_image_cache: dict[str, pygame.Surface | None] = {}
_missing_log_once: set[str] = set()

OVERRIDE_META = {
    "map": "city",
    "override_file": "",
    "tile_folder": "assets/tiles",
    "saved_at": None,
}

def _normalize_save_path(p: str) -> str: return p.replace("\\", "/").strip()
def _normalize_load_path(p: str) -> str: return os.path.normpath(p.strip())
def _override_path_for(name: str) -> str: return os.path.join(".", f"map_overrides_{name}.json")
def get_current_map_name() -> str: return CURRENT_MAP
def get_current_override_path() -> str: return _override_path_for(CURRENT_MAP)

def _build_meta(path: str) -> dict:
    import datetime as _dt
    return {
        "map": CURRENT_MAP,
        "override_file": os.path.basename(path),
        "tile_folder": _normalize_save_path(TILE_FOLDER),
        "saved_at": _dt.datetime.now().isoformat(timespec="seconds"),
    }

def get_override_meta() -> dict:
    return {"map": CURRENT_MAP, "file": os.path.basename(get_current_override_path()), "count": len(TILE_OVERRIDE)}

def set_current_map(map_name: str):
    global CURRENT_MAP
    CURRENT_MAP = map_name
    load_overrides()

def invalidate_cache(_cell: tuple[int,int] | None = None):
    _image_cache.clear()
    _missing_log_once.clear()

def save_overrides():
    """신규 포맷으로 저장: { _meta: {...}, overrides: { 'r,c': 'path' } }"""
    try:
        out = {f"{r},{c}": _normalize_save_path(p) for (r,c), p in TILE_OVERRIDE.items()}
        path = get_current_override_path()
        payload = {"_meta": _build_meta(path), "overrides": out}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        OVERRIDE_META.update(payload["_meta"])
        print(f"[map_system] overrides saved: {len(out)} cells -> {path}")
    except Exception as e:
        print("[map_system] overrides save failed:", e)

def load_overrides():
    """신규/구 포맷 자동 지원"""
    global TILE_OVERRIDE, OVERRIDE_META
    TILE_OVERRIDE.clear()
    invalidate_cache()
    path = get_current_override_path()
    OVERRIDE_META = _build_meta(path)

    if not os.path.exists(path):
        print(f"[map_system] {os.path.basename(path)} 없음 (오버라이드 없음)")
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict) and "_meta" in raw and "overrides" in raw:
            OVERRIDE_META.update(raw.get("_meta") or {})
            ov = raw.get("overrides") or {}
        else:
            ov = raw  # 구 포맷
        cnt = 0
        for k, v in ov.items():
            try:
                r, c = map(int, k.split(","))
                TILE_OVERRIDE[(r, c)] = _normalize_load_path(v)
                cnt += 1
            except Exception:
                pass
        print(f"[map_system] overrides loaded: {cnt} from {os.path.basename(path)}")
    except Exception as e:
        print("[map_system] overrides load failed:", e)

def get_cell_from_world(world_pos: V2):
    c = int(world_pos.x // TILE_SIZE) + 1
    r = int(world_pos.y // TILE_SIZE) + 1
    return (r, c) if (1 <= r <= MAP_ROWS and 1 <= c <= MAP_COLS) else None

def clamp_to_world(pos: V2) -> V2:
    return V2(max(0, min(WORLD_W, pos.x)), max(0, min(WORLD_H, pos.y)))

def _load_image_cached(path: str) -> pygame.Surface | None:
    if path in _image_cache: return _image_cache[path]
    try:
        if not os.path.exists(path):
            if path not in _missing_log_once:
                print(f"[map_system] 이미지 파일 없음: {path}")
                _missing_log_once.add(path)
            _image_cache[path] = None
            return None
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (TILE_SIZE, TILE_SIZE))
        _image_cache[path] = img
        return img
    except Exception:
        _image_cache[path] = None
        return None

def draw_background(surf: pygame.Surface, camera_offset: V2):
    surf.fill((17, 19, 24))
    top_left = -camera_offset
    bottom_right = V2(SCREEN_W, SCREEN_H) - camera_offset

    start_c = max(1, int(top_left.x // TILE_SIZE) + 1)
    end_c   = min(MAP_COLS, int(bottom_right.x // TILE_SIZE) + 1)
    start_r = max(1, int(top_left.y // TILE_SIZE) + 1)
    end_r   = min(MAP_ROWS, int(bottom_right.y // TILE_SIZE) + 1)

    for r in range(start_r, end_r + 1):
        for c in range(start_c, end_c + 1):
            path = TILE_OVERRIDE.get((r, c)) or os.path.join(TILE_FOLDER, f"{r}-{c}.png")
            img = _load_image_cached(path)
            if img is None: continue
            spos = V2((c - 1) * TILE_SIZE, (r - 1) * TILE_SIZE) + camera_offset
            surf.blit(img, spos)

    rect_screen = pygame.Rect(0, 0, WORLD_W, WORLD_H)
    rect_screen.topleft = camera_offset
    pygame.draw.rect(surf, (50, 58, 70), rect_screen, 1)
