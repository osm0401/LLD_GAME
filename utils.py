# utils.py
def draw_multiline(surf, text, font, color, pos, max_width=800, line_spacing=6):
    words = list(text)
    lines, cur = [], ""
    for ch in words:
        cand = cur + ch
        if font.size(cand)[0] <= max_width:
            cur = cand
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    x, y = pos
    for ln in lines:
        img = font.render(ln, True, color)
        surf.blit(img, (x, y))
        y += img.get_height() + line_spacing
