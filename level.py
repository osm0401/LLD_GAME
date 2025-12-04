# level.py — 배경/지면/파라ラック스 + JSON 기반 맵 데이터(바닥/벽/지형지물)

import os
import json
import math
import pygame
from pygame.math import Vector2 as V2
from settings import (
    SCREEN_W, SCREEN_H, WORLD_W, WORLD_H,
    SKY_TOP, SKY_BOTTOM, CLOUD,
    GROUND_DARK, GROUND_LIGHT, GROUND_Y,
)


class Level:
    """
    한 개의 맵(씬)을 담당하는 클래스.
    - map_id별로 map_<map_id>.json 에서 지형 데이터를 로드/세이브
    - ground_segments : 바닥(플랫폼) 곡선
    - walls           : 벽(충돌용/장식용)
    - props           : 지형지물(소품, 오브젝트)
    """

    def __init__(self, map_id: str = "city"):
        self.map_id = map_id

        # 월드 크기 (JSON에서 덮어쓸 수 있음)
        self.world_w = WORLD_W
        self.world_h = WORLD_H

        # 지형 데이터
        self.ground_segments: list[tuple[int, int]] = []
        self.walls: list[dict] = []  # {"x":..,"y":..,"w":..,"h":..}
        self.props: list[dict] = []  # {"x":..,"y":..,"w":..,"h":..}

        # 파라allax 구름(타원)
        self.clouds_far = [
            (300, 120, 260, 90),
            (1100, 100, 300, 100),
            (2000, 130, 280, 95),
            (3100, 110, 320, 110),
        ]
        self.clouds_mid = [
            (600, 180, 220, 80),
            (1700, 210, 240, 90),
            (2600, 170, 220, 80),
            (3800, 190, 260, 86),
        ]

        # JSON에서 로드 시도, 실패하면 기본 지형 사용
        self._load_from_json_or_default()

    # ------------------------------------------------------------------
    # JSON 로드/세이브
    # ------------------------------------------------------------------
    def _map_filename(self) -> str:
        """이 맵의 JSON 파일 이름 (예: map_city.json)."""
        return f"map_{self.map_id}.json"

    def _default_ground_segments(self) -> list[tuple[int, int]]:
        """기존에 하드코딩으로 쓰던 기본 바닥 형태."""
        return [
            (0, GROUND_Y),
            (800, GROUND_Y - 8),
            (1600, GROUND_Y - 22),
            (2400, GROUND_Y - 10),
            (3200, GROUND_Y - 18),
            (4000, GROUND_Y - 6),
            (WORLD_W, GROUND_Y - 12),
        ]

    def get_solid_rects(self) -> list[pygame.Rect]:
        """
        벽(walls) + 지형지물(props)을 모두 pygame.Rect 리스트로 만들어 돌려준다.
        (충돌판정에 사용)
        """
        rects: list[pygame.Rect] = []

        for w in self.walls:
            try:
                rx = int(w.get("x", 0))
                ry = int(w.get("y", 0))
                rw = int(w.get("w", 40))
                rh = int(w.get("h", 80))
                rects.append(pygame.Rect(rx, ry, rw, rh))
            except Exception:
                pass

        for p in self.props:
            try:
                rx = int(p.get("x", 0))
                ry = int(p.get("y", 0))
                rw = int(p.get("w", 30))
                rh = int(p.get("h", 30))
                rects.append(pygame.Rect(rx, ry, rw, rh))
            except Exception:
                pass

        return rects
    def _set_default_geometry(self):
        """JSON이 없거나 오류일 때 사용할 기본 지형."""
        self.ground_segments = self._default_ground_segments()
        self.walls = []
        self.props = []

    def _load_from_json_or_default(self):
        """map_<id>.json에서 맵을 로드. 실패 시 기본값."""
        path = self._map_filename()
        if not os.path.exists(path):
            print(f"[Level] {path} 없음 → 기본 지형 사용")
            self._set_default_geometry()
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.world_w = int(data.get("world_w", WORLD_W))
            self.world_h = int(data.get("world_h", WORLD_H))

            gs = data.get("ground_segments")
            if isinstance(gs, list) and gs:
                self.ground_segments = [(int(x), int(y)) for x, y in gs]
            else:
                self.ground_segments = self._default_ground_segments()

            self.walls = list(data.get("walls", []))
            self.props = list(data.get("props", []))

            print(f"[Level] {path} 로드 완료 (segments={len(self.ground_segments)}, "
                  f"walls={len(self.walls)}, props={len(self.props)})")
        except Exception as e:
            print("[Level] map load error:", e)
            self._set_default_geometry()

    def save_to_json(self):
        """현재 지형/벽/지형지물을 map_<id>.json에 저장."""
        data = {
            "id": self.map_id,
            "world_w": int(self.world_w),
            "world_h": int(self.world_h),
            "ground_segments": [[int(x), int(y)] for (x, y) in self.ground_segments],
            "walls": self.walls,
            "props": self.props,
        }
        path = self._map_filename()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[Level] 맵 저장 완료 → {path}")
        except Exception as e:
            print("[Level] map save error:", e)

    # ------------------------------------------------------------------
    # 인게임 에디터용 헬퍼 (벽/지형지물/바닥 수정)
    # ------------------------------------------------------------------
    def add_wall(self, x: float, y: float, w: int = 40, h: int = 80):
        """현재 맵에 새 벽 추가."""
        self.walls.append({
            "x": int(x),
            "y": int(y),
            "w": int(w),
            "h": int(h),
        })

    def add_prop(self, x: float, y: float, w: int = 32, h: int = 32):
        """현재 맵에 새 지형지물(소품) 추가."""
        self.props.append({
            "x": int(x),
            "y": int(y),
            "w": int(w),
            "h": int(h),
        })

    @staticmethod
    def _find_index_near(items: list[dict], x: float, y: float, radius: float = 40) -> int | None:
        """리스트에서 (x,y)에 가장 가까운 요소의 인덱스를 찾는다."""
        if not items:
            return None
        best_i = None
        best_d2 = radius * radius
        for i, it in enumerate(items):
            ix = it.get("x", 0) + it.get("w", 0) / 2
            iy = it.get("y", 0) + it.get("h", 0) / 2
            dx = ix - x
            dy = iy - y
            d2 = dx * dx + dy * dy
            if d2 <= best_d2:
                best_d2 = d2
                best_i = i
        return best_i

    def remove_wall_at(self, x: float, y: float, radius: float = 40):
        """(x,y) 주변의 벽 하나 삭제."""
        idx = self._find_index_near(self.walls, x, y, radius)
        if idx is not None:
            self.walls.pop(idx)

    def remove_prop_at(self, x: float, y: float, radius: float = 40):
        """(x,y) 주변의 지형지물 하나 삭제."""
        idx = self._find_index_near(self.props, x, y, radius)
        if idx is not None:
            self.props.pop(idx)

    def adjust_ground_at(self, x: float, new_y: float):
        """
        x 좌표와 가장 가까운 ground_segments의 지점을 찾아
        그 y를 new_y로 조정 (바닥 높이 수정).
        """
        if not self.ground_segments:
            return
        idx = min(range(len(self.ground_segments)), key=lambda i: abs(self.ground_segments[i][0] - x))
        gx, gy = self.ground_segments[idx]
        self.ground_segments[idx] = (gx, int(new_y))

    # ------------------------------------------------------------------
    # 내부 그리기 유틸
    # ------------------------------------------------------------------
    def _draw_sky(self, surf: pygame.Surface):
        """화면 전체 그라디언트 배경."""
        for y in range(SCREEN_H):
            t = y / (SCREEN_H - 1)
            r = int(SKY_TOP[0] * (1 - t) + SKY_BOTTOM[0] * t)
            g = int(SKY_TOP[1] * (1 - t) + SKY_BOTTOM[1] * t)
            b = int(SKY_TOP[2] * (1 - t) + SKY_BOTTOM[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_W, y))

    def _draw_parallax_clouds(self, surf: pygame.Surface, camera_x: float):
        """카메라에 따라 움직이는 파라allax 구름."""
        # 먼 구름(느리게)
        for x, y, w, h in self.clouds_far:
            rx = int(x - camera_x * 0.2)
            ry = y
            pygame.draw.ellipse(surf, CLOUD, (rx, ry, w, h))
        # 중간 구름
        for x, y, w, h in self.clouds_mid:
            rx = int(x - camera_x * 0.4)
            ry = y
            pygame.draw.ellipse(surf, CLOUD, (rx, ry, w, h))

    def _draw_ground(self, surf: pygame.Surface, camera_x: float):
        """바닥 + 잔디 디테일 + 벽 + 지형지물 렌더링."""
        # 바닥(ground_segments)을 폴리곤으로 채우기
        pts = []
        for x, gy in self.ground_segments:
            pts.append((int(x - camera_x), int(gy)))

        if len(pts) >= 2:
            # 아래 화면 끝까지 닫아서 채우기
            pts_poly = [(pts[0][0], SCREEN_H)] + pts + [(pts[-1][0], SCREEN_H)]
            pygame.draw.polygon(surf, GROUND_LIGHT, pts_poly)
            pygame.draw.lines(surf, GROUND_DARK, False, pts, 3)

            # 난간/잔디 느낌의 디테일
            for x in range(-100, SCREEN_W + 100, 12):
                base = self.surface_y_rect_x(int(x + camera_x))
                pygame.draw.rect(surf, GROUND_DARK, (x, base - 4, 8, 4))

        # 벽(직사각형)
        for w in self.walls:
            try:
                rx = int(w.get("x", 0) - camera_x)
                ry = int(w.get("y", 0))
                rw = int(w.get("w", 40))
                rh = int(w.get("h", 80))
                rect = pygame.Rect(rx, ry, rw, rh)
                pygame.draw.rect(surf, (90, 90, 110), rect)
                pygame.draw.rect(surf, (30, 30, 45), rect, 2)
            except Exception:
                pass

        # 지형지물(소품)
        for p in self.props:
            try:
                rx = int(p.get("x", 0) - camera_x)
                ry = int(p.get("y", 0))
                rw = int(p.get("w", 30))
                rh = int(p.get("h", 30))
                rect = pygame.Rect(rx, ry, rw, rh)
                pygame.draw.rect(surf, (130, 110, 70), rect)
                pygame.draw.rect(surf, (80, 60, 40), rect, 2)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def draw(self, surf: pygame.Surface, camera_x: float):
        """현재 맵 전체를 그린다."""
        self._draw_sky(surf)
        self._draw_parallax_clouds(surf, camera_x)
        self._draw_ground(surf, camera_x)

    # 주어진 월드 x에서의 지면 y 샘플
    def surface_y_rect_x(self, world_x: int) -> int:
        """ground_segments 사이를 보간해서 해당 x의 지면 y를 구한다."""
        segs = self.ground_segments
        if not segs:
            return GROUND_Y
        for i in range(len(segs) - 1):
            x0, y0 = segs[i]
            x1, y1 = segs[i + 1]
            if x0 <= world_x <= x1:
                t = (world_x - x0) / max(1, (x1 - x0))   # ← 여기까지 이미 고쳐둔 부분
                return int(y0 * (1 - t) + y1 * t)
        return segs[-1][1]

    def get_support_y(self, world_x: float) -> int:
        """
        world_x 위치에서
        - 기본 바닥(ground_segments)
        - 그 x를 덮고 있는 벽/지형지물의 "윗면"
        중에서 가장 위(화면 기준 위쪽, 즉 y가 가장 작은 값)를 발판으로 사용.

        NPC처럼 '딱 서 있는' 애들의 발바닥 y를 구할 때 사용.
        """
        # 기본 바닥 높이
        ground_y = self.surface_y_rect_x(int(world_x))
        support_y = ground_y

        # 벽 + 지형지물 위도 발판으로 인정
        for obj in (self.walls + self.props):
            try:
                ox = obj.get("x", 0)
                oy = obj.get("y", 0)  # obj의 top
                ow = obj.get("w", 0)

                # 이 오브젝트가 world_x를 수평으로 덮고 있을 때만 후보
                if ox <= world_x <= ox + ow:
                    # y는 작을수록 화면 위 → '더 높은' 발판
                    if oy < support_y:
                        support_y = int(oy)
            except Exception:
                pass

        return support_y
    def get_support_y(self, world_x: float) -> int:
        """
        world_x 위치에서
        - 기본 바닥(ground_segments)
        - 그 x를 덮고 있는 벽/지형지물의 "윗면"
        중에서 가장 위(화면 기준 위쪽, 즉 y가 가장 작은 값)를 발판으로 사용.

        NPC처럼 '딱 서 있는' 애들의 발바닥 y를 구할 때 사용.
        """
        # 기본 바닥 높이
        ground_y = self.surface_y_rect_x(int(world_x))
        support_y = ground_y

        # 벽 + 지형지물 위도 발판으로 인정
        for obj in (self.walls + self.props):
            try:
                ox = obj.get("x", 0)
                oy = obj.get("y", 0)          # obj의 top
                ow = obj.get("w", 0)

                # 이 오브젝트가 world_x를 수평으로 덮고 있을 때만 후보
                if ox <= world_x <= ox + ow:
                    # y는 작을수록 화면 위 → '더 높은' 발판
                    if oy < support_y:
                        support_y = int(oy)
            except Exception:
                pass

        return support_y

    # 플레이어 rect의 바닥 y 결정
    def surface_y(self, player_rect: pygame.Rect) -> int:
        """
        플레이어 rect의 중심 x 에서 지면 높이를 찾고,
        그 위에 플레이어 키(rect.height)를 빼서 발바닥이 딱 닿도록 y를 돌려준다.
        """
        px_center = player_rect.centerx
        base_y = self.surface_y_rect_x(px_center)
        return base_y - player_rect.height
