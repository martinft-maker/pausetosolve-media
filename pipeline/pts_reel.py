#!/usr/bin/env python3
"""@pausetosolve – hjernetrim-reels. Tre tema (pts_theme.py) i blokker på 5: brass, desk, nixie.
Én gåte = én linje i pipeline/puzzles.jsonl. Serier:
  A emoji-likning · B finn den som skiller seg ut · C tallrekke · D gåte i tekst · E synsbedrag · F hukommelse
Bruk: pts_reel.py BANK.jsonl ID [ID ...] OUTDIR      (lager OUTDIR/pausetosolve_NNN.mp4)
      pts_reel.py --still BANK.jsonl ID OUT.png T     (ett bilde ved tid T, for kontroll)"""
import sys, os, re, json, math, subprocess, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pts_theme

HANDLE = "pausetosolve"
W, H, FPS = 1080, 1920, 30
NAVY, GRIDC, CARD, CARDLINE = (11, 16, 38), (18, 25, 54), (20, 28, 64), (46, 60, 120)
YEL, WHITE, MUTED, OPC, GREEN, RED = (255, 222, 0), (255, 255, 255), (160, 172, 220), (120, 136, 200), (60, 220, 120), (255, 80, 90)
INTER = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
CX0, CY0, CW, CH = pts_theme.CX0, pts_theme.CY0, pts_theme.CW, pts_theme.CH
RING_Y = pts_theme.TIMER_Y
T = None   # aktivt tema
def set_theme(name):
    global T, WHITE, OPC, YEL, GREEN, MUTED
    T = pts_theme.make(name); WHITE, OPC, YEL, GREEN, MUTED = T.fg, T.op, T.q, T.ans, T.muted
    return T
_f = {}
def F(w, s):
    if T is not None:
        return T.font(s) if w in ("Black", "Bold") else T.font_text(s)
    if (w, s) not in _f: _f[(w, s)] = ImageFont.truetype(INTER % w, s)
    return _f[(w, s)]

# ---------- emoji ----------
_em = ImageFont.truetype(EMOJI, 109)
EMO = re.compile("((?:[\U0001F000-\U0001FAFF☀-➿⬀-⯿⌀-⏿]️?(?:‍[\U0001F000-\U0001FAFF☀-➿]️?)*)+)")
_ec = {}
def emoji(ch, size):
    if (ch, size) not in _ec:
        im = Image.new("RGBA", (400, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 0), ch, font=_em, embedded_color=True)
        bb = im.getbbox(); im = im.crop(bb)
        s = size / max(im.width, im.height)
        im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
        out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); out.paste(im, ((size - im.width) // 2, (size - im.height) // 2), im)
        _ec[(ch, size)] = out
    return _ec[(ch, size)]
def is_emo(s): return bool(EMO.fullmatch(s))
def emo_chars(s): return re.findall("[^️‍](?:️)?(?:‍[^️‍]️?)*", s)

def rich_width(d, text, font):
    w = 0
    for p in EMO.split(text):
        if not p: continue
        w += len(emo_chars(p)) * int(font.size * 1.05) if is_emo(p) else d.textlength(p, font=font)
    return w
def rich(img, d, x, y, text, font, fill):
    for p in EMO.split(text):
        if not p: continue
        if is_emo(p):
            for ch in emo_chars(p):
                e = emoji(ch, int(font.size * 0.95)); img.paste(e, (int(x), int(y + font.size * 0.1)), e); x += int(font.size * 1.05)
        else:
            d.text((x, y), p, font=font, fill=fill); x += d.textlength(p, font=font)
def rich_c(img, d, cx, y, text, font, fill):
    rich(img, d, cx - rich_width(d, text, font) / 2, y, text, font, fill)
def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if rich_width(d, t, font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines
def fit_lines(d, text, weight, maxw, maxh, start=72, minsize=34, lh=1.22):
    s = start
    while s > minsize:
        f = F(weight, s); ls = wrap(d, text, f, maxw)
        if len(ls) * s * lh <= maxh and all(rich_width(d, l, f) <= maxw for l in ls): return f, ls
        s -= 2
    f = F(weight, minsize); return f, wrap(d, text, f, maxw)

# ---------- bakgrunn ----------
def background():
    img = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(img)
    for x in range(0, W, 60): d.line((x, 0, x, H), fill=GRIDC, width=2)
    for y in range(0, H, 60): d.line((0, y, W, y), fill=GRIDC, width=2)
    f = F("Bold", 34); t = "@" + HANDLE; d.text((W / 2 - d.textlength(t, font=f) / 2, 168), t, font=f, fill=(70, 84, 140))
    return img

def new_card():
    c = T.card_base(); return c, ImageDraw.Draw(c)

# ---------- serie A: emoji-likning ----------
def card_A(p, reveal):
    c, d = new_card(); rows = p["rows"] + [p["q"]]
    n = len(rows); size = 104 if n <= 4 else 88; gap = (CH - 70) / n
    opf = F("Black", int(size * 0.8))
    for r, toks in enumerate(rows):
        y = 35 + r * gap + (gap - size) / 2
        ws = [size + 6 if is_emo(t) else d.textlength(t, font=opf) + 30 for t in toks]
        if r == n - 1 and reveal: ws[-1] = d.textlength(str(p["answer"]), font=opf) + 30
        x = CW / 2 - sum(ws) / 2
        for t, w in zip(toks, ws):
            if is_emo(t):
                e = emoji(t, size); c.paste(e, (int(x + 3), int(y)), e)
            else:
                col = WHITE
                if t in ("+", "=", "×", "−", "-"): col = OPC
                if t == "?":
                    t, col = (str(p["answer"]), GREEN) if reveal else ("?", YEL)
                d.text((x + 15, y + size / 2 - opf.size * 0.62), t, font=opf, fill=col)
            x += w
    return c

# ---------- serie B: finn den som skiller seg ut ----------
def card_B(p, reveal):
    c, d = new_card(); R, C = p["rows"], p["cols"]
    cell = min((CW - 60) / C, (CH - 60) / R); size = int(cell * 0.86)
    ox, oy = (CW - cell * C) / 2, (CH - cell * R) / 2
    rr, cc = p["pos"]
    for r in range(R):
        for k in range(C):
            ch = p["odd"] if (r, k) == (rr, cc) else p["base"]
            e = emoji(ch, size)
            if reveal and (r, k) != (rr, cc):
                e = e.copy(); a = e.getchannel("A").point(lambda v: v * 0.22); e.putalpha(a)
            c.paste(e, (int(ox + k * cell + (cell - size) / 2), int(oy + r * cell + (cell - size) / 2)), e)
    if reveal:
        x, y = ox + cc * cell + cell / 2, oy + rr * cell + cell / 2; rad = cell * 0.68
        d.ellipse((x - rad, y - rad, x + rad, y + rad), outline=YEL + (255,), width=9)
    return c

# ---------- serie C: tallrekke ----------
def card_C(p, reveal):
    c, d = new_card(); seq = [str(v) for v in p["seq"]]
    if reveal: seq = [str(p["answer"]) if v == "?" else v for v in seq]
    lines = [seq] if len(seq) <= 4 else [seq[: (len(seq) + 1) // 2], seq[(len(seq) + 1) // 2:]]
    s = 150 if len(seq) <= 4 else 132
    while True:
        f = F("Black", s); ws = [sum(d.textlength(v, font=f) for v in ln) + d.textlength(", ", font=f) * (len(ln) - 1) for ln in lines]
        if max(ws) <= CW - 90 or s < 60: break
        s -= 6
    top = (CH - len(lines) * s * 1.3) / 2 - (40 if reveal else 0)
    for i, ln in enumerate(lines):
        x = CW / 2 - ws[i] / 2; y = top + i * s * 1.3
        for j, v in enumerate(ln):
            col = YEL if v == "?" else (GREEN if (reveal and v == str(p["answer"]) and i == len(lines) - 1 and j == len(ln) - 1) else WHITE)
            d.text((x, y), v, font=f, fill=col); x += d.textlength(v, font=f)
            if j < len(ln) - 1: d.text((x, y), ", ", font=f, fill=OPC); x += d.textlength(", ", font=f)
    if reveal and p.get("explain"):
        ef = F("Bold", 50); t = p["explain"]; d.text((CW / 2 - d.textlength(t, font=ef) / 2, CH - 130), t, font=ef, fill=YEL)
    return c

# ---------- serie D: gåte i tekst ----------
def card_D(p, reveal):
    c, d = new_card()
    if not reveal:
        f, ls = fit_lines(d, p["question"], "Bold", CW - 120, CH - 120, start=76)
        top = (CH - len(ls) * f.size * 1.22) / 2
        for i, l in enumerate(ls): rich_c(c, d, CW / 2, top + i * f.size * 1.22, l, f, WHITE)
    else:
        f, ls = fit_lines(d, p["question"], "SemiBold", CW - 120, 230, start=46, minsize=30)
        for i, l in enumerate(ls): rich_c(c, d, CW / 2, 60 + i * f.size * 1.22, l, f, MUTED)
        af, als = fit_lines(d, p["answer"], "Black", CW - 120, 300, start=120, minsize=50, lh=1.15)
        top = 300 + (300 - len(als) * af.size * 1.15) / 2
        for i, l in enumerate(als): rich_c(c, d, CW / 2, top + i * af.size * 1.15, l, af, GREEN)
    return c

# ---------- serie E: synsbedrag ----------
def card_E(p, reveal):
    c, d = new_card(); k = p["kind"]; col = tuple(p.get("color", [255, 120, 60]))
    lab = F("Black", 64)
    if k == "muller":   # Müller-Lyer: to like lange linjer
        L = p.get("len", 520); x0 = (CW - L) / 2; ys = [210, 470]; fins = [1, -1] if p.get("flip") else [-1, 1]
        for y, s, name in zip(ys, fins, "AB"):
            d.line((x0, y, x0 + L, y), fill=WHITE, width=12)
            for xe, dirx in ((x0, 1), (x0 + L, -1)):
                dx = 70 * dirx * s
                d.line((xe, y, xe + dx, y - 70), fill=WHITE, width=12); d.line((xe, y, xe + dx, y + 70), fill=WHITE, width=12)
            d.text((40, y - 40), name, font=lab, fill=YEL)
        if reveal:
            for xe in (x0, x0 + L):
                for yy in range(120, 570, 30): d.line((xe, yy, xe, yy + 16), fill=GREEN, width=6)
    elif k == "ebbinghaus":   # to like store sirkler, ulike naboer
        r = 52; cy = CH / 2
        for cxp, ring_r, nb, name in ((CW * 0.27, 150, 70, "A"), (CW * 0.73, 95, 22, "B")):
            n = 6 if nb > 40 else 8
            for i in range(n):
                a = 2 * math.pi * i / n; x, y = cxp + ring_r * math.cos(a), cy + ring_r * math.sin(a)
                d.ellipse((x - nb, y - nb, x + nb, y + nb), fill=T.nb)
            d.ellipse((cxp - r, cy - r, cxp + r, cy + r), fill=col)
            d.text((cxp - 20, CH - 95), name, font=lab, fill=YEL)
        if reveal:
            for cxp in (CW * 0.27, CW * 0.73):
                for yy in (cy - r, cy + r): d.line((cxp - 80, yy, cxp + 80, yy), fill=GREEN, width=6)
    elif k == "contrast":     # samme grå på ulik bakgrunn
        g = Image.linear_gradient("L").rotate(90, expand=True).resize((CW - 80, CH - 160))
        if p.get("flip"): g = g.transpose(Image.FLIP_LEFT_RIGHT)
        c.paste(Image.merge("RGB", (g, g, g)), (40, 40))
        v = p.get("gray", 128); sq = 150
        for fx, name in ((0.22, "A"), (0.78, "B")):
            x = 40 + (CW - 80) * fx - sq / 2; y = 40 + (CH - 160) / 2 - sq / 2
            d.rectangle((x, y, x + sq, y + sq), fill=(v, v, v))
            d.text((x + sq / 2 - 20, CH - 105), name, font=lab, fill=YEL)
        if reveal:
            y = 40 + (CH - 160) / 2 - 30
            d.rectangle((40 + (CW - 80) * 0.22, y, 40 + (CW - 80) * 0.78, y + 60), fill=(v, v, v))
    elif k == "ponzo":        # to like lange streker mellom skinner
        top, bot = 60, CH - 60
        d.line((CW / 2 - 60, top, 90, bot), fill=MUTED, width=10); d.line((CW / 2 + 60, top, CW - 90, bot), fill=MUTED, width=10)
        for i in range(9):
            yy = top + (bot - top) * (i / 8) ** 1.4; half = 60 + (CW / 2 - 150) * ((yy - top) / (bot - top))
            d.line((CW / 2 - half, yy, CW / 2 + half, yy), fill=(50, 64, 120), width=6)
        L = 190; ya, yb = 200, 540
        for yy, name in ((ya, "A"), (yb, "B")):
            d.line((CW / 2 - L / 2, yy, CW / 2 + L / 2, yy), fill=col, width=22)
            d.text((CW / 2 + L / 2 + 30, yy - 38), name, font=lab, fill=YEL)
        if reveal:
            for xe in (CW / 2 - L / 2, CW / 2 + L / 2):
                for yy in range(ya - 30, yb + 30, 30): d.line((xe, yy, xe, yy + 16), fill=GREEN, width=6)
    if reveal:
        f = F("Black", 54); t = p["answer"]
        d.rounded_rectangle((CW / 2 - d.textlength(t, font=f) / 2 - 30, CH / 2 - 50, CW / 2 + d.textlength(t, font=f) / 2 + 30, CH / 2 + 30), 30, fill=((10, 14, 18, 235) if T.name == "nixie" else (252, 248, 236, 240)))
        d.text((CW / 2 - d.textlength(t, font=f) / 2, CH / 2 - 42), t, font=f, fill=GREEN)
    return c

# ---------- serie F: hukommelse ----------
def card_F(p, phase):
    """phase: show | hide | reveal"""
    c, d = new_card(); g = p["grid"]; C = p["cols"]; R = math.ceil(len(g) / C)
    cell = min((CW - 80) / C, (CH - 80) / R); size = int(cell * 0.72)
    ox, oy = (CW - cell * C) / 2, (CH - cell * R) / 2
    qf = F("Black", int(cell * 0.55))
    for i, ch in enumerate(g):
        r, k = divmod(i, C); x, y = ox + k * cell, oy + r * cell
        d.rounded_rectangle((x + 8, y + 8, x + cell - 8, y + cell - 8), 22, fill=T.tile + (255,))
        if phase == "hide":
            d.text((x + cell / 2 - d.textlength("?", font=qf) / 2, y + cell / 2 - qf.size * 0.62), "?", font=qf, fill=T.tile_q)
            continue
        e = emoji(ch, size)
        if phase == "reveal" and ch != p["target"]:
            e = e.copy(); e.putalpha(e.getchannel("A").point(lambda v: v * 0.22))
        c.paste(e, (int(x + (cell - size) / 2), int(y + (cell - size) / 2)), e)
        if phase == "reveal" and ch == p["target"]:
            d.rounded_rectangle((x + 8, y + 8, x + cell - 8, y + cell - 8), 22, outline=YEL + (255,), width=8)
    return c

CARDS = {"A": card_A, "B": card_B, "C": card_C, "D": card_D, "E": card_E}

# ---------- tidslinje ----------
def timeline(p):
    if p["series"] == "F":
        return dict(mem=(0.0, 3.6), count=(4.0, 9.0), reveal=9.6, end=14.0)
    return dict(mem=None, count=(1.0, 6.0), reveal=6.6, end=12.0)

def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3

def ring(d, cx, cy, r, frac, num, col=YEL):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(34, 44, 90), width=22)
    if frac > 0: d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * frac, fill=col, width=22)
    f = F("Black", int(r * 1.05)); d.text((cx - d.textlength(num, font=f) / 2, cy - r * 0.68), num, font=f, fill=col)

class Reel:
    def __init__(self, p, theme=None):
        set_theme(theme or p.get("theme") or pts_theme.theme_for_id(p["id"]))
        self.p = p; self.tl = timeline(p); self.bg = T.background()
        s = p["series"]
        if s == "F":
            cards = dict(show=card_F(p, "show"), hide=card_F(p, "hide"), rev=card_F(p, "reveal"))
        else:
            cards = dict(q=CARDS[s](p, False), rev=CARDS[s](p, True))
        self.cards = {k: T.place(v) for k, v in cards.items()}
        # krok som eget lag (så animert bakgrunn kan ligge under)
        top = self.bg.copy(); T.hook(top, p["hook"])
        diff = np.abs(np.asarray(top, np.int16) - np.asarray(self.bg, np.int16)).sum(axis=2)
        self.hook_layer = top.convert("RGBA"); self.hook_layer.putalpha(Image.fromarray(np.clip(diff * 6, 0, 255).astype(np.uint8)))
        self.animated = T.name == "brass"
        self.static = None if self.animated else Image.alpha_composite(self.bg.convert("RGBA"), self.hook_layer).convert("RGB")

    def frame(self, t):
        p, tl = self.p, self.tl
        if self.animated:
            img = self.bg.copy(); T.animate(img, t); img.paste(self.hook_layer, (0, 0), self.hook_layer)
        else:
            img = self.static.copy()
        d = ImageDraw.Draw(img)
        # undertittel
        if tl["mem"] and t < tl["mem"][1]: sub = "Memorize the grid!"
        elif t >= tl["reveal"]: sub = p.get("explain_top", "Here's the answer")
        else: sub = p["prompt"]
        sfit, sls = fit_lines(d, sub, "SemiBold", 900, 60, start=44, minsize=30)
        rich_c(img, d, W / 2, 392, sls[0], sfit, T.sub)
        # kort (pop inn, bytt ved avsløring)
        if p["series"] == "F":
            key = "show" if t < tl["mem"][1] else ("hide" if t < tl["reveal"] else "rev")
            swap = tl["mem"][1] if tl["mem"][1] <= t < tl["mem"][1] + 0.25 else (tl["reveal"] if tl["reveal"] <= t < tl["reveal"] + 0.25 else None)
        else:
            key = "rev" if t >= tl["reveal"] else "q"
            swap = tl["reveal"] if tl["reveal"] <= t < tl["reveal"] + 0.25 else None
        card, (px, py) = self.cards[key]
        sc = 0.94 + 0.06 * ease(t / 0.35)
        if swap is not None: sc = 0.96 + 0.04 * ease((t - swap) / 0.25)
        if sc < 0.999:
            cw, ch = int(card.width * sc), int(card.height * sc); cc = card.resize((cw, ch), Image.BILINEAR)
            img.paste(cc, (int(px + (card.width - cw) / 2), int(py + (card.height - ch) / 2)), cc)
        else:
            img.paste(card, (px, py), card)
        if T.name == "desk": T.tape(img)
        # nedtelling / status
        c0, c1 = tl["count"]; total = c1 - c0
        if (tl["mem"] and t < c0) or t < c0: T.timer(img, total, total)
        elif t < c1: T.timer(img, c1 - t, total)
        elif t < tl["reveal"]: T.timesup(img, (t - c1) / (tl["reveal"] - c1))
        else: T.verdict(img, p.get("verdict", "Did you get it?"), (t - tl["reveal"]) / 0.4)
        # bunntekst
        d = ImageDraw.Draw(img)
        bt = "Comment your answer 👇" if t < tl["reveal"] else "Follow for a daily puzzle 🧠"
        if tl["mem"] and t < tl["mem"][1]: bt = "Then answer the question 👇"
        rich_c(img, d, W / 2, 1665, bt, T.font_text(48), T.bottom)
        return img

# ---------- lyd ----------
SR = 44100
def env(n, a, dcy):
    t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / dcy)
def add(buf, sig, at):
    i = int(at * SR)
    if i >= len(buf) or i < 0: return
    j = min(len(buf), i + len(sig)); buf[i:j] += sig[:j - i]
def lowpass(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y

def bed(dur, variant):
    """Lett, nysgjerrig «quiz»-groove. Original."""
    bpm = [118, 124, 112, 128][variant % 4]; beat = 60 / bpm; n = int(dur * SR); rng = np.random.default_rng(variant)
    out = np.zeros(n)
    kn = int(0.22 * SR); kt = np.arange(kn) / SR
    kick = np.sin(2 * np.pi * (52 * kt + 70 * (1 - np.exp(-kt * 40)) / 40)) * np.exp(-kt * 14) * 0.7
    hn = int(0.05 * SR); hat = np.diff(rng.standard_normal(hn + 1)) * env(hn, 0.0005, 0.015) * 0.22
    progs = [[(220.0, (0, 3, 7)), (174.61, (0, 4, 7)), (196.0, (0, 4, 7)), (164.81, (0, 4, 7))],
             [(261.63, (0, 4, 7)), (220.0, (0, 3, 7)), (174.61, (0, 4, 7)), (196.0, (0, 4, 7))],
             [(196.0, (0, 3, 7)), (155.56, (0, 4, 7)), (174.61, (0, 4, 7)), (146.83, (0, 4, 7))],
             [(293.66, (0, 3, 7)), (233.08, (0, 4, 7)), (261.63, (0, 4, 7)), (220.0, (0, 4, 7))]]
    arp = [[0, 7, 12, 7], [0, 4, 7, 12], [12, 7, 3, 7], [0, 12, 7, 4]][(variant // 4) % 4]
    prog = progs[variant % 4]; b = 0
    while b * beat < dur:
        t = b * beat; root, ivs = prog[(b // 4) % 4]
        add(out, kick, t); add(out, hat, t + beat / 2)
        for k in range(4):   # marimba-aktig arpeggio på 16-deler
            iv = ivs[k % 3] if k < 3 else 12
            iv = arp[k] if arp[k] in (0, 12) else iv
            f = root * 2 ** (iv / 12) * 2; mn = int(0.22 * SR); mt = np.arange(mn) / SR
            tone = (np.sin(2 * np.pi * f * mt) + 0.25 * np.sin(2 * np.pi * 4 * f * mt)) * env(mn, 0.001, 0.07) * 0.16
            add(out, tone, t + k * beat / 4)
        bn = int(beat * 0.9 * SR); bt = np.arange(bn) / SR
        add(out, np.sin(2 * np.pi * root / 2 * bt) * env(bn, 0.005, 0.25) * 0.35, t)
        b += 1
    return out

def tick(hi=False):
    n = int(0.09 * SR); t = np.arange(n) / SR; f = 2100 if hi else 1500
    return (np.sin(2 * np.pi * f * t) * 0.8 + np.sin(2 * np.pi * f * 1.5 * t) * 0.3) * np.exp(-t * 60)
def buzzer():
    n = int(0.45 * SR); t = np.arange(n) / SR
    return np.sign(np.sin(2 * np.pi * 140 * t)) * 0.35 * env(n, 0.005, 0.3) + np.sin(2 * np.pi * 70 * t) * 0.3 * env(n, 0.005, 0.3)
def ding():
    n = int(1.4 * SR); t = np.arange(n) / SR
    return sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * dcy) for f, a, dcy in ((1318.5, 0.6, 3), (1975.5, 0.35, 4), (2637, 0.2, 6), (1568, 0.3, 3.5)))
def whoosh(rng):
    n = int(0.35 * SR); x = lowpass(rng.standard_normal(n), 2500); return x * np.sin(np.linspace(0, np.pi, n)) * 0.25

def soundtrack(p, variant):
    tl = timeline(p); dur = tl["end"]; n = int(dur * SR); rng = np.random.default_rng(99)
    music = bed(dur, variant); fx = np.zeros(n)
    c0, c1 = tl["count"]
    # musikken dempes litt under nedtellingen så tikkene høres
    gain = np.ones(n); a, b = int(c0 * SR), int(c1 * SR); gain[a:b] = 0.55
    gain = np.convolve(gain, np.ones(2000) / 2000, mode="same")
    for s in range(int(round(c1 - c0))):
        add(fx, tick(hi=(c1 - c0 - s) <= 3) * 0.55, c0 + s)
    add(fx, buzzer() * 0.5, c1)
    add(fx, whoosh(rng), tl["reveal"] - 0.12); add(fx, ding() * 0.5, tl["reveal"])
    if tl["mem"]:
        add(fx, whoosh(rng) * 0.8, tl["mem"][1] - 0.1)
    mix = music * gain * 0.75 + fx
    fi, fo = int(0.02 * SR), int(0.6 * SR); mix[:fi] *= np.linspace(0, 1, fi); mix[-fo:] *= np.linspace(1, 0, fo)
    return mix / (np.max(np.abs(mix)) + 1e-9) * 0.89

def write_wav(path, x):
    y = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())

# ---------- render ----------
def render(p, out):
    r = Reel(p); dur = r.tl["end"]; nf = int(dur * FPS)
    tmp = tempfile.mkdtemp(); v, a = f"{tmp}/v.mp4", f"{tmp}/a.wav"
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", v], stdin=subprocess.PIPE)
    last, lastimg = None, None
    for i in range(nf):
        t = i / FPS; im = r.frame(t)
        proc.stdin.write(im.tobytes())
    proc.stdin.close(); assert proc.wait() == 0
    write_wav(a, soundtrack(p, int(p["id"]) % 16))
    part = out[:-4] + ".part.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "160k", "-shortest", part], check=True)
    os.replace(part, out)

def theme_of(p): return p.get("theme") or pts_theme.theme_for_id(p["id"])

def load(bank):
    return {json.loads(l)["id"]: json.loads(l) for l in open(bank, encoding="utf-8") if l.strip()}

if __name__ == "__main__":
    if sys.argv[1] == "--still":
        _, _, bank, pid, out, t = sys.argv
        Reel(load(bank)[pid]).frame(float(t)).save(out)
    else:
        bank, *ids, outdir = sys.argv[1:]; P = load(bank); os.makedirs(outdir, exist_ok=True)
        for pid in ids:
            render(P[pid], f"{outdir}/{HANDLE}_{pid}.mp4"); print("ok", pid, flush=True)
