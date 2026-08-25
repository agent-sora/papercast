#!/usr/bin/env python3
"""Generate the podcast cover art: a nerdy hugging-face-style robot.

Draws a 3000x3000 px square (Apple/iTunes podcast-art spec range) with PIL:
dark slate backdrop, faint circuit traces, a warm yellow badge, and a friendly
round-glasses robot wearing podcast headphones. Output: assets/cover.png,
which build_rss.py copies into the published site (feed itunes:image).
"""
import os

from PIL import Image, ImageDraw, ImageFont

W = H = 3000
SLATE = (13, 16, 23)
PANEL = (22, 27, 38)
YELLOW = (255, 210, 30)
ORANGE = (255, 157, 0)
STEEL = (122, 162, 255)
WHITE = (235, 238, 244)
DARKVISOR = (10, 12, 18)


def font(size, bold=True):
    names = ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"] if bold else \
            ["DejaVuSans.ttf", "DejaVuSans-Bold.ttf"]
    for n in names:
        for base in ("/usr/share/fonts/truetype/dejavu", ""):
            p = os.path.join(base, n) if base else n
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
        try:  # matplotlib ships DejaVu as well
            import matplotlib
            d = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data",
                             "fonts", "ttf")
            p = os.path.join(d, names[0] if bold else names[1])
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def rounded(draw, box, r, **kw):
    draw.rounded_rectangle(box, radius=r, **kw)


def circuit(draw):
    """Faint PCB traces in the corners."""
    c = (34, 44, 66)
    for x in range(140, 900, 190):
        draw.line([(x, 60), (x, 420), (x + 160, 580)], fill=c, width=14)
        draw.ellipse([x - 16, 44, x + 16, 76], fill=c)
    for y in range(1500, 2900, 220):
        draw.line([(2940, y), (2600, y), (2450, y + 150)], fill=c, width=14)
        draw.ellipse([2924, y - 16, 2956, y + 16], fill=c)


def robot(draw):
    cx = W // 2
    # antenna
    draw.line([(cx, 700), (cx, 520)], fill=STEEL, width=26)
    draw.ellipse([cx - 46, 430, cx + 46, 522], fill=YELLOW)
    # headphone band
    draw.arc([cx - 780, 830, cx + 780, 1750], 180, 360, fill=STEEL, width=64)
    # ears / headphone cups
    for sx in (-1, 1):
        ex = cx + sx * 800
        rounded(draw, [ex - 110, 1180, ex + 110, 1660], 90, fill=PANEL,
                outline=STEEL, width=16)
        rounded(draw, [ex - 52, 1300, ex + 52, 1540], 44, fill=STEEL)
    # mic boom from left cup toward mouth
    draw.arc([cx - 700, 1450, cx + 250, 2300], 40, 115, fill=STEEL, width=26)
    draw.ellipse([cx + 170, 2020, cx + 320, 2170], fill=ORANGE)
    # head
    rounded(draw, [cx - 700, 850, cx + 700, 2050], 340, fill=WHITE,
            outline=(180, 188, 200), width=10)
    # visor
    rounded(draw, [cx - 580, 1030, cx + 580, 1560], 240, fill=DARKVISOR)
    # nerdy round glasses + glowing eyes
    eye_y = 1290
    for sx in (-1, 1):
        exx = cx + sx * 270
        draw.ellipse([exx - 165, eye_y - 165, exx + 165, eye_y + 165],
                     outline=STEEL, width=22)
        draw.ellipse([exx - 92, eye_y - 92, exx + 92, eye_y + 92],
                     fill=(96, 220, 255))
    draw.line([(cx - 100, eye_y), (cx + 100, eye_y)], fill=STEEL, width=22)
    # friendly smile (the hug-bot nod)
    draw.arc([cx - 260, 1560, cx + 260, 1930], 15, 165,
             fill=(150, 158, 172), width=30)
    # neck + shoulders
    rounded(draw, [cx - 150, 2030, cx + 150, 2180], 60, fill=PANEL)
    rounded(draw, [cx - 560, 2150, cx + 560, 2560], 200, fill=PANEL,
            outline=(48, 58, 84), width=12)
    # little heart held up (hugging-face nod)
    hx, hy = cx + 620, 2320
    draw.ellipse([hx - 130, hy - 90, hx + 10, hy + 50], fill=ORANGE)
    draw.ellipse([hx - 10, hy - 90, hx + 130, hy + 50], fill=ORANGE)
    draw.polygon([(hx - 128, hy + 8), (hx + 128, hy + 8),
                  (hx, hy + 170)], fill=ORANGE)


def main():
    img = Image.new("RGB", (W, H), SLATE)
    d = ImageDraw.Draw(img)
    circuit(d)
    # warm badge behind the robot
    d.ellipse([W // 2 - 1050, 620, W // 2 + 1050, 2720], fill=(36, 31, 16))
    d.ellipse([W // 2 - 1010, 660, W // 2 + 1010, 2680],
              outline=YELLOW, width=18)
    robot(d)

    f_big = font(300)
    f_small = font(150)
    d.text((W // 2, 330), "AGENT SORA", anchor="mm", fill=YELLOW, font=f_big)
    d.text((W // 2, 2830), "DAILY  PAPERS", anchor="mm", fill=WHITE,
           font=f_small)
    d.text((W // 2, 2830), "DAILY  PAPERS", anchor="mm",
           fill=(255, 157, 0), font=f_small)

    out = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "assets", "cover.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
