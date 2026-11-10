import math, random, subprocess, os, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
SR = 44100
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
GOLD = (232, 196, 120)
WHITE = (255, 248, 238)
RED = (230, 70, 80)

def F(path, size): return ImageFont.truetype(path, size)

# ---------- voice ----------
lines = [
    "Hayotingizdagi eng muhim kun, faqat bir marta boʻladi.",
    "Dekabr oyi uchun, maxsus aksiya!",
    "Uch yuz dollarlik toʻy videosi, endi atigi, uch million soʻm!",
    "Professional suratga olish, chiroyli montaj, va unutilmas xotiralar.",
    "Shoshiling! Joylar soni cheklangan.",
    "Toʻy sanangizni, hoziroq band qiling!",
]
def read_wav(p):
    with wave.open(p) as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if sr != SR:
        x = np.linspace(0, len(a) - 1, int(len(a) * SR / sr))
        a = np.interp(x, np.arange(len(a)), a)
    return a

if os.environ.get("NATURAL_VOICE"):
    subprocess.run(["python3", f"{OUT}/tts.py", f"{OUT}/mms_uzb", f"{OUT}/lines_cyr.txt", OUT], check=True)
voices = []
for i, t in enumerate(lines):
    p = f"{OUT}/v{i}.wav"
    if not os.environ.get("NATURAL_VOICE"):
        subprocess.run(["espeak-ng", "-v", "uz", "-s", "128", "-p", "40", "-a", "180", "-w", p, t.replace("ʻ", "'")], check=True)
    voices.append(read_wav(p))

PAD_START, PAD_END = 0.5, 0.9
durs = [PAD_START + len(v) / SR + PAD_END for v in voices]
durs[-1] += 2.0  # hold the final card
starts = np.cumsum([0] + durs[:-1])
TOTAL = sum(durs)

# ---------- music: soft pad + bell plucks ----------
n = int(TOTAL * SR)
t = np.arange(n) / SR
music = np.zeros(n, dtype=np.float32)
def note(f): return 440 * 2 ** ((f - 69) / 12)
chords = [[57, 61, 64, 69], [54, 57, 61, 66], [50, 54, 57, 62], [52, 56, 59, 64]]  # A F#m D E
CH = 3.2
for ci in range(int(TOTAL / CH) + 2):
    ch = chords[ci % 4]
    s0 = int(ci * CH * SR); s1 = min(n, int((ci + 1) * CH * SR + 0.8 * SR))
    if s0 >= n: break
    tt = np.arange(s1 - s0) / SR
    env = np.minimum(1, tt / 0.8) * np.minimum(1, np.maximum(0, (CH + 0.8 - tt) / 0.8))
    seg = sum(np.sin(2 * np.pi * note(m) * tt) + 0.3 * np.sin(4 * np.pi * note(m) * tt) for m in ch)
    music[s0:s1] += 0.05 * env * seg
    for k, m in enumerate([ch[3] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12]):
        b0 = s0 + int(k * CH / 4 * SR); bl = int(1.5 * SR)
        if b0 + bl > n: continue
        bt = np.arange(bl) / SR
        music[b0:b0 + bl] += 0.06 * np.exp(-bt * 3) * np.sin(2 * np.pi * note(m) * bt)
fade = np.minimum(1, t / 1.0) * np.minimum(1, (TOTAL - t) / 1.5)
music *= fade
voice_track = np.zeros(n, dtype=np.float32)
for v, s in zip(voices, starts):
    a = int((s + PAD_START) * SR)
    voice_track[a:a + len(v)] += v[: n - a]
# duck music under the voice
envv = np.convolve(np.abs(voice_track), np.ones(4410) / 4410, mode="same")
duck = 1 - 0.55 * np.clip(envv * 12, 0, 1)
mix = voice_track * 1.0 + music * duck
mix = mix / max(1e-6, np.abs(mix).max()) * 0.9
with wave.open(f"{OUT}/audio.wav", "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())

# ---------- visuals ----------
yy = np.linspace(0, 1, H)[:, None]
top, bot = np.array([18, 16, 40]), np.array([70, 14, 34])
grad = (top * (1 - yy) + bot * yy)[:, :, None].repeat(1, 2)
bg_arr = np.broadcast_to((top * (1 - yy[..., None]) + bot * yy[..., None]), (H, W, 3)).astype(np.uint8)
BG = Image.fromarray(bg_arr.copy())
# vignette glow
glow = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(glow)
gd.ellipse([-200, 500, W + 200, 1500], fill=70)
glow = glow.filter(ImageFilter.GaussianBlur(180))
BG = Image.composite(Image.new("RGB", (W, H), (150, 90, 60)), BG, glow)

random.seed(3)
flakes = [[random.uniform(0, W), random.uniform(0, H), random.uniform(2, 7), random.uniform(40, 120), random.uniform(0, 6.28)] for _ in range(140)]

def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def text_layer(draw_fn):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); draw_fn(ImageDraw.Draw(L)); return L
def ctext(d, y, s, font, fill, shadow=True):
    w = d.textlength(s, font=font)
    if shadow: d.text(((W - w) / 2 + 3, y + 4), s, font=font, fill=(0, 0, 0, 140))
    d.text(((W - w) / 2, y), s, font=font, fill=fill)
def put(frame, layer, alpha, dy=0, scale=1.0):
    if alpha <= 0: return
    if scale != 1.0:
        sw, sh = int(W * scale), int(H * scale)
        layer = layer.resize((sw, sh), Image.LANCZOS)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); c.paste(layer, ((W - sw) // 2, (H - sh) // 2)); layer = c
    if dy: layer = layer.transform(layer.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy))
    if alpha < 1:
        a = layer.getchannel("A").point(lambda p: int(p * alpha)); layer.putalpha(a)
    frame.alpha_composite(layer)

def rings(d, cx, cy, r):
    for ox in (-r * 0.55, r * 0.55):
        d.ellipse([cx + ox - r, cy - r, cx + ox + r, cy + r], outline=GOLD + (255,), width=14)
    d.polygon([(cx + r * 0.55, cy - r - 60), (cx + r * 0.55 - 28, cy - r - 25), (cx + r * 0.55, cy - r - 5), (cx + r * 0.55 + 28, cy - r - 25)], fill=(220, 240, 255, 255))

def frame_line(d, y):
    d.line([(W / 2 - 220, y), (W / 2 + 220, y)], fill=GOLD + (200,), width=3)
    d.ellipse([W / 2 - 9, y - 9, W / 2 + 9, y + 9], fill=GOLD + (255,))

# pre-built layers
L = {}
L["s0a"] = text_layer(lambda d: rings(d, W / 2, 620, 120))
L["s0b"] = text_layer(lambda d: (ctext(d, 860, "Hayotingizdagi", F(SERIF, 92), WHITE), ctext(d, 980, "eng muhim kun", F(SERIF, 92), WHITE)))
L["s0c"] = text_layer(lambda d: (frame_line(d, 1150), ctext(d, 1210, "faqat bir marta boʻladi…", F(SANS_R, 60), GOLD)))
L["s1a"] = text_layer(lambda d: (ctext(d, 700, "❄", F(SANS_R, 160), (220, 240, 255)),))
L["s1b"] = text_layer(lambda d: (ctext(d, 920, "DEKABR", F(SERIF, 190), GOLD), ctext(d, 1140, "AKSIYASI", F(SERIF, 130), WHITE)))
def price_old(d):
    f = F(SERIF, 200); s = "300$"; w = d.textlength(s, font=f)
    ctext(d, 560, s, f, (200, 190, 200))
L["s2a"] = text_layer(price_old)
def strike(p):
    def fn(d):
        f = F(SERIF, 200); w = d.textlength("300$", font=f); x0 = (W - w) / 2 - 30
        d.line([(x0, 720), (x0 + (w + 60) * p, 660)], fill=RED + (255,), width=18)
    return text_layer(fn)
L["s2c"] = text_layer(lambda d: (ctext(d, 880, "endi atigi", F(SANS_R, 64), WHITE),))
def newprice(d):
    d.rounded_rectangle([90, 990, W - 90, 1290], radius=40, fill=(232, 196, 120, 255))
    s = "3 000 000"; f = F(SERIF, 140); w = d.textlength(s, font=f)
    d.text(((W - w) / 2, 1025), s, font=f, fill=(60, 14, 30))
    s2 = "soʻm"; f2 = F(SANS, 70); w2 = d.textlength(s2, font=f2)
    d.text(((W - w2) / 2, 1195), s2, font=f2, fill=(60, 14, 30))
L["s2d"] = text_layer(newprice)
L["s3t"] = text_layer(lambda d: (ctext(d, 520, "Sizga nima", F(SERIF, 96), WHITE), ctext(d, 630, "beramiz?", F(SERIF, 96), GOLD)))
items = ["Professional suratga olish", "Chiroyli montaj", "Unutilmas xotiralar"]
def item(i):
    def fn(d):
        y = 880 + i * 190
        d.rounded_rectangle([90, y, W - 90, y + 140], radius=30, fill=(255, 255, 255, 30), outline=GOLD + (180,), width=3)
        d.ellipse([130, y + 40, 190, y + 100], fill=GOLD + (255,))
        d.line([(145, y + 70), (158, y + 85), (178, y + 55)], fill=(60, 14, 30, 255), width=8)
        d.text((235, y + 40), items[i], font=F(SANS, 50), fill=WHITE)
    return text_layer(fn)
for i in range(3): L[f"s3i{i}"] = item(i)
L["s4a"] = text_layer(lambda d: (ctext(d, 760, "SHOSHILING!", F(SERIF, 118), GOLD),))
def limited(d):
    d.rounded_rectangle([140, 1000, W - 140, 1150], radius=75, fill=RED + (235,))
    ctext(d, 1042, "Joylar soni cheklangan", F(SANS, 52), WHITE, shadow=False)
L["s4b"] = text_layer(limited)
L["s5a"] = text_layer(lambda d: (rings(d, W / 2, 470, 90), ctext(d, 680, "Toʻy sanangizni", F(SERIF, 96), WHITE), ctext(d, 795, "hoziroq band qiling!", F(SERIF, 76), GOLD)))
def contact(d):
    d.rounded_rectangle([110, 1010, W - 110, 1420], radius=40, fill=(0, 0, 0, 90), outline=GOLD + (200,), width=3)
    ctext(d, 1050, "☎  +998 __ ___ __ __", F(SANS, 64), WHITE)
    ctext(d, 1170, "@instagram_sahifangiz", F(SANS_R, 56), GOLD)
    ctext(d, 1290, "Direct’ga «DEKABR» deb yozing", F(SANS_R, 46), WHITE)
L["s5b"] = text_layer(contact)

def scene(i, lt, f):
    d = durs[i]
    out = ease((d - lt) / 0.4) if i < 5 else 1.0
    a = lambda t0: ease((lt - t0) / 0.6) * out
    s = lambda t0: (1 - ease((lt - t0) / 0.6)) * 60
    if i == 0:
        put(f, L["s0a"], a(0.1), s(0.1)); put(f, L["s0b"], a(0.5), s(0.5)); put(f, L["s0c"], a(1.6), s(1.6))
    elif i == 1:
        put(f, L["s1a"], a(0.0), s(0.0)); put(f, L["s1b"], a(0.3), scale=0.85 + 0.15 * ease((lt - 0.3) / 0.7))
    elif i == 2:
        put(f, L["s2a"], a(0.0), s(0.0))
        p = ease((lt - 1.0) / 0.5)
        if p > 0: put(f, strike(p), out)
        put(f, L["s2c"], a(1.7), s(1.7))
        k = ease((lt - 2.2) / 0.5); pulse = 1 + 0.025 * math.sin(lt * 6) * k
        put(f, L["s2d"], k * out, scale=(0.6 + 0.4 * k) * pulse)
    elif i == 3:
        put(f, L["s3t"], a(0.0), s(0.0))
        for j in range(3): put(f, L[f"s3i{j}"], a(0.6 + j * 1.2), s(0.6 + j * 1.2))
    elif i == 4:
        put(f, L["s4a"], a(0.0), scale=0.8 + 0.2 * ease(lt / 0.5) + 0.03 * math.sin(lt * 9))
        put(f, L["s4b"], a(0.7), s(0.7))
    else:
        put(f, L["s5a"], a(0.0), s(0.0)); put(f, L["s5b"], a(0.8), s(0.8))
        fo = 1 - ease((lt - (d - 0.8)) / 0.8)
        if fo < 1:
            blk = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - fo)))); f.alpha_composite(blk)

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-i", f"{OUT}/audio.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                       "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", f"{OUT}/dekabr_aksiya.mp4"], stdin=subprocess.PIPE)
NF = int(TOTAL * FPS)
for fi in range(NF):
    tsec = fi / FPS
    f = BG.copy().convert("RGBA")
    sd = ImageDraw.Draw(f)
    for fl in flakes:
        x = (fl[0] + 25 * math.sin(tsec * 0.8 + fl[4])) % W
        y = (fl[1] + fl[3] * tsec) % H
        r = fl[2]; sd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, int(60 + r * 18)))
    i = int(np.searchsorted(starts, tsec, side="right") - 1)
    scene(i, tsec - starts[i], f)
    ff.stdin.write(f.convert("RGB").tobytes())
ff.stdin.close(); ff.wait()
print("done", TOTAL)
