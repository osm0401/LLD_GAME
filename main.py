# main.py
import pygame
import settings as S
from player import Player
from level import Level
from npc import NPC


def _sysfont(name, size):
    try:
        return pygame.font.SysFont(name, size)
    except Exception:
        return pygame.font.SysFont(None, size)


class WarpGate:
    """가까이서 F를 누르면 씬 이동. 워프가 안 먹는 상황을 방지하기 위해 입력을 보강."""
    def __init__(self, world_x, level, label, target_scene):
        self.w, self.h = 40, 90
        base_y = level.get_support_y(world_x)
        self.x = world_x - self.w // 2
        self.y = base_y - self.h

        self.label = label
        self.target_scene = target_scene
        self.range = 80
        self.font = _sysfont(S.FONT_NAME, 18)

        # ✅ 연속 워프 방지용 쿨다운
        self._last_use_ms = 0
        self.cooldown_ms = 180

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, player_rect, events):
        near = abs(player_rect.centerx - self.rect.centerx) <= self.range

        # ✅ 이벤트 누락 대비: KEYDOWN 또는 현재 키 눌림 둘 다 허용
        pressed = pygame.key.get_pressed()
        want = near and (
            any(e.type == pygame.KEYDOWN and e.key == pygame.K_f for e in events)
            or pressed[pygame.K_f]
        )

        now = pygame.time.get_ticks()
        if want and (now - self._last_use_ms) >= self.cooldown_ms:
            self._last_use_ms = now
            return near, True

        return near, False

    def draw(self, surf, camera_x):
        sx, sy = int(self.x - camera_x), int(self.y)
        r = pygame.Rect(sx, sy, self.w, self.h)
        pygame.draw.rect(surf, (120, 220, 255), r, border_radius=10)
        pygame.draw.rect(surf, (20, 40, 60), r, 2)

    def draw_hint(self, surf, camera_x, near):
        if not near:
            return
        txt = self.font.render(f"F: {self.label}", True, (30, 30, 40))
        box = pygame.Surface((txt.get_width() + 10, txt.get_height() + 6), pygame.SRCALPHA)
        box.fill((255, 255, 255, 210))
        sx = int(self.rect.centerx - camera_x) - box.get_width() // 2
        sy = self.rect.top - 50
        surf.blit(box, (sx, sy))
        surf.blit(txt, (sx + 5, sy + 3))


def build_scene(scene_id: str):
    if scene_id == "casino":
        level = Level("casino_map.json")
        spawn_x = 1200
        npc = NPC("워니", 1400, level)  # ✅ 이름 변경
        gate = WarpGate(2000, level, "연구소로 이동", "lab")

    elif scene_id == "lab":
        level = Level("map_lab.json")
        spawn_x = 400
        npc = NPC("워니", 600, level)   # ✅ 이름 통일
        gate = WarpGate(300, level, "카지노로 돌아가기", "casino")

    else:
        return build_scene("casino")

    return level, spawn_x, npc, gate


def main():
    pygame.init()
    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
    clock = pygame.time.Clock()
    font = _sysfont(S.FONT_NAME, 18)

    wall_edit_mode = False
    photo_edit_mode = False

    photo_palette = [
        "assets/photos/casino_logo.png",
        "assets/photos/note1.png",
        "assets/photos/poster.png",
    ]
    photo_index = 0

    current_scene = "casino"
    level, spawn_x, npc, gate = build_scene(current_scene)

    player = Player((spawn_x, 0))
    player.pos.y = level.surface_y(player.rect)

    camera_x = 0.0
    running = True

    while running:
        dt = clock.tick(S.FPS) / 1000.0

        # ✅ 이벤트는 프레임당 딱 1번만
        events = pygame.event.get()

        # ----------------- 시스템/키 이벤트 -----------------
        for e in events:
            if e.type == pygame.QUIT:
                running = False

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_b:
                    wall_edit_mode = not wall_edit_mode
                    if wall_edit_mode:
                        photo_edit_mode = False

                if e.key == pygame.K_p:
                    photo_edit_mode = not photo_edit_mode
                    if photo_edit_mode:
                        wall_edit_mode = False

                if e.key == pygame.K_LEFTBRACKET and photo_palette:
                    photo_index = (photo_index - 1) % len(photo_palette)
                if e.key == pygame.K_RIGHTBRACKET and photo_palette:
                    photo_index = (photo_index + 1) % len(photo_palette)

                if e.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    level.save_map()

        # ----------------- 마우스 에디터 -----------------
        mx, my = pygame.mouse.get_pos()
        world_x = mx + camera_x
        world_y = my

        if wall_edit_mode:
            for e in events:
                if e.type == pygame.MOUSEBUTTONDOWN:
                    cell = level.wall_cell_from_world(world_x, world_y)
                    if cell:
                        c, r = cell
                        if e.button == 1:
                            level.toggle_wall_cell(c, r)
                        elif e.button == 3:
                            level.toggle_wall_cell(c, r, set_to=False)

        if photo_edit_mode:
            for e in events:
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if e.button == 1 and photo_palette:
                        level.photos.append({
                            "x": int(world_x),
                            "y": int(world_y),
                            "w": 96,
                            "h": 96,
                            "path": photo_palette[photo_index],
                        })
                    elif e.button == 3 and level.photos:
                        best_i, best_d = -1, 10**18
                        for i, ph in enumerate(level.photos):
                            dx = ph["x"] - world_x
                            dy = ph["y"] - world_y
                            d = dx * dx + dy * dy
                            if d < best_d:
                                best_d, best_i = d, i
                        if best_i != -1 and best_d <= 120 * 120:
                            level.photos.pop(best_i)

        # ----------------- 워프 -----------------
        gate_near, gate_activated = gate.update(player.rect, events)
        if gate_activated:
            current_scene = gate.target_scene
            level, spawn_x, npc, gate = build_scene(current_scene)
            player.pos.x = spawn_x
            player.pos.y = level.surface_y(player.rect)
            camera_x = 0.0

        # ----------------- NPC -----------------
        near = npc.update(player.rect, events)

        # ----------------- 플레이어 -----------------
        keys = pygame.key.get_pressed()
        player.update(dt, keys, level)

        # ----------------- 카메라 -----------------
        target = player.pos.x + player.w / 2 - S.SCREEN_W / 2
        if level.world_w > S.SCREEN_W:
            target = max(0, min(level.world_w - S.SCREEN_W, target))
        else:
            target = 0
        camera_x += (target - camera_x) * min(1.0, dt * 8.0)

        # ----------------- 렌더 -----------------
        level.draw(screen, camera_x)
        gate.draw(screen, camera_x)
        npc.draw(screen, camera_x)
        player.draw(screen, camera_x)

        if wall_edit_mode:
            level.draw_wall_grid_overlay(screen, camera_x)

        gate.draw_hint(screen, camera_x, gate_near)
        npc.draw_dialog(screen, camera_x, near, S.SCREEN_W, S.SCREEN_H)

        asset_name = photo_palette[photo_index] if photo_palette else "none"
        help_lines = [
            f"MAP: {level.map_file}",
            f"WallGrid(B): {'ON' if wall_edit_mode else 'OFF'}",
            f"PhotoMode(P): {'ON' if photo_edit_mode else 'OFF'}  Asset: {asset_name}",
            "A/D 이동  SPACE 대화  F 워프  [ ] 사진변경  Ctrl+S 저장",
        ]

        for i, s in enumerate(help_lines):
            img = font.render(s, True, (30, 30, 40))
            box = pygame.Surface((img.get_width() + 10, img.get_height() + 4), pygame.SRCALPHA)
            box.fill((255, 255, 255, 150))
            screen.blit(box, (10, 10 + i * 22))
            screen.blit(img, (15, 12 + i * 22))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
