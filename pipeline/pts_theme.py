"""Tema for @pausetosolve-reels. Alt lages prosedyrisk i kode (ingen bilder utenfra).
  brass  – «Messingmaskin»: pergament, tannhjul som roterer, trykkmåler som nedtelling
  desk   – «Detektivbordet»: indekskort på trebord, stoppeklokke, rødt stempel
  nixie  – «Nixie-hvelvet»: stål, mørk glassplate, glødende nixie-rør
Rotasjon: theme_for_id(id) -> blokker på 5 id-er: brass, desk, nixie, brass, …"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1920
CX0, CY0, CW, CH = 70, 470, 940, 680          # kortet
TIMER_Y = 1360
LORA = "/usr/share/fonts/truetype/baskerville/Lora-Variable.ttf"
INTER = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
_fc = {}
def lora(size, wght=700):
    k = ("lora", size, wght)
    if k not in _fc:
        f = ImageFont.truetype(LORA, size)
        try: f.set_variation_by_axes([wght])
        except Exception: pass
        _fc[k] = f
    return _fc[k]
def inter(w, s):
    k = ("inter", w, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(INTER % w, s)
    return _fc[k]

THEMES = ["brass", "desk", "nixie"]
def theme_for_id(pid): return THEMES[((int(pid) - 1) // 5) % 3]

# ---------- teksturer ----------
def noise(h, w, scale, octaves=4, seed=0):
    r = np.random.default_rng(seed); out = np.zeros((h, w)); amp = 1; tot = 0
    for o in range(octaves):
        sh, sw = max(2, int(h / scale * 2 ** o)), max(2, int(w / scale * 2 ** o))
        small = Image.fromarray((r.random((sh, sw)) * 255).astype(np.uint8))
        out += np.asarray(small.resize((w, h), Image.BICUBIC), dtype=float) / 255 * amp; tot += amp; amp *= 0.5
    return out / tot
def brushed(h, w, seed=0, vertical=False):
    r = np.random.default_rng(seed)
    s = Image.fromarray((r.random((4, w) if vertical else (h, 4)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(s, dtype=float) / 255
def colorize(t, c0, c1):
    t = np.clip(t, 0, 1)[..., None]; return np.array(c0) * (1 - t) + np.array(c1) * t
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
def vignette(h, w, strength=0.6, power=2.2):
    y, x = np.mgrid[0:h, 0:w]; d = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2) / 1.42
    return 1 - strength * d ** power
def brass_tex(h, w, seed=1, dark=False):
    b = brushed(h, w, seed) * 0.55 + noise(h, w, 300, 4, seed + 5) * 0.45
    c0, c1 = ((70, 46, 18), (150, 108, 48)) if dark else ((150, 104, 40), (238, 196, 110))
    a = colorize(b, c0, c1); p = np.clip((noise(h, w, 220, 3, seed + 9) - 0.55) * 4, 0, 1)
    return a * (1 - 0.25 * p)[..., None] + np.array([40, 70, 60]) * 0.25 * p[..., None]
def copper_tex(h, w, seed=21):
    return colorize(brushed(h, w, seed) * 0.6 + noise(h, w, 300, 3, seed + 1) * 0.4, (110, 52, 28), (205, 120, 72))
def wood_tex(h, w, seed=2):
    y, x = np.mgrid[0:h, 0:w].astype(float)
    n = noise(h, w, 260, 4, seed); n2 = noise(h, w, 60, 3, seed + 3)
    rings = np.sin(x / 22 + n * 9 + y / 900) * 0.5 + 0.5
    t = rings ** 1.6 * 0.45 + brushed(h, w, seed + 7, vertical=True) * 0.35 + n2 * 0.2
    a = colorize(t, (52, 28, 14), (128, 74, 38))
    for px in range(0, w, 270): a[:, max(0, px - 2):px + 2] *= 0.45
    return a
def paper_tex(h, w, seed=4, tint=(238, 226, 196), edge=0.35):
    n = noise(h, w, 120, 5, seed); n2 = noise(h, w, 25, 2, seed + 1)
    a = np.array(tint, float) * (0.9 + 0.12 * n[..., None]) - 10 * n2[..., None]
    v = vignette(h, w, edge, 3.0)
    return a * v[..., None] + np.array([150, 110, 60]) * (1 - v[..., None]) * 0.6
def steel_tex(h, w, seed=6, k=1.0):
    b = brushed(h, w, seed, vertical=True) * 0.6 + noise(h, w, 200, 4, seed) * 0.4
    return colorize(b, (38, 42, 46), (92, 98, 104)) * k

def shadow(base, mask, off=(14, 22), blur=22, alpha=0.65):
    sh = Image.new("L", base.size, 0); sh.paste(mask, off)
    sh = sh.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha))
    base.paste(Image.new("RGB", base.size, (0, 0, 0)), (0, 0), sh)
def rrect_mask(w, h, r):
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255); return m
def bevel(base, box, r, light=60, dark=70, width=6):
    hl = Image.new("L", base.size, 0); ImageDraw.Draw(hl).rounded_rectangle(box, r, outline=255, width=width)
    yy = np.linspace(1, -1, base.size[1])[:, None]; m = np.asarray(hl, float) / 255
    arr = np.asarray(base.convert("RGB"), float)
    arr = arr + (np.clip(yy, 0, 1) * m)[..., None] * light - (np.clip(-yy, 0, 1) * m)[..., None] * dark
    out = to_img(arr)
    if base.mode == "RGBA": out.putalpha(base.getchannel("A"))
    base.paste(out)
def rivet(base, x, y, r=13):
    s = int(r * 4); yy, xx = np.mgrid[0:s, 0:s]
    dist = np.sqrt((xx - s / 2 + r * 0.35) ** 2 + (yy - s / 2 + r * 0.35) ** 2)
    a = np.zeros((s, s, 4)); a[..., :3] = colorize(np.clip(1 - dist / (r * 1.6), 0, 1), (90, 60, 25), (255, 230, 160))
    a[..., 3] = (np.sqrt((xx - s / 2) ** 2 + (yy - s / 2) ** 2) <= r) * 255
    rim = Image.new("L", (s, s), 0); ImageDraw.Draw(rim).ellipse((s / 2 - r, s / 2 - r + 3, s / 2 + r, s / 2 + r + 3), fill=150)
    base.paste(Image.new("RGB", (s, s), (0, 0, 0)), (int(x - s / 2), int(y - s / 2)), rim.filter(ImageFilter.GaussianBlur(3)))
    im = Image.fromarray(a.astype(np.uint8), "RGBA"); base.paste(im, (int(x - s / 2), int(y - s / 2)), im)
def ctext(d, cx, y, s, f, fill): d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill)
def engraved(d, cx, y, s, f, dark, light):
    w = d.textlength(s, font=f); d.text((cx - w / 2 + 2, y + 2), s, font=f, fill=light); d.text((cx - w / 2, y), s, font=f, fill=dark)

def gear_sprite(R, teeth, tex):
    """RGBA-tannhjul (sentrert) + skyggemaske."""
    S = int(R * 2 + 8); c = S / 2; m = Image.new("L", (S, S), 0); d = ImageDraw.Draw(m); pts = []
    for i in range(teeth * 4):
        a = i * 2 * math.pi / (teeth * 4); rr = R if (i % 4) in (1, 2) else R * 0.84
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    d.polygon(pts, fill=255); d.ellipse((c - R * 0.35, c - R * 0.35, c + R * 0.35, c + R * 0.35), fill=0)
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.6; r1 = R * 0.58
        d.ellipse((c + r1 * math.cos(a) - R * 0.14, c + r1 * math.sin(a) - R * 0.14, c + r1 * math.cos(a) + R * 0.14, c + r1 * math.sin(a) + R * 0.14), fill=0)
    t = tex.resize((S, S)) if tex.size != (S, S) else tex
    yy, xx = np.mgrid[0:S, 0:S]
    hl = np.clip(1 - np.sqrt((xx - c + R * 0.4) ** 2 + (yy - c + R * 0.4) ** 2) / (R * 1.4), 0, 1) ** 2 * 70
    rgb = to_img(np.asarray(t.convert("RGB"), float) + hl[..., None]); rgb.putalpha(m)
    return rgb, m

# =====================================================================
class Theme:
    name = "base"
    def font(self, s): return lora(s, 700)
    def font_text(self, s): return lora(s, 600)
    def animate(self, img, t): pass

# ---------------- Messingmaskin ----------------
class Brass(Theme):
    name = "brass"
    fg, op, q, ans, muted = (50, 30, 12), (140, 90, 40), (170, 40, 20), (30, 115, 50), (110, 70, 30)
    hl, tile, tile_q, line, nb = (170, 40, 20), (214, 196, 156), (140, 90, 40), (50, 30, 12), (160, 130, 90)
    sub, bottom = (250, 225, 170), (250, 225, 170)
    def __init__(self):
        self.tex = to_img(brass_tex(560, 560, 12)); self.cop = to_img(copper_tex(560, 560, 21))
        self.gears = [(40, 120, 230, 14, self.tex, 0.25), (1080, 330, 170, 11, self.cop, -0.35),
                      (30, 1830, 260, 16, self.cop, 0.2), (1040, 1700, 150, 10, self.tex, -0.4)]
        self.sprites = []
        for (_, _, R, n, tx, _) in self.gears:
            spr, m = gear_sprite(R, n, tx); pad = 30
            sh = Image.new("L", (m.width + 2 * pad, m.height + 2 * pad), 0); sh.paste(m, (pad, pad))
            self.sprites.append((spr, sh.filter(ImageFilter.GaussianBlur(10)).point(lambda v: v * 0.6), pad))
    def background(self):
        img = to_img(brass_tex(H, W, 11, dark=True) * vignette(H, W, 0.75, 2.0)[..., None])
        # kortskygge + pergament-ramme bakes inn
        m = Image.new("L", (W, H), 0); m.paste(rrect_mask(CW, CH, 10), (CX0, CY0)); shadow(img, m, (16, 26), 26, 0.8)
        # måler
        gx, gy, R = W // 2, TIMER_Y, 175
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse((gx - R - 26, gy - R - 26, gx + R + 26, gy + R + 26), fill=255)
        shadow(img, m, (12, 20), 20, 0.75); img.paste(to_img(brass_tex(H, W, 12)), (0, 0), m)
        bevel(img, (gx - R - 26, gy - R - 26, gx + R + 26, gy + R + 26), R + 26, 80, 90, 10)
        face = Image.new("L", (W, H), 0); ImageDraw.Draw(face).ellipse((gx - R, gy - R, gx + R, gy + R), fill=255)
        img.paste(to_img(paper_tex(H, W, 51, (242, 234, 214))), (0, 0), face)
        d = ImageDraw.Draw(img)
        for i in range(26):
            a = math.radians(225 - i * 10.8)
            d.line((gx + (R - 18) * math.cos(a), gy - (R - 18) * math.sin(a), gx + (R - 32) * math.cos(a), gy - (R - 32) * math.sin(a)), fill=(80, 56, 30), width=3)
        for i in range(6):
            a = math.radians(225 - i * 54); r1, r2 = R - 18, R - 48
            d.line((gx + r1 * math.cos(a), gy - r1 * math.sin(a), gx + r2 * math.cos(a), gy - r2 * math.sin(a)), fill=(40, 26, 12), width=7)
            s = str(5 - i); rr = R - 82; ft = lora(40, 700)
            d.text((gx + rr * math.cos(a) - d.textlength(s, font=ft) / 2, gy - rr * math.sin(a) - 26), s, font=ft, fill=(40, 26, 12))
        d.arc((gx - R + 14, gy - R + 14, gx + R - 14, gy + R - 14), 279, 315, fill=(190, 40, 30), width=10)
        ft = lora(22, 600); ctext(d, gx, gy + 104, "PRESSURE", ft, (110, 80, 50))
        return img
    def animate(self, img, t):
        for (x, y, R, n, tx, sp), (spr, sh, pad) in zip(self.gears, self.sprites):
            ang = math.degrees(t * sp) % 360
            s2, sh2 = spr.rotate(ang, resample=Image.BILINEAR), sh.rotate(ang, resample=Image.BILINEAR)
            ox, oy = int(x - spr.width / 2), int(y - spr.height / 2)
            img.paste((0, 0, 0), (ox + 10 - pad, oy + 16 - pad, ox + 10 - pad + sh2.width, oy + 16 - pad + sh2.height), sh2)
            img.paste(s2, (ox, oy), s2)
    def hook(self, img, text):
        f = lora(64, 700); d = ImageDraw.Draw(img); pw = int(min(1000, d.textlength(text, font=f) + 150)); ph = 128
        px, py = (W - pw) // 2, 205
        plate = to_img(brass_tex(ph, pw, 31)); m = rrect_mask(pw, ph, 18)
        full = Image.new("L", (W, H), 0); full.paste(m, (px, py)); shadow(img, full, (12, 18), 16, 0.7)
        img.paste(plate, (px, py), m); bevel(img, (px, py, px + pw, py + ph), 18, 70, 80, 7)
        for x in (px + 30, px + pw - 30): rivet(img, x, py + ph / 2, 11)
        engraved(ImageDraw.Draw(img), W / 2, py + 28, text, f, (58, 36, 12), (255, 235, 180))
    def card_base(self):
        c = to_img(paper_tex(CH, CW, 41)).convert("RGBA"); c.putalpha(rrect_mask(CW, CH, 10))
        for (x, y) in ((30, 30), (CW - 30, 30), (30, CH - 30), (CW - 30, CH - 30)): rivet(c, x, y, 15)
        return c
    def place(self, card): return card, (CX0, CY0)
    def timer(self, img, left, total):
        gx, gy, R = W // 2, TIMER_Y, 175; d = ImageDraw.Draw(img)
        v = max(0.0, min(5.0, left * 5.0 / total)); v = v + 0.06 * math.sin(left * 40) * (v > 0.05)
        a = math.radians(225 - (5 - v) * 54)
        d.line((gx + 3, gy + 5, gx + 3 + (R - 40) * math.cos(a), gy + 5 - (R - 40) * math.sin(a)), fill=(60, 40, 20), width=9)
        d.line((gx, gy, gx + (R - 40) * math.cos(a), gy - (R - 40) * math.sin(a)), fill=(150, 20, 15), width=9)
        rivet(img, gx, gy, 18)
    def plate_text(self, img, text, col, y=TIMER_Y + 210):
        f = lora(70, 700); d = ImageDraw.Draw(img); pw = int(d.textlength(text, font=f) + 110); ph = 120
        px, py = int(W / 2 - pw / 2), int(y - ph / 2)
        img.paste(to_img(brass_tex(ph, pw, 33)), (px, py), rrect_mask(pw, ph, 16)); bevel(img, (px, py, px + pw, py + ph), 16, 70, 80, 6)
        engraved(ImageDraw.Draw(img), W / 2, py + 20, text, f, col, (255, 235, 180))
    def timesup(self, img, k):
        self.timer(img, 0, 5)
        # damp
        if k < 1:
            st = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(st)
            for i in range(9):
                r = 40 + 120 * k + i * 6; x = W / 2 + math.sin(i * 1.7) * 110 * k; y = TIMER_Y - 190 - 260 * k - i * 14
                sd.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=int(150 * (1 - k)))
            img.paste(Image.new("RGB", (W, H), (240, 236, 228)), (0, 0), st.filter(ImageFilter.GaussianBlur(30)))
        self.plate_text(img, "TIME'S UP!", (150, 20, 15), TIMER_Y)
    def verdict(self, img, text, k):
        self.timer(img, 0, 5); self.plate_text(img, text, (30, 90, 40), TIMER_Y)

# ---------------- Detektivbordet ----------------
class Desk(Theme):
    name = "desk"
    fg, op, q, ans, muted = (25, 25, 60), (60, 60, 110), (200, 30, 30), (20, 130, 60), (90, 90, 110)
    hl, tile, tile_q, line, nb = (200, 30, 30), (226, 222, 206), (90, 90, 110), (25, 25, 60), (150, 160, 190)
    sub, bottom = (250, 240, 210), (250, 240, 210)
    ROT = 1.8
    GX = 300
    NOTE_X = 795
    def background(self):
        img = to_img(wood_tex(H, W) * vignette(H, W, 0.7, 2.0)[..., None])
        ring = Image.new("L", (W, H), 0); ImageDraw.Draw(ring).ellipse((640, 1150, 930, 1440), outline=255, width=16)
        img.paste(Image.new("RGB", (W, H), (35, 18, 8)), (0, 0), ring.filter(ImageFilter.GaussianBlur(5)).point(lambda v: v * 0.35))
        pen = Image.new("RGBA", (620, 40), (0, 0, 0, 0)); pd = ImageDraw.Draw(pen)
        pd.rectangle((60, 4, 560, 36), fill=(226, 172, 40)); pd.rectangle((60, 4, 560, 14), fill=(245, 205, 90))
        pd.polygon([(0, 20), (60, 4), (60, 36)], fill=(222, 190, 150)); pd.polygon([(0, 20), (18, 15), (18, 25)], fill=(40, 40, 40))
        pd.rectangle((560, 4, 590, 36), fill=(180, 180, 175)); pd.rectangle((590, 4, 620, 36), fill=(220, 120, 130))
        pen = pen.rotate(4, expand=True, resample=Image.BICUBIC)
        sh = Image.new("L", (W, H), 0); sh.paste(pen.getchannel("A"), (60, 1555))
        img.paste(Image.new("RGB", (W, H), (0, 0, 0)), (14, 22), sh.filter(ImageFilter.GaussianBlur(10)).point(lambda v: v * 0.6))
        img.paste(pen, (60, 1555), pen)
        # lapp der stempelet lander
        nw, nh = 440, 250; note = to_img(paper_tex(nh, nw, 95, (250, 248, 240), 0.2)).convert("RGBA")
        note = note.rotate(4, expand=True, resample=Image.BICUBIC); nx, ny = 575, TIMER_Y - 140
        sh = Image.new("L", (W, H), 0); sh.paste(note.getchannel("A"), (nx, ny)); shadow(img, sh, (10, 16), 14, 0.6)
        img.paste(note, (nx, ny), note)
        # kortskygge
        m = rrect_mask(CW, CH, 6).rotate(self.ROT, expand=True); full = Image.new("L", (W, H), 0)
        full.paste(m, (CX0 - (m.width - CW) // 2, CY0 - (m.height - CH) // 2)); shadow(img, full, (18, 30), 24, 0.7)
        # stoppeklokke-kropp
        gx, gy, R = self.GX, TIMER_Y, 150
        m = Image.new("L", (W, H), 0); md = ImageDraw.Draw(m)
        md.ellipse((gx - R - 22, gy - R - 22, gx + R + 22, gy + R + 22), fill=255); md.rounded_rectangle((gx - 26, gy - R - 70, gx + 26, gy - R), 10, fill=255)
        md.ellipse((gx - 40, gy - R - 110, gx + 40, gy - R - 40), fill=255)
        hole = Image.new("L", (W, H), 0); ImageDraw.Draw(hole).ellipse((gx - 20, gy - R - 92, gx + 20, gy - R - 58), fill=255)
        m = ImageChops.subtract(m, hole)
        chrome = to_img(colorize(brushed(H, W, 71) * 0.5 + noise(H, W, 150, 3, 72) * 0.5, (120, 120, 125), (240, 240, 245)))
        shadow(img, m, (14, 22), 18, 0.75); img.paste(chrome, (0, 0), m)
        face = Image.new("L", (W, H), 0); ImageDraw.Draw(face).ellipse((gx - R, gy - R, gx + R, gy + R), fill=255)
        img.paste(Image.new("RGB", (W, H), (248, 246, 240)), (0, 0), face)
        return img
    def hook(self, img, text):
        f = lora(58, 700); d = ImageDraw.Draw(img)
        label = text; pw = int(d.textlength(label, font=f) + 100); ph = 112
        tag = to_img(paper_tex(ph, pw, 91, (250, 248, 238), 0.2)).convert("RGBA"); td = ImageDraw.Draw(tag)
        td.text((50, 22), label, font=f, fill=(30, 30, 45))
        tag = tag.rotate(-1.5, expand=True, resample=Image.BICUBIC)
        px, py = (W - tag.width) // 2, 200
        sh = Image.new("L", (W, H), 0); sh.paste(tag.getchannel("A"), (px, py)); shadow(img, sh, (10, 16), 14, 0.7)
        img.paste(tag, (px, py), tag)
        tape = Image.new("RGBA", (180, 60), (240, 235, 200, 140)).rotate(-10, expand=True); img.paste(tape, (px - 40, py - 20), tape)
    def card_base(self):
        c = to_img(paper_tex(CH, CW, 61, (246, 242, 230), 0.25)).convert("RGBA"); d = ImageDraw.Draw(c)
        for y in range(110, CH - 20, 74): d.line((24, y, CW - 24, y), fill=(160, 192, 220), width=3)
        d.line((90, 0, 90, CH), fill=(220, 120, 120), width=3)
        c.putalpha(rrect_mask(CW, CH, 6)); return c
    def place(self, card):
        r = card.rotate(self.ROT, expand=True, resample=Image.BICUBIC)
        return r, (CX0 - (r.width - card.width) // 2, CY0 - (r.height - card.height) // 2)
    def tape(self, img):
        tp = Image.new("RGBA", (220, 66), (240, 235, 200, 150)).rotate(-12, expand=True); img.paste(tp, (430, CY0 - 40), tp)
    def timer(self, img, left, total, digit=True):
        gx, gy, R = self.GX, TIMER_Y, 150; d = ImageDraw.Draw(img); frac = max(0, left / total)
        if frac > 0: d.pieslice((gx - R + 12, gy - R + 12, gx + R - 12, gy + R - 12), -90, -90 + 360 * frac, fill=(255, 215, 200))
        for i in range(60):
            a = math.radians(90 - i * 6); r1 = R - 10; r2 = R - (30 if i % 5 == 0 else 20)
            d.line((gx + r1 * math.cos(a), gy - r1 * math.sin(a), gx + r2 * math.cos(a), gy - r2 * math.sin(a)), fill=(30, 30, 30), width=4 if i % 5 == 0 else 2)
        a = math.radians(90 - frac * 360)
        d.line((gx, gy, gx + (R - 30) * math.cos(a), gy - (R - 30) * math.sin(a)), fill=(200, 30, 30), width=6)
        d.ellipse((gx - 12, gy - 12, gx + 12, gy + 12), fill=(200, 30, 30))
        if digit:
            ctext(d, gx, gy - 108, str(max(0, math.ceil(left))), lora(64, 700), (30, 30, 30))
            ctext(d, self.NOTE_X, TIMER_Y - 70, f"{max(0, math.ceil(left))} sec", lora(76, 700), (200, 30, 30) if left <= 2 else (40, 40, 60))
    def stamp(self, img, text, col, k, rot=-9):
        fs = 72
        while fs > 34 and ImageDraw.Draw(img).textlength(text, font=lora(fs, 700)) > 330: fs -= 2
        f = lora(fs, 700); tmp = Image.new("RGBA", (900, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(tmp)
        w = d.textlength(text, font=f); d.rounded_rectangle((450 - w / 2 - 28, 110 - fs * 0.8, 450 + w / 2 + 28, 110 + fs * 0.8), 14, outline=col + (235,), width=8)
        d.text((450 - w / 2, 110 - fs * 0.62), text, font=f, fill=col + (235,))
        grit = (noise(220, 900, 18, 2, 5) > 0.22).astype(np.uint8) * 255
        tmp.putalpha(ImageChops.multiply(tmp.getchannel("A"), Image.fromarray(grit)))
        s = 1.35 - 0.35 * min(1, k * 4); tmp = tmp.rotate(rot, expand=True, resample=Image.BICUBIC)
        tmp = tmp.resize((int(tmp.width * s), int(tmp.height * s)), Image.BILINEAR)
        img.paste(tmp, (int(self.NOTE_X - tmp.width / 2), int(TIMER_Y - 12 - tmp.height / 2)), tmp)
    def timer_note(self, img, text):
        d = ImageDraw.Draw(img); f = lora(44, 600)
        ctext(d, self.NOTE_X, TIMER_Y - 40, text, f, (40, 40, 60))
    def timesup(self, img, k): self.timer(img, 0, 5, digit=False); self.stamp(img, "TIME'S UP!", (200, 30, 30), k)
    def verdict(self, img, text, k): self.timer(img, 0, 5, digit=False); self.stamp(img, text, (20, 120, 55), k, rot=-6)

# ---------------- Nixie-hvelvet ----------------
class Nixie(Theme):
    name = "nixie"
    fg, op, q, ans, muted = (235, 238, 242), (120, 128, 140), (255, 140, 40), (90, 230, 140), (160, 168, 180)
    hl, tile, tile_q, line, nb = (255, 140, 40), (34, 38, 48), (120, 128, 140), (235, 238, 242), (70, 80, 100)
    sub, bottom = (200, 205, 210), (235, 238, 242)
    TW, TH = 170, 300
    def font(self, s): return inter("Black", s)
    def font_text(self, s): return inter("SemiBold", s)
    def __init__(self): self._tubes = {}
    def background(self):
        img = to_img(steel_tex(H, W) * vignette(H, W, 0.8, 1.8)[..., None])
        for x in range(60, W, 160):
            for y in (60, H - 60): rivet(img, x, y, 12)
        cx, cy = W // 2, CY0 + CH // 2
        ring = Image.new("L", (W, H), 0); ImageDraw.Draw(ring).ellipse((cx - 520, cy - 520, cx + 520, cy + 520), outline=255, width=50)
        shadow(img, ring, (10, 16), 16, 0.7); img.paste(to_img(steel_tex(H, W, 9, 1.35)), (0, 0), ring)
        m = Image.new("L", (W, H), 0); m.paste(rrect_mask(CW, CH, 30), (CX0, CY0)); shadow(img, m, (14, 22), 24, 0.85)
        # rørholdere
        for i in range(2):
            x = W // 2 - self.TW - 15 + i * (self.TW + 30)
            m = Image.new("L", (W, H), 0); m.paste(rrect_mask(self.TW, self.TH, self.TW // 2), (x, TIMER_Y - 170)); shadow(img, m, (8, 14), 14, 0.8)
        return img
    def hook(self, img, text):
        f = inter("Black", 60); d = ImageDraw.Draw(img); pw = int(min(1000, d.textlength(text, font=f) + 100)); ph = 120
        px, py = (W - pw) // 2, 200
        m = rrect_mask(pw, ph, 14); full = Image.new("L", (W, H), 0); full.paste(m, (px, py)); shadow(img, full, (10, 16), 14, 0.7)
        img.paste(to_img(steel_tex(ph, pw, 13, 1.5)), (px, py), m); bevel(img, (px, py, px + pw, py + ph), 14, 60, 70, 6)
        engraved(ImageDraw.Draw(img), W / 2, py + 24, text, f, (28, 30, 34), (210, 214, 218))
    def card_base(self):
        c = to_img(colorize(noise(CH, CW, 300, 3, 81), (10, 12, 16), (26, 30, 38))).convert("RGBA"); c.putalpha(rrect_mask(CW, CH, 30))
        bevel(c, (0, 0, CW - 1, CH - 1), 30, 50, 60, 8); return c
    def place(self, card): return card, (CX0, CY0)
    def tube(self, digit, level=1.0, col=(255, 120, 30)):
        key = (digit, round(level, 2), col)
        if key in self._tubes: return self._tubes[key]
        w, h = self.TW, self.TH; img = Image.new("RGB", (w + 80, h + 80), (0, 0, 0)); x, y = 40, 40
        tube = rrect_mask(w, h, w // 2)
        yy, xx = np.mgrid[0:h, 0:w]; glass = np.zeros((h, w, 3)) + np.array([24, 20, 18])
        glass += (np.clip(1 - np.abs(xx - w * 0.3) / (w * 0.12), 0, 1) * 40)[..., None]
        img.paste(to_img(glass), (x, y), tube); d = ImageDraw.Draw(img); f = inter("ExtraLight", int(h * 0.62))
        for k in "0123456789": d.text((x + w / 2 - d.textlength(k, font=f) / 2, y + h * 0.12), k, font=f, fill=(58, 46, 38))
        if digit is not None and level > 0:
            glow = Image.new("L", img.size, 0); ImageDraw.Draw(glow).text((x + w / 2 - d.textlength(digit, font=f) / 2, y + h * 0.12), digit, font=f, fill=255)
            for rad, a in ((30, 2.0), (10, 2.0), (3, 1.0)):
                img.paste(Image.new("RGB", img.size, col), (0, 0), glow.filter(ImageFilter.GaussianBlur(rad)).point(lambda v: min(255, v * a * level)))
            hot = tuple(min(255, c + 100) for c in col)
            img.paste(Image.new("RGB", img.size, hot), (0, 0), glow.filter(ImageFilter.GaussianBlur(1)).point(lambda v: v * level))
        mesh = Image.new("L", (w, h), 0); md = ImageDraw.Draw(mesh)
        for i in range(-h, w + h, 14): md.line((i, 0, i + h, h), fill=40); md.line((i + h, 0, i, h), fill=40)
        mm = Image.new("L", img.size, 0); mm.paste(ImageChops.multiply(mesh, tube), (x, y)); img.paste(Image.new("RGB", img.size, (0, 0, 0)), (0, 0), mm)
        hl = Image.new("L", img.size, 0); ImageDraw.Draw(hl).rounded_rectangle((x + w * 0.18, y + 20, x + w * 0.3, y + h - 40), 20, fill=60)
        img.paste(Image.new("RGB", img.size, (255, 255, 255)), (0, 0), hl.filter(ImageFilter.GaussianBlur(6)))
        a = Image.new("L", img.size, 0); a.paste(tube, (x, y)); a = ImageChops.lighter(a, img.convert("L").point(lambda v: min(255, v * 3)))
        out = img.convert("RGBA"); out.putalpha(a); self._tubes[key] = out; return out
    def tubes(self, img, d1, d2, level=1.0, col=(255, 120, 30)):
        for i, dg in enumerate((d1, d2)):
            t = self.tube(dg, level, col); x = W // 2 - self.TW - 15 + i * (self.TW + 30) - 40
            img.paste(t, (x, TIMER_Y - 170 - 40), t)
    def lamps(self, img, red, green):
        for i, (on, col) in enumerate(((red, (255, 60, 40)), (green, (60, 230, 120)))):
            lx, ly = W // 2 - 60 + i * 120, TIMER_Y + 205
            lm = Image.new("L", (W, H), 0); ImageDraw.Draw(lm).ellipse((lx - 24, ly - 24, lx + 24, ly + 24), fill=255)
            if on: img.paste(Image.new("RGB", (W, H), col), (0, 0), lm.filter(ImageFilter.GaussianBlur(24)).point(lambda v: v * 0.8))
            img.paste(Image.new("RGB", (W, H), col if on else (55, 58, 62)), (0, 0), lm)
    def timer(self, img, left, total):
        n = max(0, math.ceil(left)); fr = math.ceil(left) - left
        level = 0.35 if fr > 0.93 else 1.0          # flimmer ved bytte
        self.tubes(img, "0", str(n), level); self.lamps(img, red=(left <= 2 and int(left * 4) % 2 == 0), green=False)
    def timesup(self, img, k):
        self.tubes(img, "0", "0", 1.0 if int(k * 8) % 2 == 0 else 0.4); self.lamps(img, True, False)
    def verdict(self, img, text, k):
        self.lamps(img, False, True)
        d = ImageDraw.Draw(img); f = inter("Black", 84)
        bx = d.textlength(text, font=f) + 80
        d.rounded_rectangle((W / 2 - bx / 2, TIMER_Y - 70, W / 2 + bx / 2, TIMER_Y + 50), 24, fill=(10, 14, 18))
        ctext(d, W / 2, TIMER_Y - 62, text, f, self.ans)

def make(name): return {"brass": Brass, "desk": Desk, "nixie": Nixie}[name]()
