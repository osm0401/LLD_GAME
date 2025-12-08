# isac.py
"""
Isaac-like Topdown View Controller

이 모듈은 "연구실(scene='lab')"처럼 탑다운 뷰가 필요한 씬에서
카메라/렌더/모드 전환을 한 곳에 모아 관리하기 위한 유틸이다.

핵심 철학:
- Player.update가 mode="topdown"일 때 WASD 이동을 처리하도록 두고,
  여기서는 모드 전환 + 탑다운 전용 카메라 + 탑다운 전용 렌더만 담당한다.
- 기존 NPC.draw는 camera_y를 고려하지 않는 경우가 많으므로,
  탑다운에서는 이 모듈의 간단 렌더러를 사용한다.
- Level에 draw_topdown이 있으면 사용하고,
  없으면 fallback(단색 바닥 + 벽/props 사각형)으로 그린다.

main에서 사용 예:

    from isac import TopdownView

    top = TopdownView()

    # 씬 진입 시
    if current_scene == "lab":
        top.enter(player)

    # 씬 업데이트
    top.update(dt, player, level)

    # 렌더
    top.draw(screen, level, player, npcs=[npc], gates=[gate])

"""

from __future__ import annotations
import pygame


class TopdownView:
    def __init__(self,
                 *,
                 bg_color=(22, 24, 32),
                 cam_smooth=10.0):
        self.bg_color = bg_color
        self.cam_smooth = cam_smooth
        self.camera_x = 0.0
        self.camera_y = 0.0

    # ---------------------------------------------------------
    # 모드 전환
    # ---------------------------------------------------------
    def enter(self, player):
        """탑다운 씬 진입 시 호출."""
        if hasattr(player, "mode"):
            player.mode = "topdown"

    def exit(self, player):
        """탑다운 씬 종료 시 호출."""
        if hasattr(player, "mode"):
            player.mode = "side"

    # ---------------------------------------------------------
    # 카메라
    # ---------------------------------------------------------
    def _calc_target(self, player, level, screen_w, screen_h):
        px = player.pos.x + player.w / 2
        py = player.pos.y + player.h / 2

        target_x = px - screen_w / 2
        target_y = py - screen_h / 2

        # 월드 경계 클램프
        if getattr(level, "world_w", 0) > screen_w:
            target_x = max(0, min(level.world_w - screen_w, target_x))
        else:
            target_x = 0

        if getattr(level, "world_h", 0) > screen_h:
            target_y = max(0, min(level.world_h - screen_h, target_y))
        else:
            target_y = 0

        return target_x, target_y

    def update(self, dt, player, level, *, screen_w=None, screen_h=None):
        """탑다운 카메라 업데이트."""
        if screen_w is None or screen_h is None:
            # level이 settings를 직접 쓰는 구조가 많아 안전하게 디스플레이에서 가져옴
            screen = pygame.display.get_surface()
            screen_w, screen_h = screen.get_width(), screen.get_height()

        tx, ty = self._calc_target(player, level, screen_w, screen_h)

        # 부드러운 보간
        k = min(1.0, dt * self.cam_smooth)
        self.camera_x += (tx - self.camera_x) * k
        self.camera_y += (ty - self.camera_y) * k

    # ---------------------------------------------------------
    # 탑다운 렌더 (레벨 fallback)
    # ---------------------------------------------------------
    def _draw_level_fallback(self, surf, level):
        # 바닥
        surf.fill(self.bg_color)

        # photos를 탑다운 카메라 기준으로 그릴 수 있으면 사용
        if hasattr(level, "draw_photos_topdown"):
            level.draw_photos_topdown(surf, self.camera_x, self.camera_y)
        elif hasattr(level, "draw_photos"):
            # draw_photos가 camera_x만 쓰는 버전이면 y는 무시되지만 일단 호출
            try:
                level.draw_photos(surf, self.camera_x)
            except Exception:
                pass

        # walls
        for r in getattr(level, "walls", []):
            rr = pygame.Rect(r.x - self.camera_x, r.y - self.camera_y, r.w, r.h)
            pygame.draw.rect(surf, (90, 95, 110), rr)
            pygame.draw.rect(surf, (30, 32, 40), rr, 2)

        # props(솔리드만)
        for d in getattr(level, "props", []):
            try:
                if not d.get("solid", True):
                    continue
                r = d["rect"]
            except Exception:
                continue
            rr = pygame.Rect(r.x - self.camera_x, r.y - self.camera_y, r.w, r.h)
            pygame.draw.rect(surf, (110, 105, 125), rr)
            pygame.draw.rect(surf, (35, 35, 45), rr, 2)

    def draw_level(self, surf, level):
        """Level에 draw_topdown이 있으면 그걸 우선 사용."""
        if hasattr(level, "draw_topdown"):
            level.draw_topdown(surf, self.camera_x, self.camera_y)
        else:
            self._draw_level_fallback(surf, level)

    # ---------------------------------------------------------
    # 엔티티 렌더 (NPC/게이트)
    # ---------------------------------------------------------
    def _draw_rect_entity(self, surf, rect_world, color, outline=(20, 20, 30)):
        rr = pygame.Rect(
            rect_world.x - self.camera_x,
            rect_world.y - self.camera_y,
            rect_world.w,
            rect_world.h
        )
        pygame.draw.rect(surf, color, rr, border_radius=6)
        pygame.draw.rect(surf, outline, rr, 1, border_radius=6)

    def draw_npcs(self, surf, npcs):
        """탑다운에서 NPC는 안전하게 간단 사각형으로 렌더."""
        for npc in npcs:
            if not hasattr(npc, "rect"):
                continue
            self._draw_rect_entity(surf, npc.rect, (200, 120, 120))

    def draw_gates(self, surf, gates):
        """탑다운에서 게이트도 간단 렌더."""
        for gate in gates:
            if not hasattr(gate, "rect"):
                continue
            self._draw_rect_entity(surf, gate.rect, (120, 220, 255), outline=(10, 30, 50))

    # ---------------------------------------------------------
    # 플레이어 렌더
    # ---------------------------------------------------------
    def draw_player(self, surf, player):
        # player.draw가 camera_x만 받는 구버전일 수 있어 안전 분기
        if hasattr(player, "draw"):
            try:
                # 최신 시그니처(draw(surf, camera_x, camera_y))
                player.draw(surf, self.camera_x, self.camera_y)
                return
            except TypeError:
                # 구형 시그니처(draw(surf, camera_x))
                try:
                    player.draw(surf, self.camera_x)
                    return
                except Exception:
                    pass

        # 최후 fallback
        rect = pygame.Rect(
            int(player.pos.x - self.camera_x),
            int(player.pos.y - self.camera_y),
            player.w, player.h
        )
        pygame.draw.rect(surf, (120, 160, 255), rect, border_radius=6)

    # ---------------------------------------------------------
    # 통합 draw
    # ---------------------------------------------------------
    def draw(self, surf, level, player, *, npcs=(), gates=()):
        """
        탑다운 씬 1프레임 렌더.
        순서:
          1) 레벨
          2) 게이트
          3) NPC
          4) 플레이어
        """
        self.draw_level(surf, level)
        self.draw_gates(surf, gates)
        self.draw_npcs(surf, npcs)
        self.draw_player(surf, player)

    # ---------------------------------------------------------
    # 외부에서 카메라 값이 필요할 때
    # ---------------------------------------------------------
    def get_camera(self):
        return self.camera_x, self.camera_y
