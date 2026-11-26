"""ORCHESTRATOR + SOUND + QA AGENTS: runs the full safe render workflow for one job."""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

from . import captions, editor, ff, motion, remote
from .config import ROOT, check_disk, load_config, rel, safe_path, slug
from .planner import build_plan, normalize_job


class RenderLock:
    """Prevents two renders of the same job writing the same files."""

    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
        except FileExistsError as e:
            raise ff.FFError(f"Ye job pehle se render ho raha hai (lock: {rel(self.path)}). "
                             "Agar koi render nahi chal raha to lock file delete karo.") from e
        return self

    def __exit__(self, *a):
        self.path.unlink(missing_ok=True)


def final_mix(merged: Path, dur: float, ass: Path | None, job: dict, cfg: dict, intro_end: float,
              outro_start: float, whoosh_times: list[float], out: Path, work: Path, log) -> Path:
    """Captions burn + logo watermark + voice cleanup + music ducking + SFX + loudness + H.264 export."""
    W, H, fps = job["width"], job["height"], job["fps"]
    args = ["-i", merged]
    fg, n = [], 1
    vlast = "0:v"
    if ass:
        fonts = str(ROOT / cfg["paths"]["fonts"]).replace(":", r"\:")
        fg.append(f"[0:v]subtitles=filename={ass.name}:fontsdir='{fonts}'[vsub]")
        vlast = "vsub"
    logo = job["logo"]
    if logo.get("watermark") and logo.get("src"):
        args += ["-i", safe_path(logo["src"], "image")]
        lw = int(min(W, H) * 0.14) // 2 * 2
        m = int(min(W, H) * 0.035)
        fg.append(f"[{n}:v]scale={lw}:-1,format=rgba,colorchannelmixer=aa=0.85[lg]")
        fg.append(f"[{vlast}][lg]overlay=x=W-w-{m}:y={m}:enable='between(t,{intro_end:.2f},{outro_start:.2f})'[vwm]")
        vlast, n = "vwm", n + 1
    fg.append(f"[{vlast}]fps={fps},format=yuv420p[vout]")

    ac = cfg["audio"]
    fg.append(f"[0:a]highpass=f=70,acompressor=threshold=0.125:ratio=3:attack=10:release=200,volume={ac['voice_gain']}[voice0]")
    mix = []
    music = job["music"]
    use_music = music.get("enabled") and music.get("src")
    if use_music and music.get("duck"):
        fg.append("[voice0]asplit=2[voice][sc]")
    else:
        fg.append("[voice0]anull[voice]")
    mix.append("[voice]")
    if use_music:
        args += ["-stream_loop", "-1", "-i", safe_path(music["src"], "audio")]
        fg.append(f"[{n}:a]atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
                  f"volume={music['volume']},afade=t=in:d=1.5,afade=t=out:st={max(dur-2.5,0):.2f}:d=2.5[m0]")
        if music.get("duck"):
            fg.append("[m0][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[mus]")
        else:
            fg.append("[m0]anull[mus]")
        mix.append("[mus]")
        n += 1
    sfx = list(job["sfx"])
    whoosh = ROOT / ac["default_whoosh"]
    if job.get("auto_whoosh") and whoosh.exists():
        sfx += [{"src": rel(whoosh), "at": max(t - 0.15, 0), "volume": 0.5} for t in whoosh_times]
    for i, s in enumerate(sfx):
        args += ["-i", safe_path(s["src"], "audio")]
        ms = int(float(s.get("at", 0)) * 1000)
        fg.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,volume={s.get('volume', 0.6)},adelay={ms}:all=1[sfx{i}]")
        mix.append(f"[sfx{i}]")
        n += 1
    if len(mix) > 1:
        fg.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first:dropout_transition=0[amx]")
    else:
        fg.append(f"{mix[0]}anull[amx]")
    fg.append(f"[amx]loudnorm=I={ac['loudness_lufs']}:TP={ac['true_peak']}:LRA=11,aresample=48000,"
              f"afade=t=out:st={max(dur-0.5,0):.2f}:d=0.5[aout]")

    exp = job["export"]
    tmp = out.with_name(out.stem + ".partial.mp4")
    log.say(f"  [Sound] voice cleanup, music={'ON' if use_music else 'OFF'}, sfx={len(sfx)}, loudness {ac['loudness_lufs']} LUFS")
    ff.ffmpeg([*args, "-filter_complex", ";".join(fg), "-map", "[vout]", "-map", "[aout]",
               "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", exp["preset"], "-crf", str(exp["crf"]),
               "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(fps), "-g", str(fps * 2),
               "-c:a", "aac", "-b:a", exp["audio_bitrate"], "-ar", "48000", "-ac", "2",
               "-movflags", "+faststart", "-metadata", f"title={job['title']}",
               "-metadata", "artist=DESI MINING WALA", tmp], log=log, cwd=work,
              timeout=cfg["limits"]["command_timeout_sec"])
    tmp.replace(out)  # atomic: final file only appears when complete
    return out


def qa_check(path: Path, job: dict, expected: float, log) -> dict:
    """QA AGENT: verify codec, resolution, duration, audio and full decode."""
    info = ff.media_info(path)
    decode = ff.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], timeout=1800).strip()
    checks = {
        "video_codec_h264": info["vcodec"] == "h264",
        "pixel_format_yuv420p": info["pix_fmt"] == "yuv420p",
        "resolution_ok": (info["width"], info["height"]) == (job["width"], job["height"]),
        "fps_ok": abs(info["fps"] - job["fps"]) < 0.5,
        "audio_aac": info["acodec"] == "aac",
        "duration_ok": abs(info["duration"] - expected) < 1.0,
        "decodes_without_errors": decode == "",
    }
    report = {"file": rel(path), "info": info, "expected_duration": round(expected, 3),
              "checks": checks, "passed": all(checks.values()), "decode_errors": decode[:2000]}
    log.say(f"  [QA] {'PASS' if report['passed'] else 'FAIL'}: {info['width']}x{info['height']} "
            f"{info['vcodec']}/{info['acodec']} {info['duration']:.2f}s {info['size_bytes']/1e6:.2f}MB")
    return report


def render_job(job_path: Path | dict, keep_work: bool = False, verbose: bool = True) -> dict:
    cfg = load_config()
    raw = job_path if isinstance(job_path, dict) else json.loads(Path(job_path).read_text(encoding="utf-8"))
    raw["id"] = slug(raw.get("id") or Path(str(job_path)).stem)
    remote.resolve_remote(raw)
    job = normalize_job(raw)
    out_dir = ROOT / cfg["paths"]["output"] / job["id"]
    work = out_dir / "work"
    work.mkdir(parents=True, exist_ok=True)
    check_disk(cfg, out_dir)
    log = ff.Logger(out_dir / "render.log", verbose)
    t0 = time.time()
    with RenderLock(out_dir / ".lock"):
        plan = build_plan(job)
        (out_dir / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "job.resolved.json").write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
        log.say(f"[Planner] Job '{job['id']}': {job['width']}x{job['height']} style={job['style']} target={job['target_duration']}s")
        for s in plan["steps"]:
            log.say(f"   - {s}")

        segs: list[tuple[Path, float]] = []
        idx = 0
        intro_dur = outro_dur = 0.0
        if job["logo"]["intro"]:
            p = motion.scene("intro", job, cfg, work, log)
            segs.append(editor.normalize_external(p, idx, "intro", job, work, log)); idx += 1
            intro_dur = segs[-1][1]
        pr = job["product_reveal"]
        if pr.get("enabled") and pr["position"] == "start":
            p = motion.scene("product", job, cfg, work, log)
            segs.append(editor.normalize_external(p, idx, "product", job, work, log)); idx += 1

        reserved = (job["logo"]["outro_duration"] if job["logo"]["outro"] else 0) + \
                   (pr.get("duration", 0) if pr.get("enabled") and pr["position"] == "end" else 0)
        budget = float(job["target_duration"]) - sum(d for _, d in segs) - reserved
        n_tl = len(job["timeline"])
        td = float(job["transitions"]["duration"])
        budget += td * (len(segs) + n_tl + (1 if reserved else 0) - 1)  # overlaps eaten by transitions
        body_start_idx = len(segs)
        for it in job["timeline"]:
            if budget <= 0.5:
                log.say("  [Editor] Target duration poora ho gaya, baaki items skip")
                break
            if it["type"] == "video":
                p, d = editor.render_video_item(it, idx, job, cfg, work, budget, log)
            elif it["type"] == "image":
                it = {**it, "duration": min(float(it["duration"]), budget)}
                p, d = editor.render_image_item(it, idx, job, cfg, work, log)
            else:
                it = {**it, "duration": min(float(it["duration"]), budget)}
                p0 = motion.scene("title", job, cfg, work, log, item=it, n=idx)
                p, d = editor.normalize_external(p0, idx, "title", job, work, log)
            if p:
                segs.append((p, d)); idx += 1; budget -= d
        if len(segs) == body_start_idx:
            raise ff.FFError("Body me koi segment nahi bana (inputs check karo)")
        if pr.get("enabled") and pr["position"] == "end":
            p = motion.scene("product", job, cfg, work, log)
            segs.append(editor.normalize_external(p, idx, "product", job, work, log)); idx += 1
        if job["logo"]["outro"]:
            p = motion.scene("outro", job, cfg, work, log)
            segs.append(editor.normalize_external(p, idx, "outro", job, work, log)); idx += 1
            outro_dur = segs[-1][1]

        merged, ttimes, mdur = editor.merge_segments(segs, job, work, log)
        intro_end = max(intro_dur - td, 0) if intro_dur else 0.0
        outro_start = mdur - outro_dur + (td if outro_dur else 0) if outro_dur else mdur
        ass = captions.build_captions(merged, job, cfg, work, (intro_end, outro_start), log)
        final = out_dir / f"{job['id']}.mp4"
        whoosh = ttimes + ([0.0] if intro_dur else [])
        final_mix(merged, mdur, ass, job, cfg, intro_end, outro_start, whoosh, final, work, log)
        ff.ffmpeg(["-ss", f"{min(intro_dur + 1.0, mdur / 2):.2f}", "-i", final, "-frames:v", "1", "-q:v", "3",
                   out_dir / "thumbnail.jpg"], log=log)
        report = qa_check(final, job, mdur, log)
        report["render_seconds"] = round(time.time() - t0, 1)
        report["plan"] = plan
        (out_dir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        motion.cleanup(job["id"])
        if not keep_work:
            shutil.rmtree(work, ignore_errors=True)
        log.say(f"[Done] {rel(final)} ({report['render_seconds']}s me render hua)")
        log.close()
        return report
