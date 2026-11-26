#!/usr/bin/env python3
"""DESI MINING WALA Video Studio - command line.

  python pipeline/studio.py doctor                 # tools check
  python pipeline/studio.py probe <file>           # duration/resolution/codec
  python pipeline/studio.py plan jobs/my.json      # editing plan preview
  python pipeline/studio.py render jobs/my.json    # full render -> output/<id>/<id>.mp4
  python pipeline/studio.py demo [--aspect 9:16]   # generate demo assets + render
  python pipeline/studio.py transcribe <file>      # Hindi/Haryanvi -> SRT (needs Whisper model)
  python pipeline/studio.py manifest               # list assets for the dashboard
  Agent tools: assets | storyboard | sfx | music-bed | voiceover | track | shift-audio |
               qc | export | grade-preview | still | merge-audio   (see workflow/TOOLS.md)
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dmw import captions, ff  # noqa: E402
from dmw.config import ALLOWED_MEDIA, ROOT, load_config, safe_path  # noqa: E402
from dmw.planner import build_plan, normalize_job  # noqa: E402


def cmd_doctor(_):
    ok = True
    for tool, args in [("ffmpeg", ["-version"]), ("ffprobe", ["-version"]), ("node", ["--version"]), ("npx", ["--version"])]:
        path = shutil.which(tool)
        ver = subprocess.run([tool, *args], capture_output=True, text=True).stdout.splitlines()[0] if path else "-"
        print(f"{'OK ' if path else 'MISSING'} {tool:8} {ver}")
        ok &= bool(path)
    rem = (ROOT / "remotion" / "node_modules" / "remotion").exists()
    print(f"{'OK ' if rem else 'MISSING'} remotion  (cd remotion && npm ci)")
    try:
        import faster_whisper  # noqa: F401
        print(f"OK  faster-whisper {faster_whisper.__version__}")
    except ImportError:
        print("MISSING faster-whisper (pip install -r pipeline/requirements.txt)")
    from dmw.motion import find_browser
    print(f"INFO browser for Remotion: {find_browser(load_config()) or 'Remotion auto-download'}")
    return 0 if ok else 1


def cmd_probe(a):
    print(json.dumps(ff.media_info(Path(a.file)), indent=2))


def cmd_plan(a):
    job = json.loads(Path(a.job).read_text(encoding="utf-8"))
    job.setdefault("id", Path(a.job).stem)
    print(json.dumps(build_plan(normalize_job(job)), indent=2, ensure_ascii=False))


def cmd_render(a):
    from dmw.render import render_job
    rep = render_job(Path(a.job), keep_work=a.keep_work)
    print(json.dumps({"file": rep["file"], "passed": rep["passed"], "checks": rep["checks"]}, indent=2))
    return 0 if rep["passed"] else 2


def cmd_demo(a):
    from dmw.demo import write_demo_job
    from dmw.render import render_job
    path = write_demo_job(a.aspect)
    print(f"Demo job: {path.relative_to(ROOT)}")
    if a.assets_only:
        return 0
    rep = render_job(path, keep_work=a.keep_work)
    print(json.dumps({"file": rep["file"], "passed": rep["passed"], "checks": rep["checks"]}, indent=2))
    return 0 if rep["passed"] else 2


def cmd_transcribe(a):
    cfg = load_config()
    words = captions.transcribe(Path(a.file), cfg, a.language, a.dialect)
    chunks = captions.chunk_words(words, 7)
    out = Path(a.out or Path(a.file).with_suffix(".srt"))

    def ts(t):
        h, r = divmod(t, 3600); m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    lines = [f"{i}\n{ts(c[0]['start'])} --> {ts(c[-1]['end'])}\n{' '.join(w['text'] for w in c)}\n" for i, c in enumerate(chunks, 1)]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"SRT saved: {out}")


def cmd_manifest(_):
    assets = ROOT / "assets"
    kinds = {"raw-videos": "video", "photos": "image", "logos": "image", "music": "audio", "sfx": "audio", "scripts": "text", "luts": "lut"}
    man = {}
    for folder, kind in kinds.items():
        d = assets / folder
        man[folder] = sorted(str(p.relative_to(ROOT)) for p in d.rglob("*") if p.suffix.lower() in ALLOWED_MEDIA[kind]) if d.exists() else []
    (assets / "manifest.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    print(json.dumps(man, indent=2))


def _p(x):
    return Path(x) if Path(x).is_absolute() else ROOT / x


def _show(d):
    print(json.dumps(d, indent=2, ensure_ascii=False))


def cmd_storyboard(a):
    from dmw import tools
    _show(tools.storyboard(Path(a.job), _p(a.out) if a.out else None))


def cmd_sfx(a):
    from dmw import tools
    _show(tools.sfx(a.kind, _p(a.out) if a.out else None))


def cmd_music_bed(a):
    from dmw import tools
    _show(tools.music_bed(a.mood, a.duration, _p(a.out) if a.out else None))


def cmd_voiceover(a):
    from dmw import tools
    text = Path(a.text_file).read_text(encoding="utf-8") if a.text_file else a.text
    _show(tools.voiceover(text, _p(a.out), a.lang, a.speed))


def cmd_track(a):
    from dmw import tools
    _show(tools.track(_p(a.video), _p(a.out), a.mode, a.sample_fps, a.reframe, _p(a.reframe_out) if a.reframe_out else None))


def cmd_shift_audio(a):
    from dmw import tools
    _show(tools.shift_audio(_p(a.video), a.ms, _p(a.out)))


def cmd_qc(a):
    from dmw import tools
    rep = tools.qc_deep(_p(a.mp4), _p(a.out_dir))
    _show({k: rep[k] for k in ("file", "status", "loudness_lufs", "warnings", "checks", "contact_sheet")})
    return 0 if rep["status"] != "FAIL" else 2


def cmd_export(a):
    from dmw import tools
    _show(tools.export(_p(a.mp4), a.presets.split(","), _p(a.out_dir)))


def cmd_grade_preview(a):
    from dmw import tools
    _show(tools.grade_preview(_p(a.video), a.grades.split(","), _p(a.out), a.t))


def cmd_still(a):
    from dmw import tools
    props = json.loads(Path(a.props).read_text(encoding="utf-8")) if a.props.endswith(".json") else json.loads(a.props)
    _show(tools.still(a.comp, props, _p(a.out)))


def cmd_merge_audio(a):
    from dmw import tools
    _show(tools.merge_audio(_p(a.prod_dir)))


def cmd_assets(_):
    from dmw import tools
    _show(tools.asset_scan())


def main():
    ap = argparse.ArgumentParser(description="DESI MINING WALA Video Studio")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor").set_defaults(fn=cmd_doctor)
    p = sub.add_parser("probe"); p.add_argument("file"); p.set_defaults(fn=cmd_probe)
    p = sub.add_parser("plan"); p.add_argument("job"); p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("render"); p.add_argument("job"); p.add_argument("--keep-work", action="store_true"); p.set_defaults(fn=cmd_render)
    p = sub.add_parser("demo"); p.add_argument("--aspect", default="9:16"); p.add_argument("--assets-only", action="store_true"); p.add_argument("--keep-work", action="store_true"); p.set_defaults(fn=cmd_demo)
    p = sub.add_parser("transcribe"); p.add_argument("file"); p.add_argument("--language", default="hi")
    p.add_argument("--dialect", default="haryanvi"); p.add_argument("--out"); p.set_defaults(fn=cmd_transcribe)
    sub.add_parser("manifest").set_defaults(fn=cmd_manifest)
    sub.add_parser("assets", help="asset manifest + duplicates").set_defaults(fn=cmd_assets)
    p = sub.add_parser("storyboard"); p.add_argument("job"); p.add_argument("--out"); p.set_defaults(fn=cmd_storyboard)
    p = sub.add_parser("sfx"); p.add_argument("kind"); p.add_argument("--out"); p.set_defaults(fn=cmd_sfx)
    p = sub.add_parser("music-bed"); p.add_argument("--mood", default="desi"); p.add_argument("--duration", type=float, default=30)
    p.add_argument("--out"); p.set_defaults(fn=cmd_music_bed)
    p = sub.add_parser("voiceover"); p.add_argument("--text"); p.add_argument("--text-file"); p.add_argument("--out", required=True)
    p.add_argument("--lang", default="hi"); p.add_argument("--speed", type=int, default=145); p.set_defaults(fn=cmd_voiceover)
    p = sub.add_parser("track"); p.add_argument("video"); p.add_argument("--out", required=True)
    p.add_argument("--mode", default="auto", choices=["auto", "face", "motion"]); p.add_argument("--sample-fps", type=float, default=5)
    p.add_argument("--reframe", help="e.g. 9:16"); p.add_argument("--reframe-out"); p.set_defaults(fn=cmd_track)
    p = sub.add_parser("shift-audio"); p.add_argument("video"); p.add_argument("--ms", type=int, required=True)
    p.add_argument("--out", required=True); p.set_defaults(fn=cmd_shift_audio)
    p = sub.add_parser("qc"); p.add_argument("mp4"); p.add_argument("--out-dir", required=True); p.set_defaults(fn=cmd_qc)
    p = sub.add_parser("export"); p.add_argument("mp4"); p.add_argument("--presets", default="master,reels,whatsapp")
    p.add_argument("--out-dir", required=True); p.set_defaults(fn=cmd_export)
    p = sub.add_parser("grade-preview"); p.add_argument("video"); p.add_argument("--grades", default="natural,earthy-mining,teal-orange,vibrant,bw,documentary")
    p.add_argument("--out", required=True); p.add_argument("--t", type=float); p.set_defaults(fn=cmd_grade_preview)
    p = sub.add_parser("merge-audio"); p.add_argument("prod_dir"); p.set_defaults(fn=cmd_merge_audio)
    p = sub.add_parser("still"); p.add_argument("comp"); p.add_argument("--props", default="{}"); p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_still)
    a = ap.parse_args()
    try:
        sys.exit(a.fn(a) or 0)
    except Exception as e:  # noqa: BLE001
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
