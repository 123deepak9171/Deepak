"""Thin, safe wrappers around ffmpeg / ffprobe (no shell, timeouts, logging)."""
from __future__ import annotations

import json
import re
import shlex
import subprocess
from pathlib import Path


class FFError(RuntimeError):
    pass


class Logger:
    def __init__(self, path: Path | None = None, verbose: bool = True):
        self.path = path
        self.verbose = verbose
        self.fh = open(path, "a", encoding="utf-8") if path else None

    def say(self, msg: str) -> None:
        if self.verbose:
            print(msg, flush=True)
        self.raw(msg + "\n")

    def raw(self, text: str) -> None:
        if self.fh:
            self.fh.write(text)
            self.fh.flush()

    def close(self):
        if self.fh:
            self.fh.close()


def run(cmd: list[str], log: Logger | None = None, cwd: Path | None = None, timeout: int = 3600) -> str:
    if log:
        log.raw("\n$ " + " ".join(shlex.quote(str(c)) for c in cmd) + "\n")
    try:
        p = subprocess.run([str(c) for c in cmd], cwd=cwd, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise FFError(f"Timeout ({timeout}s): {cmd[0]}") from e
    if log:
        log.raw(p.stdout[-30000:] + "\n")
    if p.returncode != 0:
        raise FFError(f"Command fail hua ({p.returncode}): {' '.join(map(str, cmd[:6]))} ...\n{p.stdout[-2500:]}")
    return p.stdout


def ffmpeg(args: list, log: Logger | None = None, cwd: Path | None = None, timeout: int = 3600) -> str:
    return run(["ffmpeg", "-hide_banner", "-nostdin", "-y", *args], log=log, cwd=cwd, timeout=timeout)


def probe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format",
                          "-show_streams", str(path)], capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise FFError(f"ffprobe fail: {path}: {out.stderr[-500:]}")
    return json.loads(out.stdout)


def media_info(path: Path) -> dict:
    d = probe(path)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    dur = float(d["format"].get("duration") or (v or {}).get("duration") or 0)
    fps = 0.0
    if v and v.get("avg_frame_rate") not in (None, "0/0"):
        n, dd = v["avg_frame_rate"].split("/")
        fps = float(n) / float(dd) if float(dd) else 0.0
    return {
        "path": str(path),
        "duration": round(dur, 3),
        "width": int(v["width"]) if v else 0,
        "height": int(v["height"]) if v else 0,
        "fps": round(fps, 3),
        "vcodec": v["codec_name"] if v else None,
        "pix_fmt": v.get("pix_fmt") if v else None,
        "profile": v.get("profile") if v else None,
        "acodec": a["codec_name"] if a else None,
        "sample_rate": int(a["sample_rate"]) if a else None,
        "channels": a.get("channels") if a else None,
        "has_video": v is not None,
        "has_audio": a is not None,
        "size_bytes": int(d["format"].get("size", 0)),
        "bit_rate": int(d["format"].get("bit_rate", 0) or 0),
        "format": d["format"].get("format_name"),
    }


def detect_silence(path: Path, noise_db: float, min_dur: float, log: Logger | None = None) -> list[tuple[float, float]]:
    """Return list of (silence_start, silence_end) in seconds."""
    out = ffmpeg(["-i", path, "-vn", "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}", "-f", "null", "-"], log=None)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    res = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else float("inf")
        res.append((max(0.0, s), e))
    if log:
        log.raw(f"silences in {path}: {res}\n")
    return res


def speech_intervals(start: float, end: float, silences: list[tuple[float, float]], padding: float, min_keep: float) -> list[tuple[float, float]]:
    """Complement of silences inside [start,end] with padding -> segments to keep."""
    keep, cur = [], start
    for s, e in silences:
        s2, e2 = max(s, start), min(e, end)
        if e2 <= s2:
            continue
        seg_end = min(s2 + padding, end)
        if seg_end - cur >= min_keep:
            keep.append((round(cur, 3), round(seg_end, 3)))
        cur = max(cur, e2 - padding)
    if end - cur >= min_keep:
        keep.append((round(cur, 3), round(end, 3)))
    # merge overlaps created by padding
    merged: list[tuple[float, float]] = []
    for s, e in keep:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(e, merged[-1][1]))
        else:
            merged.append((s, e))
    return merged
