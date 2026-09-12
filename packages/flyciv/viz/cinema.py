"""Render the 12–15s Watch clip from a showcase run. Not the lab HUD."""

from __future__ import annotations

import json
import math
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


def _iso(x: float, y: float, ox: float, oy: float, s: float) -> tuple[float, float]:
    return ox + (x - y) * s, oy + (x + y) * s * 0.52


def render_frame(img: np.ndarray, frame: dict, soma: np.ndarray, yaw: float, pitch: float, t01: float, glow: np.ndarray) -> None:
    from PIL import Image, ImageDraw, ImageFont

    h, w = img.shape[:2]
    world_w = int(w * 0.50)
    brain_w = int(w * 0.33)
    # navy fill
    img[:] = (7, 11, 20)
    pil = Image.fromarray(img, "RGB")
    draw = ImageDraw.Draw(pil)
    try:
        font_big = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 54)
        font_mid = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 28)
        font_sm = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
        font_word = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)
    except OSError:
        font_big = font_mid = font_sm = font_word = ImageFont.load_default()

    n = int(frame["res"])
    wear = _dec_u8(frame["wear_b64"]).reshape(n, n)
    mask = _dec_u8(frame["mask_b64"]).reshape(n, n)
    nest = frame["nest"]
    agents = frame["agents"]
    # content box
    ys, xs = np.where((mask > 0) | (wear > 6))
    pts_x = list(xs) + [int(nest[1])] + [int(a["x"]) for a in agents]
    pts_y = list(ys) + [int(nest[0])] + [int(a["y"]) for a in agents]
    x0, x1 = max(0, min(pts_x) - 3), min(n - 1, max(pts_x) + 3)
    y0, y1 = max(0, min(pts_y) - 3), min(n - 1, max(pts_y) + 3)
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    s = min(world_w / (bw + bh + 2), (h - 80) / ((bw + bh) * 0.52 + 2)) * 0.9
    ox, oy = world_w * 0.52, h * 0.16

    def iso(x, y):
        return _iso(x - x0, y - y0, ox, oy, s)

    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            m = int(mask[y, x])
            wv = int(wear[y, x])
            px, py = iso(x, y)
            if m & 1:
                col = (255, 211, 106)
            elif m & 2:
                col = (196, 146, 42)
            elif wv:
                t = wv / 255.0
                col = (int(20 + t * 180), int(16 + t * 90), int(8 + t * 20))
            else:
                col = (12, 18, 32)
            poly = [
                (px, py),
                (px + s, py + s * 0.52),
                (px, py + s * 1.04),
                (px - s, py + s * 0.52),
            ]
            draw.polygon(poly, fill=col)
            if m & 4:
                draw.ellipse((px - 4, py + s * 0.4 - 4, px + 4, py + s * 0.4 + 4), fill=(61, 255, 106))
    nx, ny = iso(nest[1], nest[0])
    glow_r = 28 if frame.get("trainer") else 16
    draw.ellipse((nx - glow_r, ny - glow_r + 6, nx + glow_r, ny + glow_r + 6), fill=(30, 70, 160))
    draw.rectangle((nx - 10, ny, nx + 10, ny + 14), fill=(61, 139, 255) if frame.get("trainer") else (40, 90, 200))
    for a in agents:
        px, py = iso(a["x"], a["y"])
        k = a.get("k", "c")
        if k == "c":
            draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=(109, 123, 147))
        else:
            r = 12 if k == "C" else 10
            draw.ellipse((px - r - 3, py - r - 3, px + r + 3, py + r + 3), outline=(255, 211, 106), width=3)
            draw.ellipse((px - r, py - r, px + r, py + r), fill=(255, 122, 24))

    # brain
    bx0 = world_w
    bw_b = brain_w
    draw.rectangle((bx0, 0, bx0 + bw_b, h), fill=(5, 7, 13))
    if len(soma) >= 3:
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        sc = min(bw_b, h) * 0.46
        cx, cyi = bx0 + bw_b / 2, h / 2
        n_s = len(soma) // 3
        spikes = frame.get("spikes") or []
        halo = None
        # cheap: draw every 2nd soma
        for k in range(0, n_s, 2):
            x, y, z = float(soma[k * 3]), float(soma[k * 3 + 1]), float(soma[k * 3 + 2])
            x1, z1 = x * cy - z * sy, x * sy + z * cy
            y1, z2 = y * cp - z1 * sp, y * sp + z1 * cp
            px, py = cx + x1 * sc, cyi + y1 * sc
            g = float(glow[k]) if k < len(glow) else 0.0
            if g > 0.08:
                col = (61, 255, 208)
                rr = 2
            else:
                col = (90, 98, 112)
                rr = 1
            draw.rectangle((px, py, px + rr, py + rr), fill=col)
        if frame.get("ate") or frame.get("trainer") and t01 > 0.47:
            overlay = Image.new("RGB", (bw_b, h), (61, 255, 208))
            brain_crop = pil.crop((bx0, 0, bx0 + bw_b, h))
            brain_crop = Image.blend(brain_crop, overlay, 0.12)
            pil.paste(brain_crop, (bx0, 0))

    # scope
    sx0 = world_w + brain_w
    draw.rectangle((sx0, 0, w, h), fill=(11, 16, 32))
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
    mx = max(0.2, max(r[1] for r in rows))
    for i, (lab, v) in enumerate(rows):
        y = 80 + i * 36
        draw.text((sx0 + 16, y), lab, fill=(180, 190, 210), font=font_sm)
        bwbar = int((w - sx0 - 32) * min(1.0, v / mx))
        draw.rectangle((sx0 + 16, y + 18, sx0 + 16 + max(4, bwbar), y + 28), fill=(61, 255, 208) if lab != "trainer" else (255, 122, 24))

    # chrome
    draw.text((24, 18), "FLYCIV", fill=(238, 243, 255), font=font_word)
    tr = "trainer ON" if frame.get("trainer") else "trainer OFF"
    draw.text((w - 320, 18), f"gen {frame.get('generation', 0)}  ·  {tr}", fill=(61, 255, 208) if frame.get("trainer") else (140, 150, 170), font=font_mid)
    title = _shot(t01)
    if title:
        draw.text((40, int(h * 0.72)), title, fill=(255, 255, 255), font=font_big)
    ev = frame.get("events") or []
    names_e = {"first_trail": "first trail", "first_store": "first store", "first_road": "roads", "trainer_unlocked": "trainer on", "trainer_child": "child born"}
    ticker = "  →  ".join(names_e.get(e.get("name", ""), e.get("name", "")) for e in ev)
    if t01 > 0.88:
        ticker = "tiny MaleCNS · frozen brain · evolving habits"
    draw.text((24, h - 48), ticker, fill=(200, 210, 230), font=font_sm)
    arr = np.array(pil)
    img[:] = arr


def render_clip(watch_json: Path, out_dir: Path, seconds: float = 13.5, fps: int = 24) -> tuple[Path, Path]:
    from PIL import Image

    payload = json.loads(Path(watch_json).read_text(encoding="utf-8"))
    frames = payload["frames"]
    cloud = payload.get("meta", {}).get("cloud") or spectator_cloud()
    soma = _dec_f32(cloud["xyz_b64"])
    n_s = int(cloud["n"])
    glow = np.zeros(n_s, dtype=np.float32)
    n_out = int(seconds * fps)
    out_dir = Path(out_dir)
    seq = out_dir / "png"
    seq.mkdir(parents=True, exist_ok=True)
    W, H = 1920, 1080
    img = np.zeros((H, W, 3), dtype=np.uint8)
    halo = cloud.get("halo") or []
    toy_idx = cloud.get("toy_idx") or []
    yaw = 0.95
    for k in range(n_out):
        t01 = k / max(1, n_out - 1)
        n = len(frames)
        if t01 < 0.12:
            fi = int((t01 / 0.12) * min(6, n - 1))
        else:
            rest = (t01 - 0.12) / 0.88
            fi = min(n - 1, 6 + int(rest * (n - 1 - 6)))
        f = frames[fi]
        spikes = f.get("spikes") or []
        glow *= 0.82
        for t, sp in enumerate(spikes):
            if not sp:
                continue
            if t < len(halo):
                for h in halo[t]:
                    if h < n_s:
                        glow[h] = max(glow[h], 0.7)
            if t < len(toy_idx) and toy_idx[t] < n_s:
                glow[int(toy_idx[t])] = 1.0
        yaw += 0.012
        render_frame(img, f, soma, yaw, 0.42, t01, glow)
        Image.fromarray(img).save(seq / f"f{k:04d}.png")
    wide = out_dir / "flyciv-watch-16x9.mp4"
    tall = out_dir / "flyciv-watch-9x16.mp4"
    import subprocess

    subprocess.check_call(
        [
            "ffmpeg", "-y", "-framerate", str(fps), "-i", str(seq / "f%04d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(wide),
        ]
    )
    # 9:16 crop of the same timeline: center-left map+brain
    subprocess.check_call(
        [
            "ffmpeg", "-y", "-i", str(wide),
            "-vf", "crop=720:1080:120:0,scale=1080:1920",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(tall),
        ]
    )
    return wide, tall
