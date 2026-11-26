"""MOTION GRAPHICS AGENT: logo animation, product reveal, title cards, outro via Remotion.
Falls back to an FFmpeg drawtext card if Remotion/Chromium is not available."""
from __future__ import annotations

import glob
import json
import os
import shutil
from pathlib import Path

from . import ff
from .config import ROOT, safe_path

REMOTION_DIR = ROOT / "remotion"
FONT = ROOT / "assets" / "fonts" / "Poppins-ExtraBold.ttf"


def find_browser(cfg: dict) -> str | None:
    """'auto': use DMW_BROWSER env, else Playwright's preinstalled headless shell (cloud
    sessions where Remotion's own browser download is blocked), else let Remotion download."""
    setting = os.environ.get("DMW_BROWSER") or cfg["remotion"].get("browser_executable", "auto")
    if setting and setting != "auto":
        return setting
    hits = sorted(glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell"))
    return hits[-1] if hits else None


def _stage_asset(src: str | None, job_id: str, name: str) -> str | None:
    if not src:
        return None
    p = safe_path(src, "image")
    dest_dir = REMOTION_DIR / "public" / "job" / job_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{name}{p.suffix.lower()}"
    shutil.copy2(p, dest)
    return f"job/{job_id}/{dest.name}"


def render_remotion(comp: str, props: dict, out: Path, cfg: dict, log) -> Path:
    if not (REMOTION_DIR / "node_modules" / "remotion").exists():
        raise ff.FFError("Remotion node_modules missing: `cd remotion && npm ci` chalao")
    props_file = out.with_suffix(".props.json")
    props_file.write_text(json.dumps(props), encoding="utf-8")
    cmd = ["npx", "remotion", "render", "src/index.ts", comp, str(out), f"--props={props_file}",
           f"--concurrency={cfg['remotion']['concurrency']}", "--log=error", "--codec=h264"]
    b = find_browser(cfg)
    if b:
        cmd.append(f"--browser-executable={b}")
    ff.run(cmd, log=log, cwd=REMOTION_DIR, timeout=cfg["remotion"]["timeout_sec"])
    return out


def ffmpeg_card(text: str, sub: str, dur: float, job: dict, out: Path, log) -> Path:
    W, H, fps = job["width"], job["height"], job["fps"]
    unit = min(W, H)
    esc = lambda t: t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")
    vf = (f"drawtext=fontfile={FONT}:text='{esc(text)}':fontcolor=white:fontsize={int(unit*0.09)}:"
          f"x=(w-tw)/2:y=(h-th)/2-{int(unit*0.05)},"
          f"drawtext=fontfile={FONT}:text='{esc(sub)}':fontcolor=0xF5A623:fontsize={int(unit*0.045)}:"
          f"x=(w-tw)/2:y=(h/2)+{int(unit*0.05)},fade=t=in:d=0.4,fade=t=out:st={max(dur-0.4,0)}:d=0.4")
    ff.ffmpeg(["-f", "lavfi", "-i", f"color=c=0x111111:s={W}x{H}:r={fps}:d={dur}", "-vf", vf,
               "-c:v", "libx264", "-pix_fmt", "yuv420p", out], log=log)
    return out


def scene(kind: str, job: dict, cfg: dict, work: Path, log, **kw) -> Path:
    """Render one motion scene. kind: intro | outro | product | title."""
    base = {"width": job["width"], "height": job["height"], "fps": job["fps"]}
    brand = cfg["brand"]
    jid = job["id"]
    if kind == "intro":
        comp, dur = "LogoReveal", job["logo"]["intro_duration"]
        props = {**base, "durationSec": dur, "logo": _stage_asset(job["logo"]["src"], jid, "logo"),
                 "tagline": job["logo"].get("tagline", brand["tagline"])}
        fb = (brand["name"], brand["tagline"])
    elif kind == "outro":
        comp, dur = "Outro", job["logo"]["outro_duration"]
        props = {**base, "durationSec": dur, "logo": _stage_asset(job["logo"]["src"], jid, "logo"),
                 "cta": job["logo"].get("cta", brand["outro_cta"])}
        fb = (brand["name"], brand["outro_cta"])
    elif kind == "product":
        pr = job["product_reveal"]
        comp, dur = "ProductReveal", pr["duration"]
        props = {**base, "durationSec": dur, "title": pr["title"], "subtitle": pr["subtitle"],
                 "image": _stage_asset(pr.get("image"), jid, "product"), "price": pr.get("price", "")}
        fb = (pr["title"], pr["subtitle"])
    else:
        it = kw["item"]
        comp, dur = "TitleCard", float(it["duration"])
        props = {**base, "durationSec": dur, "title": it.get("title", ""), "subtitle": it.get("subtitle", "")}
        fb = (it.get("title", ""), it.get("subtitle", ""))
    out = work / f"remotion_{kind}_{kw.get('n', 0)}.mp4"
    try:
        log.say(f"  [Motion] Remotion {comp} render ({dur}s)...")
        return render_remotion(comp, props, out, cfg, log)
    except ff.FFError as e:
        log.say(f"  [Motion] Remotion fail hua, FFmpeg fallback card use kar rahe hain: {str(e).splitlines()[0]}")
        return ffmpeg_card(fb[0], fb[1], dur, job, out, log)


def cleanup(job_id: str) -> None:
    shutil.rmtree(REMOTION_DIR / "public" / "job" / job_id, ignore_errors=True)
