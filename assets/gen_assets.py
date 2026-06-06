"""Visuels line-twin : cover repo + carte Malt + vidéo TikTok 9:16 de la ligne animée.

La ligne animée est la VRAIE simulation : on step le ProductionLine et on rend l'état
(buffers, états des postes, goulot, débit) image par image.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "src"))
from linetwin import ProductionLine, snapshot          # noqa: E402
from linetwin.line import State                         # noqa: E402
from linetwin.metrics import bottleneck_index           # noqa: E402

PORT = Path(r"C:\au2\Au2qwen\portfolio_malt")
IMG = PORT / "images"
VID = PORT / "videos"
for p in (HERE, IMG, VID):
    p.mkdir(parents=True, exist_ok=True)

BG = (13, 17, 23); PANEL = (22, 27, 34); PANEL2 = (33, 38, 45); BORDER = (48, 54, 61)
WHITE = (230, 237, 243); GRAY = (139, 148, 158); GREEN = (63, 185, 80)
RED = (248, 81, 73); BLUE = (88, 166, 255); AMBER = (245, 191, 79); CYAN = (57, 197, 207)
VIOLET = (188, 140, 255)

F = "C:/Windows/Fonts/"
def font(n, s): return ImageFont.truetype(F + n, s)
bold = lambda s: font("arialbd.ttf", s)
reg = lambda s: font("arial.ttf", s)
mono = lambda s: font("consola.ttf", s)
monob = lambda s: font("consolab.ttf", s)


def pill(d, x, y, text, fnt, fg, bg=PANEL, pad=16):
    w = d.textlength(text, font=fnt); h = fnt.size
    d.rounded_rectangle([x, y, x + w + pad * 2, y + h + pad], radius=(h + pad) // 2,
                        fill=bg, outline=BORDER, width=1)
    d.text((x + pad, y + pad // 2), text, font=fnt, fill=fg)
    return x + w + pad * 2 + 12


def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- IMAGES 1200x630
CW, CH = 1200, 630


def cover_and_card():
    for out, title, sub, accent, repo_copy in [
        ("15_line_twin.png", "line-twin",
         ["Jumeau numérique d'une ligne d'assemblage :", "flux, buffers, goulot détecté, débit en direct."],
         VIOLET, True)]:
        img = Image.new("RGB", (CW, CH), BG); d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 8, CH], fill=accent)
        # mini-ligne décorative
        xs = [250, 430, 610, 790, 970]; y = 250
        for i, x in enumerate(xs):
            c = RED if i == 2 else PANEL2
            d.rounded_rectangle([x - 34, y - 34, x + 34, y + 34], radius=10, fill=c, outline=BORDER, width=1)
            if i < len(xs) - 1:
                d.line([(x + 34, y), (xs[i + 1] - 34, y)], fill=BORDER, width=3)
        d.text((250 - 34, y + 50), "S0   S1   S2   S3   S4", font=mono(22), fill=GRAY)
        d.text((610 - 50, y - 86), "GOULOT", font=monob(22), fill=RED)
        d.text((64, 56), "$ python -m linetwin run", font=mono(24), fill=accent)
        d.text((62, 96), title, font=bold(76), fill=WHITE)
        yy = 340
        for line in sub:
            d.text((64, yy), line, font=reg(29), fill=GRAY); yy += 39
        d.text((64, 430), "16.5", font=bold(70), fill=accent)
        d.text((64 + d.textlength("16.5", font=bold(70)) + 16, 458), "parts/min (96% du plafond)",
               font=reg(26), fill=GRAY)
        px = 64
        for label in ("Python", "digital-twin", "bottleneck", "throughput", "pytest"):
            px = pill(d, px, 540, label, mono(20), BLUE)
        img.save(IMG / out)
        if repo_copy:
            # cover repo (réutilise le même visuel)
            img.save(HERE / "cover.png")
        print("wrote", out, "+ repo cover.png")


# ---------------------------------------------------------------- VIDÉO 9:16
VW, VH = 1080, 1920
FPS = 30
N_FRAMES = 360
SUBSTEPS = 3
DT = 0.1


def station_box(d, cx, cy, half, state, remaining, cycle, is_bottleneck, name, frame):
    col = {State.BUSY: GREEN, State.BLOCKED: AMBER, State.STARVED: GRAY}[state]
    fill = lerp(BG, col, 0.16)
    border = col
    bw = 3
    if is_bottleneck:
        pulse = 0.5 + 0.5 * np.sin(frame * 0.4)
        border = lerp(RED, (255, 180, 180), pulse)
        bw = 6
        fill = lerp(BG, RED, 0.20)
    d.rounded_rectangle([cx - half, cy - half, cx + half, cy + half], radius=14,
                        fill=fill, outline=border, width=bw)
    d.text((cx - d.textlength(name, font=bold(34)) / 2, cy - half + 12), name,
           font=bold(34), fill=WHITE)
    # barre de progression de la pièce en cours
    if state is State.BUSY and cycle > 0:
        prog = max(0.0, min(1.0, 1 - remaining / cycle))
        bx0, bx1 = cx - half + 16, cx + half - 16
        by = cy + half - 30
        d.rounded_rectangle([bx0, by, bx1, by + 16], radius=8, fill=PANEL2)
        d.rounded_rectangle([bx0, by, bx0 + int((bx1 - bx0) * prog), by + 16], radius=8, fill=col)
    d.text((cx - d.textlength(f"{cycle:.1f}s", font=mono(24)) / 2, cy + 4),
           f"{cycle:.1f}s", font=mono(24), fill=GRAY)
    # étiquette d'état
    lab = {State.BUSY: "actif", State.BLOCKED: "bloqué", State.STARVED: "à vide"}[state]
    lc = {State.BUSY: GREEN, State.BLOCKED: AMBER, State.STARVED: GRAY}[state]
    d.text((cx - d.textlength(lab, font=mono(22)) / 2, cy - 28), lab, font=mono(22), fill=lc)


def buffer_stack(d, x, cy, cap, count, frame):
    """Pile verticale de slots (input buffer)."""
    r = 9; gap = 24
    top = cy - (cap - 1) * gap / 2
    for k in range(cap):
        yy = top + k * gap
        filled = (cap - 1 - k) < count        # remplit par le bas
        c = CYAN if filled else PANEL2
        d.ellipse([x - r, yy - r, x + r, yy + r], fill=c,
                  outline=BORDER if not filled else None, width=1)


def line_video():
    cycles = [2.0, 2.0, 3.5, 2.0, 2.0]
    line = ProductionLine(cycle_times=cycles, buffer_capacity=6, cv=0.15, seed=7)
    n = len(cycles)
    # warm-up : laisse la contre-pression se propager jusqu'à S0 (régime établi)
    line.run(duration_s=25, dt=DT)

    import imageio.v2 as imageio
    w = imageio.get_writer(VID / "linetwin_flow_tiktok.mp4", fps=FPS, codec="libx264",
                           quality=8, macro_block_size=1, ffmpeg_log_level="error")

    # positions horizontales des postes
    xs = [125 + i * 200 for i in range(n)]      # 125,325,525,725,925
    cyl = 560                                    # y centre de la ligne
    half = 78

    for f in range(N_FRAMES):
        for _ in range(SUBSTEPS):
            line.step(DT)
        snap = snapshot(line)
        bi = bottleneck_index(line)
        img = Image.new("RGB", (VW, VH), BG); d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 10, VH], fill=VIOLET)

        # header
        d.text((44, 56), "$ python -m linetwin run", font=mono(28), fill=VIOLET)
        d.text((42, 100), "JUMEAU NUMÉRIQUE", font=bold(56), fill=WHITE)
        d.text((46, 168), "ligne d'assemblage · 5 postes en série", font=reg(30), fill=GRAY)

        # source (∞) à gauche
        d.text((36, cyl - 22), "∞", font=bold(56), fill=GRAY)
        d.text((28, cyl + 36), "source", font=mono(22), fill=GRAY)

        # convoyeur + marching ants
        off = (f * 6) % 24
        for x in range(70, 980, 24):
            d.line([(x - off, cyl + half + 28), (x - off + 12, cyl + half + 28)],
                   fill=BORDER, width=4)

        # buffers (input de chaque poste) entre source/postes
        # buffer[0] = source feed (devant S0) ; buffer[i] entre S(i-1) et S(i)
        for i in range(n):
            bx = xs[i] - 100 if i > 0 else xs[0] - 95
            if i == 0:
                continue  # source infinie déjà dessinée
            buffer_stack(d, bx, cyl, line.buffer_capacity, len(line.buffers[i]), f)

        # liens entre postes
        for i in range(n - 1):
            d.line([(xs[i] + half, cyl), (xs[i + 1] - half, cyl)], fill=BORDER, width=3)

        # postes
        for i in range(n):
            s = line.stations[i]
            station_box(d, xs[i], cyl, half, s.state, s.remaining, s.cycle_s,
                        i == bi, s.name, f)

        # sink
        d.text((965, cyl - 30), "→", font=bold(56), fill=GREEN)
        d.text((965, cyl + 36), "sortie", font=mono(22), fill=GREEN)

        # bandeau goulot
        d.rounded_rectangle([44, 720, VW - 44, 800], radius=14, fill=lerp(BG, RED, 0.16))
        pulse = (f // 5) % 2 == 0
        d.text((68, 738), "GOULOT D'ÉTRANGLEMENT détecté :", font=bold(32),
               fill=RED if pulse else AMBER)
        d.text((68 + d.textlength("GOULOT D'ÉTRANGLEMENT détecté : ", font=bold(32)), 738),
               f"{snap.bottleneck}", font=bold(32), fill=WHITE)

        # compteurs
        cy0 = 880
        def counter(x, label, value, unit, col):
            d.text((x, cy0), label, font=mono(28), fill=GRAY)
            d.text((x, cy0 + 34), value, font=bold(82), fill=col)
            vw = d.textlength(value, font=bold(82))
            d.text((x + vw + 12, cy0 + 86), unit, font=reg(28), fill=GRAY)
        counter(48, "DÉBIT", f"{snap.throughput_per_min:.1f}", "p/min", VIOLET)
        counter(420, "WIP", f"{snap.wip}", "pièces", CYAN)
        counter(740, "EFFICACITÉ", f"{snap.efficiency*100:.0f}", "%",
                GREEN if snap.efficiency > 0.85 else AMBER)
        d.text((48, cy0 + 130), f"plafond théorique {snap.max_throughput_per_min:.1f} p/min "
               f"(imposé par {snap.bottleneck} @ {cycles[bi]:.1f}s)", font=mono(24), fill=GRAY)

        # barres d'utilisation par poste
        by0 = 1130
        d.text((48, by0 - 56), "Utilisation par poste", font=bold(34), fill=WHITE)
        for i, s in enumerate(snap.stations):
            yy = by0 + i * 86
            d.text((48, yy), s["name"], font=monob(30), fill=WHITE)
            d.text((120, yy + 2), f"{cycles[i]:.1f}s", font=mono(26), fill=GRAY)
            bx = 230; bw = VW - 100 - bx
            d.rounded_rectangle([bx, yy, bx + bw, yy + 40], radius=12, fill=PANEL2)
            col = RED if s["is_bottleneck"] else (GRAY if s["starved"] > 0.3 else CYAN)
            d.rounded_rectangle([bx, yy, bx + int(bw * s["utilization"]), yy + 40],
                                radius=12, fill=col)
            # part bloquée (ambre) / affamée (gris) en surcouche fine
            d.text((bx + bw - 86, yy + 4), f"{s['utilization']*100:.0f}%",
                   font=monob(28), fill=WHITE)
            tag = ""
            if s["blocked"] > 0.25: tag = "amont saturé"
            elif s["starved"] > 0.25: tag = "aval à vide"
            if tag:
                d.text((bx + 14, yy + 6), tag, font=mono(24), fill=lerp(WHITE, BG, 0.2))

        # footer
        d.text((48, VH - 104), "line-twin", font=bold(36), fill=WHITE)
        d.text((48, VH - 58), "github.com/Makeph", font=mono(28), fill=GRAY)
        made = f"{snap.produced} pièces produites"
        d.text((VW - 48 - d.textlength(made, font=mono(28)), VH - 58), made,
               font=mono(28), fill=GRAY)

        w.append_data(np.asarray(img))
    w.close()
    print("wrote linetwin_flow_tiktok.mp4")


if __name__ == "__main__":
    cover_and_card()
    line_video()
    print("DONE")
