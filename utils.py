# utils.py
import pygame

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
