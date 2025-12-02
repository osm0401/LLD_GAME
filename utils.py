# utils.py
import pygame
import math

def circle_rect_intersect(cx, cy, cr, rx, ry, rw, rh):
    """원(플레이어)과 직사각형(벽 블록) 충돌 여부."""
    nx = max(rx, min(cx, rx + rw))
    ny = max(ry, min(cy, ry + rh))
    dx, dy = cx - nx, cy - ny
    return (dx*dx + dy*dy) <= (cr*cr)

def draw_multiline(surf, text, font, color, topleft, max_width):
    if not text:
        return
    x, y = topleft
    space_w = font.size(" ")[0]
    for para in str(text).split("\n"):
        words = para.split(" ")
        line = ""
        for w in words:
            test = (line + " " + w) if line else w
            if font.size(test)[0] <= max_width:
                line = test
            else:
                surf.blit(font.render(line, True, color), (x, y))
                y += font.get_linesize()
                line = w
        surf.blit(font.render(line, True, color), (x, y))
        y += font.get_linesize()
