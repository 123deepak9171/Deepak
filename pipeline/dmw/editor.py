"""EDITOR + COLORIST AGENTS: cutting, silence removal, vertical conversion, green screen,
color grading, camera zoom, image animation, transitions and merging (all FFmpeg)."""
from __future__ import annotations

from pathlib import Path

from . import ff
from .config import safe_path

GRADES = {
    "none": "",
    "natural": "eq=contrast=1.03:saturation=1.06",
    "warm-cinematic": "eq=contrast=1.08:saturation=1.1:gamma=0.98,colorbalance=rs=0.05:bs=-0.05:rh=0.04:bh=-0.04,vignette=angle=PI/5",
    "teal-orange": "colorbalance=rs=-0.06:gs=-0.01:bs=0.08:rh=0.08:gh=0.01:bh=-0.07,eq=contrast=1.1:saturation=1.15,vignette=angle=PI/5",
    "vibrant": "eq=contrast=1.06:saturation=1.35:brightness=0.01,unsharp=5:5:0.6",
    "earthy-mining": "colorbalance=rs=0.06:gs=0.02:bs=-0.06:rm=0.04:bm=-0.03,eq=contrast=1.12:saturation=1.05:gamma=0.97,vignette=angle=PI/6,unsharp=5:5:0.5",
    "documentary": "eq=contrast=1.05:saturation=0.9,colorbalance=bs=0.02",
    "bw": "hue=s=0,eq=contrast=1.18:brightness=0.01,vignette=angle=PI/5",
}

INTERMEDIATE = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p",
                "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]


def grade_filter(job: dict) -> str:
    parts = []
    g = GRADES.get(job.get("grade") or "none", "")
    if g:
        parts.append(g)
    if job.get("lut"):
        lut = str(safe_path(job["lut"], "lut")).replace(":", r"\:")
        parts.append(f"lut3d=file='{lut}'")
    return ",".join(parts)


def fit_chain(inp: str, out: str, W: int, H: int, mode: str, tag: str) -> list[str]:
    """Scale/crop any source to WxH. mode: crop | blur | pad (vertical conversion)."""
    if mode == "crop":
        return [f"[{inp}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[{out}]"]
    if mode == "pad":
        return [f"[{inp}]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x111111,setsar=1[{out}]"]
    return [
        f"[{inp}]split=2[{tag}a][{tag}b]",
        f"[{tag}a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=30,eq=brightness=-0.08[{tag}bg]",
        f"[{tag}b]scale={W}:{H}:force_original_aspect_ratio=decrease[{tag}fg]",
        f"[{tag}bg][{tag}fg]overlay=(W-w)/2:(H-h)/2,setsar=1[{out}]",
    ]


def zoom_chain(inp: str, out: str, W: int, H: int, fps: int, frames: int, strength: float, direction: str = "in",
               pan: str | None = None) -> list[str]:
    """Smooth camera zoom / Ken Burns using zoompan on an upscaled frame (reduces jitter)."""
    frames = max(frames, 2)
    rate = (strength - 1) / frames
    if direction == "out":
        z = f"max({strength:.4f}-{rate:.6f}*on,1)"
    else:
        z = f"min(1+{rate:.6f}*on,{strength:.4f})"
    x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if pan == "left":
        x = f"(iw-iw/zoom)*(1-on/{frames})"
    elif pan == "right":
        x = f"(iw-iw/zoom)*on/{frames}"
    W2, H2 = W * 3 // 2 // 2 * 2, H * 3 // 2 // 2 * 2
    return [f"[{inp}]scale={W2}:{H2},zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={fps}[{out}]"]


def cut_intervals(item: dict, info: dict, job: dict, cfg: dict, log) -> list[tuple[float, float]]:
    """Automatic cutting: trim points + silence removal."""
    start = float(item.get("start", 0) or 0)
    end = min(float(item.get("end") or info["duration"]), info["duration"])
    if end - start <= 0.1:
        raise ff.FFError(f"Clip ka duration bahut chhota hai: {item['src']}")
    if job["remove_silence"] and info["has_audio"] and item.get("remove_silence", True):
        sc = cfg["silence"]
        sil = ff.detect_silence(Path(info["path"]), sc["noise_db"], sc["min_silence"], log)
        keep = ff.speech_intervals(start, end, sil, sc["padding"], sc["min_keep"])
        return keep or [(start, end)]
    return [(start, end)]


def limit_intervals(intervals, budget: float):
    out, used = [], 0.0
    for s, e in intervals:
        if used >= budget:
            break
        e = min(e, s + (budget - used))
        if e - s >= 0.2:
            out.append((s, e))
            used += e - s
    return out, used


def render_video_item(item: dict, idx: int, job: dict, cfg: dict, work: Path, budget: float, log) -> tuple[Path, float]:
    src = safe_path(item["src"], "video")
    info = ff.media_info(src)
    if not info["has_video"]:
        raise ff.FFError(f"Isme video stream nahi hai: {item['src']}")
    intervals, used = limit_intervals(cut_intervals(item, info, job, cfg, log), budget)
    if not intervals:
        return None, 0.0
    W, H, fps = job["width"], job["height"], job["fps"]
    log.say(f"  [Editor] segment {idx} (video): {len(intervals)} part(s), {used:.1f}s rakha (original {info['duration']:.1f}s)")

    args = ["-i", src]
    fg: list[str] = []
    gs = item.get("greenscreen")
    n_in = 1
    if gs:
        bg = gs.get("background")
        if bg:
            bgp = safe_path(bg)
            if bgp.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
                args += ["-loop", "1", "-framerate", str(fps), "-i", bgp]
            else:
                args += ["-stream_loop", "-1", "-i", bgp]
        else:
            args += ["-f", "lavfi", "-i", f"color=c=0x1E1E1E:s={W}x{H}:r={fps}"]
        bg_idx = n_in
        n_in += 1
        fg += fit_chain(f"{bg_idx}:v", "gbg", W, H, "crop", "g1")
        fg += fit_chain("0:v", "gfg0", W, H, "crop" if job["fit_mode"] == "blur" else job["fit_mode"], "g2")
        # pad colour must be keyable: re-pad with key colour
        fg[-1] = fg[-1].replace("color=0x111111", f"color={gs['color']}")
        fg.append(f"[gfg0]chromakey={gs['color']}:{gs['similarity']}:{gs['blend']},despill=type=green[gfg]")
        fg.append("[gbg][gfg]overlay=shortest=1:format=auto[base0]")
    else:
        fg += fit_chain("0:v", "base0", W, H, job["fit_mode"], "f")

    grade = grade_filter(job)
    fg.append(f"[base0]fps={fps}{',' + grade if grade else ''},format=yuv420p[base]")

    if info["has_audio"]:
        a_src = "0:a"
    else:
        args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        a_src = f"{n_in}:a"
        n_in += 1

    k = len(intervals)
    fg.append(f"[base]split={k}" + "".join(f"[vs{i}]" for i in range(k)) if k > 1 else "[base]null[vs0]")
    fg.append(f"[{a_src}]asplit={k}" + "".join(f"[as{i}]" for i in range(k)) if k > 1 else f"[{a_src}]anull[as0]")
    for i, (s, e) in enumerate(intervals):
        punch = ""
        if job["punch_in"] and k > 1 and i % 2 == 1:
            pw, ph = int(W * 1.12) // 2 * 2, int(H * 1.12) // 2 * 2
            punch = f",scale={pw}:{ph},crop={W}:{H}"
        fg.append(f"[vs{i}]trim=start={s}:end={e},setpts=PTS-STARTPTS{punch},setsar=1[v{i}]")
        fg.append(f"[as{i}]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{i}]")
    fg.append("".join(f"[v{i}][a{i}]" for i in range(k)) + f"concat=n={k}:v=1:a=1[vc][ac]")
    if job["zoom"]:
        frames = int(used * fps)
        fg += zoom_chain("vc", "vz", W, H, fps, frames, job["zoom_strength"], "in" if idx % 2 == 0 else "out")
        last = "vz"
    else:
        last = "vc"
    fg.append(f"[{last}]fps={fps},format=yuv420p,setsar=1[vout]")
    fg.append("[ac]aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo[aout]")

    out = work / f"seg_{idx:03d}_video.mkv"
    ff.ffmpeg([*args, "-filter_complex", ";".join(fg), "-map", "[vout]", "-map", "[aout]",
               "-t", f"{used:.3f}", *INTERMEDIATE, out], log=log)
    return out, ff.media_info(out)["duration"]


KB_MOVES = [("in", None), ("out", None), ("in", "left"), ("in", "right")]


def render_image_item(item: dict, idx: int, job: dict, cfg: dict, work: Path, log) -> tuple[Path, float]:
    """Photo -> animated clip (Ken Burns zoom/pan) with silent audio."""
    src = safe_path(item["src"], "image")
    W, H, fps = job["width"], job["height"], job["fps"]
    dur = float(item["duration"])
    frames = int(dur * fps)
    direction, pan = KB_MOVES[idx % len(KB_MOVES)]
    if item.get("animation") in ("zoom-in", "zoom-out", "pan-left", "pan-right"):
        a = item["animation"]
        direction = "out" if a == "zoom-out" else "in"
        pan = a.split("-")[1] if a.startswith("pan") else None
    fg = fit_chain("0:v", "fit", W, H, job["fit_mode"], "i")
    grade = grade_filter(job)
    fg.append(f"[fit]format=yuv420p{',' + grade if grade else ''}[g]")
    fg += zoom_chain("g", "z", W, H, fps, frames, 1.15, direction, pan)
    fg.append(f"[z]fps={fps},format=yuv420p,setsar=1[vout]")
    out = work / f"seg_{idx:03d}_image.mkv"
    log.say(f"  [Editor] segment {idx} (photo): Ken Burns {direction}{'/' + pan if pan else ''} {dur}s")
    ff.ffmpeg(["-loop", "1", "-framerate", str(fps), "-i", src, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
               "-filter_complex", ";".join(fg), "-map", "[vout]", "-map", "1:a", "-t", f"{dur:.3f}",
               *INTERMEDIATE, out], log=log)
    return out, ff.media_info(out)["duration"]


def normalize_external(src: Path, idx: int, name: str, job: dict, work: Path, log) -> tuple[Path, float]:
    """Bring a Remotion/other MP4 to the common intermediate format (+silent audio if needed)."""
    info = ff.media_info(src)
    W, H, fps = job["width"], job["height"], job["fps"]
    args = ["-i", src]
    amap = "0:a"
    if not info["has_audio"]:
        args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        amap = "1:a"
    out = work / f"seg_{idx:03d}_{name}.mkv"
    ff.ffmpeg([*args, "-vf", f"scale={W}:{H},fps={fps},format=yuv420p,setsar=1", "-map", "0:v", "-map", amap,
               "-t", f"{info['duration']:.3f}", *INTERMEDIATE, out], log=log)
    return out, ff.media_info(out)["duration"]


def merge_segments(segs: list[tuple[Path, float]], job: dict, work: Path, log) -> tuple[Path, list[float], float]:
    """Join all segments with xfade/acrossfade transitions. Returns (path, transition_times, duration)."""
    out = work / "merged.mkv"
    if len(segs) == 1:
        ff.ffmpeg(["-i", segs[0][0], "-c", "copy", out], log=log)
        return out, [], segs[0][1]
    types = job["transitions"]["types"] or ["fade"]
    td = float(job["transitions"]["duration"])
    td = max(0.1, min(td, min(d for _, d in segs) / 2.5))
    args, fg = [], []
    for p, _ in segs:
        args += ["-i", p]
    vprev, aprev, length, times = "0:v", "0:a", segs[0][1], []
    for i in range(1, len(segs)):
        offset = length - td
        t = types[(i - 1) % len(types)]
        vo, ao = f"xv{i}", f"xa{i}"
        fg.append(f"[{vprev}][{i}:v]xfade=transition={t}:duration={td:.3f}:offset={offset:.3f}[{vo}]")
        fg.append(f"[{aprev}][{i}:a]acrossfade=d={td:.3f}:c1=tri:c2=tri[{ao}]")
        times.append(round(offset, 3))
        length = length + segs[i][1] - td
        vprev, aprev = vo, ao
    log.say(f"  [Editor] {len(segs)} segments merge (transitions: {', '.join(types)}, {td:.2f}s)")
    ff.ffmpeg([*args, "-filter_complex", ";".join(fg), "-map", f"[{vprev}]", "-map", f"[{aprev}]",
               *INTERMEDIATE, out], log=log)
    return out, times, ff.media_info(out)["duration"]
