import math, os, sys
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
SS = 4                      # supersampling
S = 1080 * SS               # square drawing area (centre of the story)
C = S // 2
LW = 24 * SS                # stroke width
WHITE = (255, 255, 255, 255)
GOLD = (232, 196, 120, 255)
BG = (0, 0, 0, 255)

def new():
    im = Image.new("RGBA", (S, S), BG)
    return im, ImageDraw.Draw(im)

def u(v): return int(v * SS)

def poly_outline(d, pts, col=WHITE, w=LW):
    d.line(pts + [pts[0], pts[1]], fill=col, width=w, joint="curve")

def star(d, cx, cy, r, col):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=col)

def sparkle(d, cx, cy, r, col):
    d.polygon([(cx, cy - r), (cx + r * .22, cy - r * .22), (cx + r, cy), (cx + r * .22, cy + r * .22),
               (cx, cy + r), (cx - r * .22, cy + r * .22), (cx - r, cy), (cx - r * .22, cy - r * .22)], fill=col)

def narxlar(d):
    global C
    C0=C; C=C+u(28)
    # price tag rotated 45 degrees
    pts = [(-90, -230), (90, -230), (150, -150), (150, 250), (-150, 250), (-150, -150)]
    pts = [(x * 1.0, y * 1.0) for x, y in [(-70, -250), (70, -250), (150, -150), (150, 240), (-150, 240), (-150, -150)]]
    a = math.radians(-45)
    rot = [(C + u(x * math.cos(a) - y * math.sin(a)), C + u(x * math.sin(a) + y * math.cos(a)) ) for x, y in pts]
    poly_outline(d, rot)
    hx, hy = 0, -165
    cx, cy = C + u(hx * math.cos(a) - hy * math.sin(a)), C + u(hx * math.sin(a) + hy * math.cos(a))
    r = u(30)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=GOLD, width=u(16))
    # "so'm" lines on the tag
    for off in (40, 110):
        x1, y1, x2, y2 = -75, off, 75, off
        p1 = (C + u(x1 * math.cos(a) - y1 * math.sin(a)), C + u(x1 * math.sin(a) + y1 * math.cos(a)))
        p2 = (C + u(x2 * math.cos(a) - y2 * math.sin(a)), C + u(x2 * math.sin(a) + y2 * math.cos(a)))
        d.line([p1, p2], fill=WHITE, width=u(18))
    C=C0

def toylar(d):
    r = u(165)
    for dx, col in ((-95, WHITE), (95, WHITE)):
        cx = C + u(dx)
        d.ellipse((cx - r, C + u(40) - r, cx + r, C + u(40) + r), outline=col, width=LW)
    # diamond on the right ring
    cx, cy = C + u(95), C + u(40) - r - u(10)
    s = u(55)
    d.polygon([(cx - s, cy - s * .35), (cx - s * .5, cy - s), (cx + s * .5, cy - s), (cx + s, cy - s * .35), (cx, cy + s * .6)], fill=GOLD)
    sparkle(d, C - u(240), C - u(200), u(40), GOLD)

def backstage(d):
    # movie camera: body, lens cone, two reels
    x0, y0, x1, y1 = C - u(230), C - u(20), C + u(110), C + u(200)
    d.rounded_rectangle((x0, y0, x1, y1), radius=u(30), outline=WHITE, width=LW)
    poly_outline(d, [(x1, C + u(60)), (C + u(250), C - u(10)), (C + u(250), C + u(230)), (x1, C + u(150))])
    for cx, rr in ((C - u(130), 85), (C + u(40), 70)):
        r = u(rr)
        cy = y0 - r - u(5)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=WHITE, width=LW)
        d.ellipse((cx - u(14), cy - u(14), cx + u(14), cy + u(14)), fill=GOLD)
    d.ellipse((x0 + u(40), y0 + u(40), x0 + u(80), y0 + u(80)), fill=GOLD)

def fikrlar(d):
    x0, y0, x1, y1 = C - u(250), C - u(190), C + u(250), C + u(130)
    d.rounded_rectangle((x0, y0, x1, y1), radius=u(70), outline=WHITE, width=LW)
    # tail
    d.line([(C - u(120), y1), (C - u(170), C + u(240)), (C - u(20), y1)], fill=WHITE, width=LW, joint="curve")
    d.line([(C - u(110), y1), (C - u(30), y1)], fill=BG, width=LW - u(6))
    for dx in (-140, 0, 140):
        star(d, C + u(dx), C - u(30), u(52), GOLD)

def klip(d):
    # clapperboard
    x0, y0, x1, y1 = C - u(230), C - u(60), C + u(230), C + u(230)
    d.rounded_rectangle((x0, y0, x1, y1), radius=u(24), outline=WHITE, width=LW)
    d.line([(x0, y0 + u(70)), (x1, y0 + u(70))], fill=WHITE, width=u(14))
    # tilted clapper
    a = math.radians(-14)
    px, py = x0, y0 - u(20)
    def R(x, y):
        return (px + x * math.cos(a) - y * math.sin(a), py + x * math.sin(a) + y * math.cos(a))
    w, h = u(460), u(85)
    poly_outline(d, [R(0, 0), R(w, 0), R(w, -h), R(0, -h)])
    for k in range(4):
        sx = u(40) + k * u(110)
        d.line([R(sx, -u(8)), R(sx + u(55), -h + u(8))], fill=GOLD, width=u(26))
    # play triangle
    d.polygon([(C - u(45), C + u(55)), (C - u(45), C + u(185)), (C + u(65), C + u(120))], fill=WHITE)

def bron(d):
    x0, y0, x1, y1 = C - u(230), C - u(180), C + u(230), C + u(230)
    d.rounded_rectangle((x0, y0, x1, y1), radius=u(40), outline=WHITE, width=LW)
    d.line([(x0, y0 + u(100)), (x1, y0 + u(100))], fill=WHITE, width=u(14))
    for dx in (-120, 120):
        d.line([(C + u(dx), y0 - u(60)), (C + u(dx), y0 + u(40))], fill=WHITE, width=LW)
    d.line([(C - u(110), C + u(85)), (C - u(25), C + u(165)), (C + u(130), C - u(5))], fill=GOLD, width=u(32), joint="curve")

ICONS = [("1_narxlar", "Narxlar", narxlar), ("2_toylar", "To'ylar", toylar), ("3_backstage", "Backstage", backstage),
         ("4_fikrlar", "Fikrlar", fikrlar), ("5_klip_reklama", "Klip & Reklama", klip), ("6_bron", "Bron", bron)]

thumbs = []
for fname, label, fn in ICONS:
    im, d = new()
    fn(d)
    sq = im.resize((1080, 1080), Image.LANCZOS)
    story = Image.new("RGB", (1080, 1920), (0, 0, 0))
    story.paste(sq.convert("RGB"), (0, 420))
    story.save(os.path.join(OUT, f"{fname}.png"))
    sq.convert("RGB").save(os.path.join(OUT, f"{fname}_kvadrat.png"))
    thumbs.append((label, sq.convert("RGB")))

# preview: how they look as highlight circles on a white profile
D, GAP = 220, 60
W = len(thumbs) * (D + GAP) + GAP
prev = Image.new("RGB", (W, D + 160), (255, 255, 255))
pd = ImageDraw.Draw(prev)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
for i, (label, sq) in enumerate(thumbs):
    x = GAP + i * (D + GAP); y = 40
    crop = sq.crop((140, 140, 940, 940)).resize((D, D), Image.LANCZOS)
    m = Image.new("L", (D * 4, D * 4), 0); ImageDraw.Draw(m).ellipse((0, 0, D * 4, D * 4), fill=255)
    prev.paste(crop, (x, y), m.resize((D, D), Image.LANCZOS))
    pd.ellipse((x - 8, y - 8, x + D + 8, y + D + 8), outline=(219, 219, 219), width=3)
    tw = pd.textlength(label, font=font)
    pd.text((x + D / 2 - tw / 2, y + D + 25), label, fill=(20, 20, 20), font=font)
prev.save(os.path.join(OUT, "preview_profil.png"))
print("ok")
