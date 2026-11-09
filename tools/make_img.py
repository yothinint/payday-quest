# -*- coding: utf-8 -*-
"""Turn the big ChatGPT PNGs in assets/ into small WebP files in img/ for the game.
Run:  python3 tools/make_img.py   (from the Payday Quest folder)
assets/ is never modified."""
import os, glob, json
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "img")
os.makedirs(OUT, exist_ok=True)

def src(folder, name=None, idx=None):
    """Find a source PNG by exact name, or by position among the ChatGPT-named files (same order as the prompt Doc)."""
    d = os.path.join(A, folder)
    if name and os.path.exists(os.path.join(d, name)):
        return os.path.join(d, name)
    gen = sorted(f for f in os.listdir(d) if f.startswith("ChatGPT Image") and f.endswith(".png"))
    return os.path.join(d, gen[idx])

def crop(im, thr=40):
    im = im.convert("RGBA")
    bb = im.getchannel("A").point(lambda v: 255 if v > thr else 0).getbbox()
    return im.crop(bb) if bb else im

def save(im, name, q=82):
    p = os.path.join(OUT, name + ".webp")
    im.save(p, "WEBP", quality=q, method=6)
    return os.path.getsize(p)

def fit(im, w=None, h=None):
    if h and not w: w = round(im.width * h / im.height)
    if w and not h: h = round(im.height * w / im.width)
    return im.resize((max(1, w), max(1, h)), Image.LANCZOS)

made = {}
def put(name, im, q=82):
    made[name] = [im.width, im.height, save(im, name, q)]

# ---- ground textures: shrink, then mirror 2x2 so the pattern is always seamless ----
for i, n in enumerate(["grass", "tall", "path", "road", "plaza", "water"]):
    im = Image.open(src("tiles", idx=i)).convert("RGB")
    im = im.resize((256, 256), Image.LANCZOS)
    big = Image.new("RGB", (512, 512))
    big.paste(im, (0, 0)); big.paste(im.transpose(Image.FLIP_LEFT_RIGHT), (256, 0))
    big.paste(im.transpose(Image.FLIP_TOP_BOTTOM), (0, 256)); big.paste(im.transpose(Image.ROTATE_180), (256, 256))
    put("t-" + n, big, 78)

# ---- buildings (height = tiles x 32 x 2 for sharp phones) ----
BLD_GEN = ["home", "store", "cafe", "office", "jobs", "post", "bank", "mall", "garage", "police", "temple", "station", "hall"]
BIG = {"office", "mall", "station", "hall", "bank"}
named = ["barber", "clinic", "flower", "food", "gym", "library", "market", "phone", "super", "vet"]
for i, b in enumerate(BLD_GEN):
    im = crop(Image.open(src("buildings", idx=i)))
    put("b-" + b, fit(im, h=(6 if b in BIG else 5) * 64))
for b in named:
    im = crop(Image.open(os.path.join(A, "buildings", b + ".png")))
    put("b-" + b, fit(im, h=(6 if b in BIG else 5) * 64))

# ---- props ----
PROPS = {"fence": "fence.png", "fountain": "fountain.png", "lake": "lake-big.png", "pond": "pond-small.png", "board": "quest-board.png"}
for k, f in PROPS.items():
    put("p-" + k, fit(crop(Image.open(os.path.join(A, "props", f))), w=384))
THAI = {"tree-pine": "ต้นป็อปลาร์", "tree-round": "ต้นไม้ระนาบ", "bush": "พุ่มไม้", "bench": "ม้านั่ง", "flowers": "แปลงดอกทิวลิป", "lamp": "โคมไฟถนน"}
for k, pre in THAI.items():
    f = [x for x in os.listdir(os.path.join(A, "props")) if x.startswith(pre)][0]
    im = crop(Image.open(os.path.join(A, "props", f)))
    put("p-" + k, fit(im, h=256) if k in ("tree-pine", "tree-round", "lamp") else fit(im, w=192))

# ---- characters ----
sheet = Image.open(src("characters", idx=0)).convert("RGBA")
a = sheet.getchannel("A").point(lambda v: 255 if v > 128 else 0)
sheet.putalpha(Image.composite(sheet.getchannel("A"), Image.new("L", sheet.size, 0), a))
CW, CH = sheet.width // 3, sheet.height // 4
cells = []
for r in range(4):
    band = sheet.crop((0, r * CH, sheet.width, (r + 1) * CH))
    proj = band.getchannel("A").resize((band.width, 1), Image.BOX)
    on = [proj.getpixel((x, 0)) > 1 for x in range(band.width)] + [False]
    runs, st = [], None
    for x, v in enumerate(on):
        if v and st is None: st = x
        if not v and st is not None:
            if x - st > 30: runs.append((st, x))
            st = None
    assert len(runs) == 3, (r, runs)
    for a0, a1 in runs:
        cell = band.crop((a0, 0, a1, band.height)); cells.append(cell.crop(cell.getchannel("A").getbbox()))
mh = max(x.height for x in cells)
sc = 120 / mh
FW, FH = 96, 128
out = Image.new("RGBA", (FW * 3, FH * 4), (0, 0, 0, 0))
for i, cell in enumerate(cells):
    cell = cell.resize((round(cell.width * sc), round(cell.height * sc)), Image.LANCZOS)
    r, c = divmod(i, 3)
    out.paste(cell, (c * FW + (FW - cell.width) // 2, r * FH + FH - 4 - cell.height), cell)
put("c-player", out, 90)
for i, n in enumerate(["friend", "aunt", "sales", "coach", "elder"]):
    put("n-" + n, fit(crop(Image.open(src("characters", idx=i + 1))), h=200))

# ---- monsters / bosses ----
for i, m in enumerate(["turtle", "owl", "wolf", "dragon", "lion", "snail", "bolt", "unicorn"]):
    put("m-" + m, fit(crop(Image.open(src("monsters", idx=i))), w=220))
for b in ["rate", "bubble", "war", "virus", "flood"]:
    put("x-" + b, fit(crop(Image.open(os.path.join(A, "bosses", b + ".png"))), w=280))

# ---- UI icons ----
UI = ["leftover", "savings", "invest", "card", "happy", "phone", "m-forced", "m-quest", "m-invite", "m-board", "fridge"]
for i, n in enumerate(UI):
    put("u-" + n, fit(crop(Image.open(src("ui", idx=i))), w=112))
put("u-wallet", fit(crop(Image.open(os.path.join(A, "ui", "acc-wallet.png"))), w=112))

# ---- minigames: split rows/grids into single items by empty columns ----
def split_cols(im):
    im = crop(im); a = im.getchannel("A").point(lambda v: 255 if v > 150 else 0)
    proj = a.resize((im.width, 1), Image.BOX)
    cols = [proj.getpixel((x, 0)) > 2 for x in range(im.width)]
    parts, s = [], None
    for x, on in enumerate(cols + [False]):
        if on and s is None: s = x
        if not on and s is not None:
            if x - s > 20: parts.append(crop(im.crop((s, 0, x, im.height))))
            s = None
    return parts
def split_even(im, n):
    im = crop(im); w = im.width / n
    return [crop(im.crop((round(i * w), 0, round((i + 1) * w), im.height)), 120) for i in range(n)]
for kind, f, n in [("good", "fruits-good.png", 7), ("bad", "fruits-bad.png", 4)]:
    for i, p in enumerate(split_even(Image.open(os.path.join(A, "minigames", f)), n)):
        put("g-%s%d" % (kind, i), fit(p, w=128) if p.width >= p.height else fit(p, h=128))
books = crop(Image.open(os.path.join(A, "minigames", "books.png")))
bw, bh = books.width / 4, books.height / 3
for i in range(12):
    r, c = divmod(i, 4)
    put("g-book%d" % i, fit(crop(books.crop((round(c * bw), round(r * bh), round((c + 1) * bw), round((r + 1) * bh)))), h=120))
put("g-cashier", fit(crop(Image.open(os.path.join(A, "minigames", "cashier.png"))), w=420))

# ---- title ----
ka = Image.open(os.path.join(A, "tiles", "key-art.png")).convert("RGB")
put("title-art", fit(ka, h=1100), 76)
put("title-logo", fit(crop(Image.open(os.path.join(A, "tiles", "logo-shape.png"))), w=640))

json.dump(made, open(os.path.join(OUT, "manifest.json"), "w"), indent=0)
tot = sum(v[2] for v in made.values())
print(len(made), "files,", round(tot / 1024), "KB total")
for k, v in sorted(made.items()): print(k, v[0], "x", v[1], round(v[2] / 1024), "KB")
