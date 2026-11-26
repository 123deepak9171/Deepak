"""Real production tools used by the specialist agents (all offline + free).

storyboard   - contact-sheet storyboard from a job (Storyboard agent)
sfx          - synthesize sound effects (Sound Effects agent)
music_bed    - synthesize a placeholder music bed (Background Music agent)
voiceover    - offline TTS guide voice with espeak-ng (Voiceover agent)
track        - face / motion tracking + subject-following reframe (Tracking agent)
shift_audio  - fix audio/video sync offset (Lip Sync agent)
qc_deep      - black/freeze/silence/loudness checks + contact sheet (QC agent)
export       - platform deliverables + checksums (Final Export agent)
grade_preview- side-by-side color grade comparison (Color Grading agent)
still        - Remotion still (thumbnail/poster) (Image Generation agent)
asset_scan   - asset manifest with metadata + duplicate detection (Asset agent)
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

from . import editor, ff
from .config import ROOT, load_config, rel, safe_path, slug

FONT = ROOT / "assets" / "fonts" / "Poppins-ExtraBold.ttf"
PRODUCTIONS = ROOT / "productions"


def production_dir(pid: str) -> Path:
    d = PRODUCTIONS / slug(pid)
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------- storyboard
def storyboard(job_path: Path, out_dir: Path | None = None) -> dict:
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    from .planner import normalize_job  # noqa: PLC0415

    raw = json.loads(Path(job_path).read_text(encoding="utf-8"))
    raw.setdefault("id", Path(job_path).stem)
    job = normalize_job(raw)
    out_dir = out_dir or production_dir(job["id"])
    vertical = job["height"] > job["width"]
    tw, th = (270, 480) if vertical else (480, 270)
    tmp = out_dir / "_sb"
    tmp.mkdir(exist_ok=True)
    cards = []
    if job["logo"]["intro"]:
        cards.append(("INTRO", "Logo reveal", f"{job['logo']['intro_duration']}s", None))
    pr = job["product_reveal"]
    if pr.get("enabled") and pr["position"] == "start":
        cards.append(("PRODUCT", pr["title"], f"{pr['duration']}s", pr.get("image")))
    for i, it in enumerate(job["timeline"], 1):
        if it["type"] == "video":
            info = ff.media_info(safe_path(it["src"], "video"))
            s, e = float(it.get("start", 0) or 0), float(it.get("end") or info["duration"])
            fr = tmp / f"f{i}.jpg"
            ff.ffmpeg(["-ss", f"{(s + e) / 2:.2f}", "-i", safe_path(it["src"]), "-frames:v", "1", fr])
            note = "green screen" if it.get("greenscreen") else Path(it["src"]).name
            cards.append((f"CLIP {i}", note, f"{e - s:.1f}s raw", str(fr)))
        elif it["type"] == "image":
            cards.append((f"PHOTO {i}", it.get("animation", "ken burns"), f"{it['duration']}s", it["src"]))
        else:
            cards.append((f"TITLE {i}", it.get("title", ""), f"{it['duration']}s", None))
    if pr.get("enabled") and pr["position"] == "end":
        cards.append(("PRODUCT", pr["title"], f"{pr['duration']}s", pr.get("image")))
    if job["logo"]["outro"]:
        cards.append(("OUTRO", "Logo + Subscribe", f"{job['logo']['outro_duration']}s", None))

    tiles = []
    for head, note, dur, img in cards:
        tile = np.full((th + 70, tw, 3), (17, 17, 17), np.uint8)
        if img:
            p = Path(img) if Path(img).is_absolute() else ROOT / img
            im = cv2.imread(str(p))
            if im is not None:
                h, w = im.shape[:2]
                sc = max(tw / w, th / h)
                im = cv2.resize(im, (int(w * sc) + 1, int(h * sc) + 1))
                y0, x0 = (im.shape[0] - th) // 2, (im.shape[1] - tw) // 2
                tile[:th] = im[y0:y0 + th, x0:x0 + tw]
        else:
            tile[:th] = (30, 30, 30)
            cv2.circle(tile, (tw // 2, th // 2), min(tw, th) // 5, (35, 166, 245), 4)
        cv2.rectangle(tile, (0, th), (tw, th + 70), (35, 166, 245), -1)
        cv2.putText(tile, f"{head}  {dur}", (8, th + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (17, 17, 17), 2)
        cv2.putText(tile, note[:28], (8, th + 58), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (17, 17, 17), 1)
        tiles.append(tile)
    cols = min(4 if vertical else 3, len(tiles))
    rows = math.ceil(len(tiles) / cols)
    blank = np.full_like(tiles[0], 17)
    grid = [np.hstack([tiles[r * cols + c] if r * cols + c < len(tiles) else blank for c in range(cols)]) for r in range(rows)]
    sheet = np.vstack(grid)
    out = out_dir / "storyboard.jpg"
    cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
    md = ["| # | Scene | Note | Duration |", "|---|---|---|---|"]
    md += [f"| {i} | {h} | {n} | {d} |" for i, (h, n, d, _) in enumerate(cards, 1)]
    (out_dir / "storyboard.md").write_text(f"# Storyboard: {job['title']}\n\n![storyboard](storyboard.jpg)\n\n" + "\n".join(md) + "\n", encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    return {"storyboard": rel(out), "scenes": len(cards)}


# ---------------------------------------------------------------- sound
SFX = {
    "whoosh": ["-f", "lavfi", "-i", "anoisesrc=d=0.7:c=pink:r=48000:a=0.7",
               "-af", "highpass=f=300,lowpass=f=5000,afade=t=in:d=0.3,afade=t=out:st=0.35:d=0.35"],
    "swipe": ["-f", "lavfi", "-i", "anoisesrc=d=0.3:c=white:r=48000:a=0.5",
              "-af", "highpass=f=2000,afade=t=in:d=0.05,afade=t=out:st=0.1:d=0.2"],
    "boom": ["-f", "lavfi", "-i", "aevalsrc=0.9*sin(2*PI*(45+50*exp(-6*t))*t)*exp(-2.5*t):s=48000:d=1.8"],
    "riser": ["-f", "lavfi", "-i", "aevalsrc=0.35*sin(2*PI*(180*t+260*t*t))*min(t/1.8\\,1):s=48000:d=2.2",
              "-af", "afade=t=out:st=2.0:d=0.2"],
    "ding": ["-f", "lavfi", "-i", "aevalsrc=0.5*sin(2*PI*1320*t)*exp(-5*t)+0.25*sin(2*PI*2640*t)*exp(-8*t):s=48000:d=1.2"],
    "click": ["-f", "lavfi", "-i", "aevalsrc=0.8*sin(2*PI*2200*t)*exp(-90*t):s=48000:d=0.12"],
    "cash": ["-f", "lavfi", "-i", "aevalsrc=0.4*sin(2*PI*1800*t)*exp(-12*t)+0.4*sin(2*PI*2400*(t-0.08))*exp(-12*(t-0.08))*gte(t\\,0.08):s=48000:d=0.8"],
}


def sfx(kind: str, out: Path | None = None) -> dict:
    if kind not in SFX:
        raise ValueError(f"SFX type: {', '.join(SFX)}")
    out = out or ROOT / "assets" / "sfx" / f"{kind}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    ff.ffmpeg([*SFX[kind], "-ac", "2", "-ar", "48000", out])
    return {"sfx": rel(out), "info": ff.media_info(out)}


def music_bed(mood: str, duration: float, out: Path | None = None) -> dict:
    """Synthetic, royalty-free PLACEHOLDER bed (simple chords + pulse). Not AI music."""
    moods = {
        "calm": (70, "0.12*sin(2*PI*220*t)+0.10*sin(2*PI*261.6*t)+0.09*sin(2*PI*329.6*t)", "0"),
        "energetic": (120, "0.10*sin(2*PI*110*t)+0.08*sin(2*PI*164.8*t)+0.07*sin(2*PI*220*t)",
                      "0.8*sin(2*PI*55*t)*exp(-14*mod(t\\,0.5))"),
        "epic": (90, "0.12*sin(2*PI*98*t)+0.10*sin(2*PI*146.8*t)+0.08*sin(2*PI*196*t)",
                 "0.9*sin(2*PI*48*t)*exp(-9*mod(t\\,0.6667))"),
        "desi": (100, "0.10*sin(2*PI*146.8*t)+0.08*sin(2*PI*220*t)+0.06*sin(2*PI*293.7*t)",
                 "0.7*sin(2*PI*70*t)*exp(-12*mod(t\\,0.6))+0.4*sin(2*PI*140*t)*exp(-20*mod(t+0.3\\,0.6))"),
    }
    if mood not in moods:
        raise ValueError(f"mood: {', '.join(moods)}")
    _, pad, beat = moods[mood]
    out = out or ROOT / "assets" / "music" / f"bed_{mood}_{int(duration)}s.mp3"
    out.parent.mkdir(parents=True, exist_ok=True)
    ff.ffmpeg(["-f", "lavfi", "-i", f"aevalsrc=({pad})*(0.75+0.25*sin(2*PI*0.25*t))+({beat}):s=48000:d={duration}",
               "-af", f"lowpass=f=6000,afade=t=in:d=1.5,afade=t=out:st={max(duration - 2, 0)}:d=2,loudnorm=I=-18",
               "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k", out])
    return {"music": rel(out), "mood": mood, "duration": duration, "note": "synthetic placeholder bed"}


def voiceover(text: str, out: Path, lang: str = "hi", speed: int = 145) -> dict:
    """Offline TTS with espeak-ng. Robotic 'guide voice' for timing - not a human-quality voice."""
    if not shutil.which("espeak-ng"):
        raise RuntimeError("espeak-ng install nahi hai (sudo apt-get install espeak-ng). Ya apni recorded voice do.")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".raw.wav")
    subprocess.run(["espeak-ng", "-v", lang, "-s", str(speed), "-w", str(tmp), text], check=True, timeout=120)
    ff.ffmpeg(["-i", tmp, "-af", "highpass=f=80,loudnorm=I=-16:TP=-1.5", "-ar", "48000", "-ac", "2", out])
    tmp.unlink(missing_ok=True)
    return {"voiceover": rel(out), "duration": ff.media_info(out)["duration"], "engine": "espeak-ng", "lang": lang}


# ---------------------------------------------------------------- tracking
def track(video: Path, out_json: Path, mode: str = "auto", sample_fps: float = 5.0,
          reframe: str | None = None, reframe_out: Path | None = None) -> dict:
    """Face (Haar cascade) or motion tracking -> per-time subject centre; optional subject-following crop."""
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    step = max(1, round(fps / sample_fps))
    face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    pts, prev, n, last = [], None, 0, (W / 2, H / 2)
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if n % step == 0:
            small = cv2.GaussianBlur(frame, (9, 9), 0)
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            src, c = "hold", last
            if mode in ("face", "auto"):
                faces = face.detectMultiScale(gray, 1.1, 5, minSize=(H // 12, H // 12))
                if len(faces):
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                    c, src = (x + w / 2, y + h / 2), "face"
            if src == "hold" and mode in ("motion", "auto") and prev is not None:
                # colour-aware difference (orange vs green has nearly equal gray values)
                diff = cv2.threshold(cv2.absdiff(prev, small).max(axis=2), 25, 255, cv2.THRESH_BINARY)[1]
                m = cv2.moments(diff)
                if m["m00"] > 255 * W * H * 0.002:
                    c, src = (m["m10"] / m["m00"], m["m01"] / m["m00"]), "motion"
            prev, last = small, c
            pts.append({"t": round(n / fps, 3), "x": round(c[0], 1), "y": round(c[1], 1), "src": src})
        n += 1
    cap.release()
    # smoothing (EMA) so the virtual camera does not shake
    a, sx, sy = 0.35, None, None
    for p in pts:
        sx = p["x"] if sx is None else a * p["x"] + (1 - a) * sx
        sy = p["y"] if sy is None else a * p["y"] + (1 - a) * sy
        p["sx"], p["sy"] = round(sx, 1), round(sy, 1)
    stats = {k: sum(1 for p in pts if p["src"] == k) for k in ("face", "motion", "hold")}
    res = {"video": rel(video), "width": W, "height": H, "fps": fps, "frames": n, "samples": len(pts), "sources": stats, "points": pts}
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(res, indent=1), encoding="utf-8")
    if reframe:
        aw, ah = map(int, reframe.split(":"))
        cw = min(W, int(H * aw / ah) // 2 * 2)
        ch = min(H, int(W * ah / aw) // 2 * 2) if cw == W else H
        reframe_out = reframe_out or out_json.with_suffix(".reframed.mp4")
        ts = np.array([p["t"] for p in pts]) if pts else np.array([0.0])
        xs = np.array([p["sx"] for p in pts]) if pts else np.array([W / 2])
        ys = np.array([p["sy"] for p in pts]) if pts else np.array([H / 2])
        cap = cv2.VideoCapture(str(video))
        enc = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                                "-s", f"{cw}x{ch}", "-r", str(fps), "-i", "-", "-i", str(video), "-map", "0:v", "-map", "1:a?",
                                "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(reframe_out)],
                               stdin=subprocess.PIPE)
        i = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            t = i / fps
            cx, cy = float(np.interp(t, ts, xs)), float(np.interp(t, ts, ys))
            x0 = int(min(max(cx - cw / 2, 0), W - cw))
            y0 = int(min(max(cy - ch / 2, 0), H - ch))
            enc.stdin.write(np.ascontiguousarray(frame[y0:y0 + ch, x0:x0 + cw]).tobytes())
            i += 1
        cap.release()
        enc.stdin.close()
        if enc.wait() != 0:
            raise ff.FFError("reframe encode fail")
        res["reframed"] = rel(reframe_out)
    res.pop("points")
    return res


def shift_audio(video: Path, ms: int, out: Path) -> dict:
    """Lip-sync offset fix: positive ms delays audio, negative advances it."""
    off = ms / 1000
    ff.ffmpeg(["-i", video, "-itsoffset", f"{off:.3f}", "-i", video, "-map", "0:v", "-map", "1:a",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out])
    return {"output": rel(out), "audio_shift_ms": ms}


# ---------------------------------------------------------------- QC / export
def qc_deep(mp4: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    info = ff.media_info(mp4)
    log = ff.ffmpeg(["-i", mp4, "-vf", "blackdetect=d=0.5:pix_th=0.08,freezedetect=n=-60dB:d=2",
                     "-af", "silencedetect=n=-50dB:d=1.5,ebur128=framelog=quiet", "-f", "null", "-"])
    black = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", log)]
    freeze = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", log)]
    silence = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
    tpk = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", log)
    lufs_v = float(lufs[-1]) if lufs else None
    sheet = out_dir / "contact_sheet.jpg"
    n = 12
    ff.ffmpeg(["-i", mp4, "-vf", f"fps={n / max(info['duration'], 1):.4f},scale=240:-2,tile=6x2", "-frames:v", "1", sheet])
    warnings = []
    mid_black = [b for b in black if b[0] > 0.6 and b[1] < info["duration"] - 0.6]
    if mid_black:
        warnings.append(f"Beech me black frames: {mid_black}")
    if freeze:
        warnings.append(f"Freeze frames at {freeze}s")
    if silence:
        warnings.append(f"Lambi silence at {silence}s")
    if lufs_v is not None and not -16.5 <= lufs_v <= -11.5:
        warnings.append(f"Loudness {lufs_v} LUFS (target -14)")
    checks = {"h264": info["vcodec"] == "h264", "aac": info["acodec"] == "aac", "yuv420p": info["pix_fmt"] == "yuv420p",
              "faststart": _faststart(mp4)}
    rep = {"file": rel(mp4), "info": info, "loudness_lufs": lufs_v, "true_peak_dbfs": float(tpk[-1]) if tpk else None,
           "black": black, "freeze_starts": freeze, "silence_starts": silence, "checks": checks,
           "warnings": warnings, "status": "PASS" if all(checks.values()) and not warnings else ("WARN" if all(checks.values()) else "FAIL"),
           "contact_sheet": rel(sheet)}
    (out_dir / "qc-report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    return rep


def _faststart(mp4: Path) -> bool:
    with open(mp4, "rb") as f:
        head = f.read(4096 * 16)
    m, d = head.find(b"moov"), head.find(b"mdat")
    return m != -1 and (d == -1 or m < d)


EXPORTS = {
    "master": {"desc": "Original quality copy"},
    "youtube": {"w": 1920, "h": 1080, "crf": 18, "ab": "192k"},
    "shorts": {"w": 1080, "h": 1920, "crf": 19, "ab": "192k"},
    "reels": {"w": 1080, "h": 1920, "crf": 20, "ab": "160k", "maxrate": "8M"},
    "whatsapp": {"short": 720, "target_mb": 15.5, "ab": "96k"},
    "square": {"w": 1080, "h": 1080, "crf": 20, "ab": "160k"},
}


def export(mp4: Path, presets: list[str], out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    info = ff.media_info(mp4)
    stem = mp4.stem
    files = []
    for p in presets:
        if p not in EXPORTS:
            raise ValueError(f"preset: {', '.join(EXPORTS)}")
        o = out_dir / f"{stem}_{p}.mp4"
        e = EXPORTS[p]
        common = ["-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-ar", "48000", "-ac", "2"]
        if p == "master":
            shutil.copy2(mp4, o)
        elif p == "whatsapp":
            vertical = info["height"] > info["width"]
            sc = "scale=720:-2" if vertical else "scale=-2:720"
            kbps = int((e["target_mb"] * 8192) / max(info["duration"], 1) - 96)
            kbps = max(min(kbps, 2500), 300)
            ff.ffmpeg(["-i", mp4, "-vf", sc, "-c:v", "libx264", "-preset", "medium", "-b:v", f"{kbps}k",
                       "-maxrate", f"{int(kbps * 1.3)}k", "-bufsize", f"{kbps * 2}k", "-b:a", e["ab"], *common, o])
        else:
            fit = editor.fit_chain("0:v", "v", e["w"], e["h"], "blur", "x")
            args = ["-i", mp4, "-filter_complex", ";".join(fit), "-map", "[v]", "-map", "0:a", "-c:v", "libx264",
                    "-preset", "medium", "-crf", str(e["crf"]), "-b:a", e["ab"], *common]
            if e.get("maxrate"):
                args += ["-maxrate", e["maxrate"], "-bufsize", "16M"]
            ff.ffmpeg([*args, o])
        oi = ff.media_info(o)
        files.append({"preset": p, "file": rel(o), "width": oi["width"], "height": oi["height"],
                      "duration": oi["duration"], "size_mb": round(oi["size_bytes"] / 1e6, 2),
                      "sha256": hashlib.sha256(o.read_bytes()).hexdigest()})
    man = {"source": rel(mp4), "exports": files}
    (out_dir / "export-manifest.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    return man


def grade_preview(video: Path, grades: list[str], out: Path, t: float | None = None) -> dict:
    info = ff.media_info(video)
    t = info["duration"] / 2 if t is None else t
    args, fg = [], []
    for i, g in enumerate(grades):
        if g not in editor.GRADES:
            raise ValueError(f"grade: {', '.join(editor.GRADES)}")
        args += ["-ss", f"{t:.2f}", "-i", video]
        flt = editor.GRADES[g] or "null"
        fg.append(f"[{i}:v]scale=480:-2,{flt},drawtext=fontfile={FONT}:text='{g}':fontsize=26:fontcolor=white:"
                  f"box=1:boxcolor=black@0.6:x=10:y=10[g{i}]")
    cols = min(3, len(grades))
    rows = math.ceil(len(grades) / cols)
    lay = "|".join(f"{'+'.join(['w0'] * (i % cols)) or '0'}_{'+'.join(['h0'] * (i // cols)) or '0'}" for i in range(len(grades)))
    fg.append("".join(f"[g{i}]" for i in range(len(grades))) + f"xstack=inputs={len(grades)}:layout={lay}:fill=black[o]"
              if len(grades) > 1 else "[g0]null[o]")
    out.parent.mkdir(parents=True, exist_ok=True)
    ff.ffmpeg([*args, "-filter_complex", ";".join(fg), "-map", "[o]", "-frames:v", "1", out])
    return {"preview": rel(out), "grades": grades, "rows": rows}


def still(comp: str, props: dict, out: Path) -> dict:
    from .motion import REMOTION_DIR, find_browser  # noqa: PLC0415
    out.parent.mkdir(parents=True, exist_ok=True)
    pf = out.with_suffix(".props.json")
    pf.write_text(json.dumps(props), encoding="utf-8")
    cmd = ["npx", "remotion", "still", "src/index.ts", comp, str(out), f"--props={pf}", "--log=error"]
    b = find_browser(load_config())
    if b:
        cmd.append(f"--browser-executable={b}")
    ff.run(cmd, cwd=REMOTION_DIR, timeout=300)
    pf.unlink(missing_ok=True)
    return {"still": rel(out)}


def asset_scan() -> dict:
    from .config import ALLOWED_MEDIA  # noqa: PLC0415
    kinds = {"raw-videos": "video", "photos": "image", "logos": "image", "music": "audio", "sfx": "audio",
             "scripts": "text", "luts": "lut", "demo": None}
    man, by_hash = {}, {}
    for folder, kind in kinds.items():
        d = ROOT / "assets" / folder
        items = []
        if d.exists():
            for p in sorted(d.rglob("*")):
                if not p.is_file() or p.name.startswith("."):
                    continue
                ext = p.suffix.lower()
                k = kind or next((kk for kk, ex in ALLOWED_MEDIA.items() if ext in ex), None)
                if not k:
                    continue
                h = hashlib.sha1()
                with open(p, "rb") as f:
                    h.update(f.read(8 << 20))
                h.update(str(p.stat().st_size).encode())
                entry = {"path": rel(p), "kind": k, "size_mb": round(p.stat().st_size / 1e6, 3), "hash": h.hexdigest()[:16]}
                if k in ("video", "audio", "image"):
                    try:
                        mi = ff.media_info(p)
                        entry.update({x: mi[x] for x in ("duration", "width", "height", "vcodec", "acodec")})
                    except ff.FFError:
                        entry["error"] = "unreadable"
                by_hash.setdefault(entry["hash"], []).append(entry["path"])
                items.append(entry)
        man[folder] = items
    man["_duplicates"] = [v for v in by_hash.values() if len(v) > 1]
    (ROOT / "assets" / "manifest.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    return {"files": sum(len(v) for k, v in man.items() if not k.startswith("_")), "duplicates": man["_duplicates"]}


def merge_audio(prod_dir: Path) -> dict:
    """Merge audio fragments written by voiceover / sound-effects / background-music agents
    (audio/vo-cues.json, audio/sfx-cues.json, audio/music.json) into audio/audio-timing.json."""
    a = Path(prod_dir) / "audio"
    a.mkdir(parents=True, exist_ok=True)
    load = lambda n, d: json.loads((a / n).read_text(encoding="utf-8")) if (a / n).exists() else d  # noqa: E731
    merged = {"voiceover": load("vo-cues.json", []), "sfx": load("sfx-cues.json", []), "music": load("music.json", {}),
              "sources": [n for n in ("vo-cues.json", "sfx-cues.json", "music.json") if (a / n).exists()]}
    for item in merged["voiceover"] + merged["sfx"] + ([merged["music"]] if merged["music"].get("src") else []):
        safe_path(item["src"], "audio")  # fail early on missing files
    if not merged["music"]:
        merged.pop("music")
    (a / "audio-timing.json").write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"audio_timing": rel(a / "audio-timing.json"), "voiceover": len(merged["voiceover"]), "sfx": len(merged["sfx"]),
            "music": bool(merged.get("music"))}
