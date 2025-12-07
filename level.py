# level.py
from __future__ import annotations
import os, json
import pygame
from pygame.math import Vector2 as V2
import settings as S

SCREEN_W = S.SCREEN_W
SCREEN_H = S.SCREEN_H
WORLD_W  = S.WORLD_W
WORLD_H  = S.WORLD_H

GROUND_LIGHT = S.GROUND_LIGHT
GROUND_DARK  = S.GROUND_DARK


class Level:
    def __init__(self, map_file: str):
        self.map_file = map_file

        self.world_w = WORLD_W
        self.world_h = WORLD_H

        # ✅ 맵별 하늘색(기본은 settings)
        self.sky_top = S.SKY_TOP
        self.sky_bottom = S.SKY_BOTTOM

        self.ground_segments: list[tuple[int, int]] = []
        self.walls: list[pygame.Rect] = []
        self.props: list[dict] = []
        self.photos: list[dict] = []
        self._photo_cache: dict[tuple[str, int, int], pygame.Surface | None] = {}

        self.wall_grid = {
            "cols": 5,
            "rows": 3,
            "cell": 80,
            "origin": V2(1200, 180),
        }
        self.wall_cells: set[tuple[int, int]] = set()

        self.load_map(self.map_file)

    # ----------------------------
    # JSON I/O
    # ----------------------------
    def load_map(self, map_file: str | None = None) -> None:
        if map_file:
            self.map_file = map_file

        self.ground_segments.clear()
        self.walls.clear()
        self.props.clear()
        self.photos.clear()
        self.wall_cells.clear()
        self._photo_cache.clear()

        if not os.path.exists(self.map_file):
            raise FileNotFoundError(f"[Level] 맵 파일 없음: {self.map_file}")

        with open(self.map_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data.get("_meta", {})

        self.world_w = int(meta.get("world_w", self.world_w))
        self.world_h = int(meta.get("world_h", self.world_h))

        # ✅ 맵별 하늘색 오버라이드
        st = meta.get("sky_top")
        sb = meta.get("sky_bottom")
        if isinstance(st, (list, tuple)) and len(st) == 3:
            self.sky_top = (int(st[0]), int(st[1]), int(st[2]))
        if isinstance(sb, (list, tuple)) and len(sb) == 3:
            self.sky_bottom = (int(sb[0]), int(sb[1]), int(sb[2]))

        for p in data.get("ground_segments", []):
            if isinstance(p, (list, tuple)) and len(p) == 2:
                self.ground_segments.append((int(p[0]), int(p[1])))

        if not self.ground_segments:
            raise ValueError("[Level] ground_segments 비어있음")

        for w in data.get("walls", []):
            r = pygame.Rect(int(w["x"]), int(w["y"]), int(w["w"]), int(w["h"]))
            self.walls.append(r)

        for p in data.get("props", []):
            r = pygame.Rect(int(p["x"]), int(p["y"]), int(p["w"]), int(p["h"]))
            self.props.append({
                "rect": r,
                "solid": bool(p.get("solid", True)),
                "name": p.get("name", ""),
            })

        for ph in data.get("photos", []):
            self.photos.append({
                "x": int(ph.get("x", 0)),
                "y": int(ph.get("y", 0)),
                "w": int(ph.get("w", 96)),
                "h": int(ph.get("h", 96)),
                "path": str(ph.get("path", "")),
            })

        self._apply_wall_grid_from_json(data)
        if self.wall_cells:
            self.rebuild_walls_from_grid()

        print(f"[Level] {self.map_file} 로드 완료")

    def save_map(self, map_file: str | None = None) -> None:
        if map_file:
            self.map_file = map_file

        data = {
            "_meta": {
                "id": os.path.splitext(os.path.basename(self.map_file))[0],
                "world_w": self.world_w,
                "world_h": self.world_h,
                # ✅ 현재 하늘색도 저장
                "sky_top": list(self.sky_top),
                "sky_bottom": list(self.sky_bottom),
            },
            "ground_segments": [[x, y] for (x, y) in self.ground_segments],
            "walls": [{"x": r.x, "y": r.y, "w": r.w, "h": r.h} for r in self.walls],
            "props": [
                {
                    "x": d["rect"].x, "y": d["rect"].y,
                    "w": d["rect"].w, "h": d["rect"].h,
                    "solid": bool(d.get("solid", True)),
                    "name": d.get("name", ""),
                }
                for d in self.props
            ],
            "photos": list(self.photos),
            "wall_grid": {
                "cols": self.wall_grid["cols"],
                "rows": self.wall_grid["rows"],
                "cell": self.wall_grid["cell"],
                "origin": [int(self.wall_grid["origin"].x), int(self.wall_grid["origin"].y)],
            },
            "wall_cells": [[c, r] for (c, r) in sorted(self.wall_cells)],
        }

        with open(self.map_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[Level] map saved -> {self.map_file}")

    # ----------------------------
    # 지면/서포트
    # ----------------------------
    def surface_y_rect_x(self, world_x: int) -> int:
        segs = self.ground_segments
        if world_x <= segs[0][0]:
            return segs[0][1]
        if world_x >= segs[-1][0]:
            return segs[-1][1]

        for i in range(len(segs) - 1):
            x0, y0 = segs[i]
            x1, y1 = segs[i + 1]
            if x0 <= world_x <= x1:
                denom = max(1, x1 - x0)
                t = (world_x - x0) / denom
                return int(y0 * (1 - t) + y1 * t)
        return segs[-1][1]

    def surface_y(self, rect: pygame.Rect) -> int:
        base = self.surface_y_rect_x(rect.centerx)
        return base - rect.height

    def get_support_y(self, world_x: int) -> int:
        best = self.surface_y_rect_x(world_x)
        for d in self.props:
            if not d.get("solid", True):
                continue
            r: pygame.Rect = d["rect"]
            if r.left <= world_x <= r.right and r.top < best:
                best = r.top
        return best

    # ----------------------------
    # 충돌 대상
    # ----------------------------
    def get_solid_rects(self) -> list[pygame.Rect]:
        out = list(self.walls)
        out += [d["rect"] for d in self.props if d.get("solid", True)]
        return out

    # ----------------------------
    # 사진
    # ----------------------------
    def _load_photo(self, path: str, w: int, h: int):
        key = (path, w, h)
        if key in self._photo_cache:
            return self._photo_cache[key]
        if not path or not os.path.exists(path):
            self._photo_cache[key] = None
            return None
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, (w, h))
            self._photo_cache[key] = img
            return img
        except Exception:
            self._photo_cache[key] = None
            return None

    def draw_photos(self, surf: pygame.Surface, camera_x: float) -> None:
        for ph in self.photos:
            x = int(ph["x"] - camera_x)
            y = int(ph["y"])
            w = int(ph["w"])
            h = int(ph["h"])
            img = self._load_photo(ph.get("path", ""), w, h)
            if img:
                surf.blit(img, (x, y))
            else:
                pygame.draw.rect(surf, (120, 120, 140), (x, y, w, h), 1)

    # ----------------------------
    # 5×3 벽 그리드
    # ----------------------------
    def _apply_wall_grid_from_json(self, data: dict) -> None:
        g = data.get("wall_grid")
        if isinstance(g, dict):
            self.wall_grid["cols"] = int(g.get("cols", self.wall_grid["cols"]))
            self.wall_grid["rows"] = int(g.get("rows", self.wall_grid["rows"]))
            self.wall_grid["cell"] = int(g.get("cell", self.wall_grid["cell"]))
            org = g.get("origin")
            if isinstance(org, (list, tuple)) and len(org) == 2:
                self.wall_grid["origin"] = V2(int(org[0]), int(org[1]))

        for pair in data.get("wall_cells", []):
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                self.wall_cells.add((int(pair[0]), int(pair[1])))

    def rebuild_walls_from_grid(self) -> None:
        cols = self.wall_grid["cols"]
        rows = self.wall_grid["rows"]
        cell = self.wall_grid["cell"]
        ox, oy = self.wall_grid["origin"]
        self.walls = []
        for (c, r) in self.wall_cells:
            if 0 <= c < cols and 0 <= r < rows:
                x = int(ox + c * cell)
                y = int(oy + r * cell)
                self.walls.append(pygame.Rect(x, y, cell, cell))

    def wall_cell_from_world(self, wx: float, wy: float):
        cols = self.wall_grid["cols"]
        rows = self.wall_grid["rows"]
        cell = self.wall_grid["cell"]
        ox, oy = self.wall_grid["origin"]
        lx, ly = wx - ox, wy - oy
        if lx < 0 or ly < 0:
            return None
        c = int(lx // cell)
        r = int(ly // cell)
        return (c, r) if (0 <= c < cols and 0 <= r < rows) else None

    def toggle_wall_cell(self, c: int, r: int, set_to=None) -> None:
        key = (c, r)
        if set_to is None:
            (self.wall_cells.remove(key) if key in self.wall_cells else self.wall_cells.add(key))
        elif set_to:
            self.wall_cells.add(key)
        else:
            self.wall_cells.discard(key)
        self.rebuild_walls_from_grid()

    def draw_wall_grid_overlay(self, surf, camera_x: float) -> None:
        cols = self.wall_grid["cols"]
        rows = self.wall_grid["rows"]
        cell = self.wall_grid["cell"]
        ox, oy = self.wall_grid["origin"]
        sx0 = int(ox - camera_x)
        sy0 = int(oy)
        w = cols * cell
        h = rows * cell

        pygame.draw.rect(surf, (240, 240, 255), (sx0, sy0, w, h), 2)
        for i in range(1, cols):
            x = sx0 + i * cell
            pygame.draw.line(surf, (200, 200, 220), (x, sy0), (x, sy0 + h), 1)
        for j in range(1, rows):
            y = sy0 + j * cell
            pygame.draw.line(surf, (200, 200, 220), (sx0, y), (sx0 + w, y), 1)

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        for (c, r) in self.wall_cells:
            pygame.draw.rect(overlay, (220, 80, 80, 90), (c * cell, r * cell, cell, cell))
        surf.blit(overlay, (sx0, sy0))

    # ----------------------------
    # 배경/지면 렌더
    # ----------------------------
    def _draw_sky(self, surf):
        for y in range(SCREEN_H):
            t = y / max(1, SCREEN_H - 1)
            r = int(self.sky_top[0] * (1 - t) + self.sky_bottom[0] * t)
            g = int(self.sky_top[1] * (1 - t) + self.sky_bottom[1] * t)
            b = int(self.sky_top[2] * (1 - t) + self.sky_bottom[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_W, y))

    def _draw_ground(self, surf, camera_x: float):
        pts = [(int(x - camera_x), int(y)) for (x, y) in self.ground_segments]
        pts = [(pts[0][0], SCREEN_H)] + pts + [(pts[-1][0], SCREEN_H)]
        pygame.draw.polygon(surf, GROUND_LIGHT, pts)
        pygame.draw.lines(surf, GROUND_DARK, False, pts[1:-1], 3)

    def draw(self, surf, camera_x: float):
        self._draw_sky(surf)
        self._draw_ground(surf, camera_x)
        self.draw_photos(surf, camera_x)
