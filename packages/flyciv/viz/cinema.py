"""Render the 12–15s Watch clip. Game skin, not a lab dashboard."""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import numpy as np

from flyciv.viz.cloud import spectator_cloud


def _dec_u8(b64: str) -> np.ndarray:
    import base64

    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8)


def _dec_f32(b64: str) -> np.ndarray:
    import base64

    return np.frombuffer(base64.b64decode(b64), dtype=np.float32)


def _shot(t01: float) -> str:
    if t01 < 0.11:
        return "gen 0"
    if t01 < 0.28:
        return "trails"
    if t01 < 0.48:
        return "a city"
    if t01 < 0.68:
        return "they built a trainer"
    if t01 < 0.88:
        return "it trains flies"
    return ""


def _fonts():
    from PIL import ImageFont

    def load(name: str, size: int):
        path = Path("/System/Library/Fonts/Supplemental") / name
        if path.is_file():
            return ImageFont.truetype(str(path), size)
        return ImageFont.load_default()

    return (
        load("Arial Bold.ttf", 72),
        load("Arial Bold.ttf", 36),
        load("Arial.ttf", 22),
        load("Arial Bold.ttf", 28),
    )


def _iso(x: float, y: float, nest_x: float, nest_y: float, ox: float, oy: float, s: float) -> tuple[float, float]:
    X, Y = x - nest_x, y - nest_y
    return ox + (X - Y) * s, oy + (X + Y) * s * 0.50


def _draw_colony(draw, frame: dict, ox: float, oy: float, s: float, fly_scale: float = 1.0) -> None:
    n = int(frame["res"])
    wear = _dec_u8(frame["wear_b64"]).reshape(n, n)
    mask = _dec_u8(frame["mask_b64"]).reshape(n, n)
    nest_y, nest_x = float(frame["nest"][0]), float(frame["nest"][1])

    def iso(x, y):
        return _iso(x, y, nest_x, nest_y, ox, oy, s)

    # Wear dust then gold roads — circles, not a tiled island.
    ys, xs = np.where((wear >= 8) | (mask > 0))
    for y, x in zip(ys.tolist(), xs.tolist()):
        wv = int(wear[y, x])
        m = int(mask[y, x])
        px, py = iso(x, y)
        if m & 1:
            r = 7 + min(18, wv / 12) * fly_scale
            col = (255, 211, 80, 230)
        elif m & 2:
            r = 5 + min(12, wv / 18) * fly_scale
            col = (210, 150, 40, 160)
        elif wv:
            r = 3 + (wv / 40) * fly_scale
            col = (180, 110, 30, 70)
        else:
            continue
        draw.ellipse((px - r, py - r * 0.55, px + r, py + r * 0.55), fill=col)
        if m & 4:
            rf = 8 * fly_scale
            draw.ellipse((px - rf, py - rf, px + rf, py + rf), fill=(40, 255, 90, 255))

    nx, ny = iso(nest_x, nest_y)
    trainer = bool(frame.get("trainer"))
    glow = 70 if trainer else 38
    draw.ellipse((nx - glow, ny - glow, nx + glow, ny + glow), fill=(40, 110, 255, 70 if trainer else 40))
    draw.ellipse((nx - 22, ny - 22, nx + 22, ny + 22), fill=(80, 170, 255, 255) if trainer else (40, 90, 220, 255))
    draw.ellipse((nx - 10, ny - 10, nx + 10, ny + 10), fill=(200, 230, 255, 255))

    agents = sorted(frame.get("agents") or [], key=lambda a: 0 if a.get("k") == "c" else 1)
    for a in agents:
        px, py = iso(float(a["x"]), float(a["y"]))
        k = a.get("k", "c")
        if k == "c":
            r = 7 * fly_scale
            draw.ellipse((px - r, py - r, px + r, py + r), fill=(120, 140, 170, 220))
        else:
            r = (18 if k == "C" else 16) * fly_scale
            draw.ellipse((px - r - 6, py - r - 6, px + r + 6, py + r + 6), outline=(255, 220, 80, 255), width=4)
            draw.ellipse((px - r, py - r, px + r, py + r), fill=(255, 110, 20, 255))


def _draw_brain(draw, box, soma: np.ndarray, glow: np.ndarray, yaw: float, pitch: float, flash: float) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(4, 6, 10, 255))
    if soma.size < 3:
        return
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    bw, bh = x1 - x0, y1 - y0
    sc = min(bw, bh) * 0.48
    cx, cyi = (x0 + x1) / 2, (y0 + y1) / 2
    n_s = len(soma) // 3
    for k in range(0, n_s, 1):
        x, y, z = float(soma[k * 3]), float(soma[k * 3 + 1]), float(soma[k * 3 + 2])
        x1p, z1 = x * cy - z * sy, x * sy + z * cy
        y1p = y * cp - z1 * sp
        px, py = cx + x1p * sc, cyi + y1p * sc
        g = float(glow[k]) if k < len(glow) else 0.0
        g2 = min(1.0, g + (0.35 if flash > 0.2 else 0.0))
        if g2 > 0.08:
            r = 2.2 + g2 * 2.8
            draw.ellipse((px - r, py - r, px + r, py + r), fill=(80, 255, 220, int(180 + 75 * g2)))
        else:
            draw.rectangle((px, py, px + 1.6, py + 1.6), fill=(150, 160, 180, 140))
    if flash > 0.15:
        # tint spikes, never a solid slab over the cloud
        pass


def _draw_scope(draw, box, frame: dict, font) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(8, 12, 22, 255))
    names = frame.get("names") or []
    rates = frame.get("rates") or []

    def rate(nm: str) -> float:
        try:
            return float(rates[names.index(nm)])
        except (ValueError, IndexError):
            return 0.0

    rows = [
        ("sugar", rate("sugar_sensor")),
        ("walk", rate("dn_walk")),
        ("follow", rate("dn_follow")),
        ("reward", rate("ppl1_reward")),
        ("trainer", 1.0 if frame.get("trainer") else 0.0),
        ("child", 1.0 if frame.get("n_child") else 0.0),
    ]
    mx = max(0.25, max(r[1] for r in rows))
    pad = 28
    row_h = (y1 - y0 - 80) / 6
    for i, (lab, v) in enumerate(rows):
        y = y0 + 50 + i * row_h
        draw.text((x0 + pad, y), lab, fill=(210, 220, 235, 255), font=font)
        bar_x0 = x0 + pad
        bar_x1 = x1 - pad
        draw.rectangle((bar_x0, y + 26, bar_x1, y + 44), fill=(20, 28, 44, 255))
        bw = int((bar_x1 - bar_x0) * min(1.0, v / mx))
        col = (255, 122, 24, 255) if lab == "trainer" else (80, 255, 210, 255)
        if lab == "child" and v > 0:
            col = (255, 211, 80, 255)
        draw.rectangle((bar_x0, y + 26, bar_x0 + max(6, bw), y + 44), fill=col)


def render_wide(frame: dict, soma: np.ndarray, glow: np.ndarray, yaw: float, t01: float, size=(1920, 1080)):
    from PIL import Image, ImageDraw

    w, h = size
    pil = Image.new("RGBA", (w, h), (6, 9, 16, 255))
    draw = ImageDraw.Draw(pil, "RGBA")
    font_big, font_mid, font_sm, font_word = _fonts()
    world_w = int(w * 0.56)
    brain_w = int(w * 0.28)
    _draw_colony(draw, frame, ox=world_w * 0.50, oy=h * 0.46, s=22.0, fly_scale=1.35)
    _draw_brain(draw, (world_w, 0, world_w + brain_w, h), soma, glow, yaw, 0.38, 1.0 if (frame.get("trainer") and 0.47 < t01 < 0.72) else 0.0)
    _draw_scope(draw, (world_w + brain_w, 0, w, h), frame, font_sm)
    draw.text((28, 22), "FLYCIV", fill=(240, 246, 255, 255), font=font_word)
    tr = "trainer ON" if frame.get("trainer") else "trainer OFF"
    tr_col = (80, 255, 210, 255) if frame.get("trainer") else (140, 150, 170, 255)
    draw.text((w - 420, 22), f"gen {frame.get('generation', 0)}  ·  {tr}", fill=tr_col, font=font_mid)
    title = _shot(t01)
    if title:
        draw.text((40, h - 160), title, fill=(255, 255, 255, 255), font=font_big)
    ev = frame.get("events") or []
    names_e = {
        "first_trail": "first trail",
        "first_store": "first store",
        "first_road": "roads",
        "trainer_unlocked": "trainer on",
        "trainer_child": "child born",
    }
    ticker = "  →  ".join(names_e.get(e.get("name", ""), e.get("name", "")) for e in ev)
    if t01 > 0.88:
        ticker = "tiny MaleCNS · frozen brain · evolving habits"
    draw.text((40, h - 56), ticker, fill=(200, 210, 230, 255), font=font_sm)
    return pil.convert("RGB")


def render_tall(frame: dict, soma: np.ndarray, glow: np.ndarray, yaw: float, t01: float, size=(1080, 1920)):
    from PIL import Image, ImageDraw

    w, h = size
    pil = Image.new("RGBA", (w, h), (6, 9, 16, 255))
    draw = ImageDraw.Draw(pil, "RGBA")
    font_big, font_mid, font_sm, font_word = _fonts()
    map_h = int(h * 0.62)
    _draw_colony(draw, frame, ox=w * 0.50, oy=map_h * 0.52, s=28.0, fly_scale=1.6)
    _draw_brain(draw, (0, map_h, w, h - 140), soma, glow, yaw, 0.38, 1.0 if (frame.get("trainer") and 0.47 < t01 < 0.72) else 0.0)
    draw.text((36, 28), "FLYCIV", fill=(240, 246, 255, 255), font=font_word)
    tr = "trainer ON" if frame.get("trainer") else "trainer OFF"
    tr_col = (80, 255, 210, 255) if frame.get("trainer") else (140, 150, 170, 255)
    draw.text((36, 80), f"gen {frame.get('generation', 0)}  ·  {tr}", fill=tr_col, font=font_mid)
    title = _shot(t01)
    if title:
        draw.text((40, map_h - 120), title, fill=(255, 255, 255, 255), font=font_big)
    ev = frame.get("events") or []
    names_e = {
        "first_trail": "first trail",
        "first_store": "first store",
        "first_road": "roads",
        "trainer_unlocked": "trainer on",
        "trainer_child": "child born",
    }
    ticker = "  →  ".join(names_e.get(e.get("name", ""), e.get("name", "")) for e in ev)
    if t01 > 0.88:
        ticker = "tiny MaleCNS · frozen brain · evolving habits"
    draw.text((36, h - 70), ticker, fill=(200, 210, 230, 255), font=font_sm)
    return pil.convert("RGB")


def _sim_index(t01: float, n: int) -> int:
    if t01 < 0.12:
        return int((t01 / 0.12) * min(6, n - 1))
    rest = (t01 - 0.12) / 0.88
    return min(n - 1, 6 + int(rest * (n - 1 - 6)))


def render_clip(watch_json: Path, out_dir: Path, seconds: float = 13.5, fps: int = 24) -> tuple[Path, Path]:
    payload = json.loads(Path(watch_json).read_text(encoding="utf-8"))
    frames = payload["frames"]
    cloud = payload.get("meta", {}).get("cloud") or spectator_cloud()
    soma = _dec_f32(cloud["xyz_b64"])
    n_s = int(cloud["n"])
    glow = np.zeros(n_s, dtype=np.float32)
    n_out = int(seconds * fps)
    out_dir = Path(out_dir)
    seq_w = out_dir / "png16"
    seq_t = out_dir / "png9"
    seq_w.mkdir(parents=True, exist_ok=True)
    seq_t.mkdir(parents=True, exist_ok=True)
    halo = cloud.get("halo") or []
    toy_idx = cloud.get("toy_idx") or []
    yaw = 0.95
    for k in range(n_out):
        t01 = k / max(1, n_out - 1)
        fi = _sim_index(t01, len(frames))
        f = frames[fi]
        spikes = f.get("spikes") or []
        glow *= 0.80
        for t, sp in enumerate(spikes):
            if not sp:
                continue
            if t < len(halo):
                for h in halo[t]:
                    if h < n_s:
                        glow[h] = max(glow[h], 0.75)
            if t < len(toy_idx) and int(toy_idx[t]) < n_s:
                glow[int(toy_idx[t])] = 1.0
        yaw += 0.010
        render_wide(f, soma, glow, yaw, t01).save(seq_w / f"f{k:04d}.png")
        render_tall(f, soma, glow, yaw, t01).save(seq_t / f"f{k:04d}.png")
    wide = out_dir / "flyciv-watch-16x9.mp4"
    tall = out_dir / "flyciv-watch-9x16.mp4"
    for seq, dest in ((seq_w, wide), (seq_t, tall)):
        subprocess.check_call(
            [
                "ffmpeg",
                "-y",
                "-framerate",
                str(fps),
                "-i",
                str(seq / "f%04d.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "17",
                str(dest),
            ]
        )
    return wide, tall
