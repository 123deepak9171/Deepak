"""PLANNER AGENT: turns a job (media + Hinglish instructions) into a concrete edit plan.

Rule based (offline, free, no API credits). Claude Code can also write the job JSON
directly - see .claude/skills/dmw-video-editor/SKILL.md.
"""
from __future__ import annotations

import copy
import re

from .config import JobError, load_config, safe_path

KEYWORDS = {
    "aspect_9_16": r"\b(reel|reels|short|shorts|vertical|insta|instagram|9:16|story|status)\b",
    "aspect_16_9": r"\b(youtube|horizontal|landscape|16:9|long video)\b",
    "aspect_1_1": r"\b(square|1:1)\b",
    "silence": r"(silence|khamoshi|chup|pause|gap|faltu|dead air)",
    "captions": r"(caption|subtitle|text|likh|shabd)",
    "no_captions": r"(no caption|bina caption|caption mat|without caption)",
    "music": r"(music|gaana|gana|bgm|background score|beat)",
    "no_music": r"(no music|bina music|music mat|without music)",
    "product": r"(product|launch|naya maal|new machine|reveal)",
    "logo": r"(logo|brand|intro)",
    "zoom": r"(zoom|push in|punch)",
    "greenscreen": r"(green ?screen|chroma|background badlo|background change)",
    "bw": r"(black ?(and|&|n) ?white|b&w|purana look)",
    "cinematic": r"(cinematic|filmy|movie|film look)",
    "energetic": r"(energetic|fast|josh|tez|dhamaka|viral)",
    "minimal": r"(minimal|simple|saaf|clean)",
    "documentary": r"(documentary|news|report|explain)",
}


def _has(key: str, text: str) -> bool:
    return re.search(KEYWORDS[key], text, re.I) is not None


def parse_duration(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*(min|minute|minat|मिनट)", text, re.I)
    if m:
        return float(m.group(1)) * 60
    m = re.search(r"(\d+(?:\.\d+)?)\s*(s|sec|second|seconds|second ka|सेकंड)\b", text, re.I)
    if m:
        return float(m.group(1))
    return None


def apply_instructions(job: dict) -> list[str]:
    """Mutates job according to free-text instructions. Returns notes of what changed."""
    text = (job.get("instructions") or "").lower()
    notes = []
    if not text:
        return notes
    if "aspect" not in job.get("_explicit", []):
        if _has("aspect_9_16", text):
            job["aspect"] = "9:16"; notes.append("Instruction se vertical 9:16 format chuna")
        elif _has("aspect_1_1", text):
            job["aspect"] = "1:1"; notes.append("Square 1:1 format chuna")
        elif _has("aspect_16_9", text):
            job["aspect"] = "16:9"; notes.append("YouTube 16:9 format chuna")
    if "style" not in job.get("_explicit", []):
        for st in ("cinematic", "energetic", "minimal", "documentary"):
            if _has(st, text):
                job["style"] = st; notes.append(f"Style '{st}' chuna"); break
    d = parse_duration(text)
    if d and "target_duration" not in job.get("_explicit", []):
        job["target_duration"] = d; notes.append(f"Duration {d:g}s set ki")
    if _has("silence", text):
        job["remove_silence"] = True; notes.append("Silence removal ON")
    if _has("no_captions", text):
        job.setdefault("captions", {})["enabled"] = False
    elif _has("captions", text):
        job.setdefault("captions", {})["enabled"] = True; notes.append("Animated captions ON")
    if _has("no_music", text):
        job.setdefault("music", {})["enabled"] = False
    if _has("zoom", text):
        job["zoom"] = True
    if _has("bw", text):
        job["grade"] = "bw"; notes.append("Black & white grade")
    if _has("product", text) and not job.get("product_reveal"):
        job["product_reveal"] = {"enabled": True, "title": job.get("title", "NEW PRODUCT"), "subtitle": ""}
        notes.append("Product reveal scene add kiya")
    return notes


def normalize_job(raw: dict) -> dict:
    """Fill defaults from config + style + instructions. Returns a fully resolved job."""
    cfg = load_config()
    job = copy.deepcopy(raw)
    job["_explicit"] = [k for k in ("aspect", "style", "target_duration") if k in raw]
    d = cfg["defaults"]
    job.setdefault("id", "job")
    job.setdefault("title", job["id"])
    job.setdefault("aspect", d["aspect"])
    job.setdefault("style", d["style"])
    job.setdefault("target_duration", d["target_duration"])
    job.setdefault("fps", d["fps"])
    job.setdefault("fit_mode", d["fit_mode"])
    job.setdefault("remove_silence", True)
    job["notes"] = apply_instructions(job)

    if job["style"] not in cfg["styles"]:
        raise JobError(f"Unknown style: {job['style']} (options: {', '.join(cfg['styles'])})")
    if job["aspect"] not in cfg["resolutions"]:
        raise JobError(f"Unknown aspect: {job['aspect']}")
    style = cfg["styles"][job["style"]]
    job["width"], job["height"] = cfg["resolutions"][job["aspect"]]
    job.setdefault("grade", style["grade"])
    job.setdefault("lut", None)
    job.setdefault("zoom", bool(style["zoom"]))
    job["zoom_strength"] = style["zoom"] or 1.06
    job.setdefault("punch_in", style["punch_in"])
    tr = job.setdefault("transitions", {})
    tr.setdefault("types", style["transitions"])
    tr.setdefault("duration", style["transition_duration"])
    if float(job["target_duration"]) > cfg["limits"]["max_target_duration"]:
        raise JobError("target_duration limit se zyada hai")

    brand = cfg["brand"]
    logo = job.setdefault("logo", {})
    logo.setdefault("src", brand["default_logo"])
    logo.setdefault("intro", True)
    logo.setdefault("outro", True)
    logo.setdefault("watermark", True)
    logo.setdefault("intro_duration", 3.0)
    logo.setdefault("outro_duration", 3.0)
    if logo["src"] and not safe_path(logo["src"], "image", must_exist=False).exists():
        logo["src"] = None  # no logo file yet -> text based logo animation

    cap = job.setdefault("captions", {})
    cap.setdefault("enabled", True)
    cap.setdefault("source", "auto")  # auto | whisper | script | srt | none
    cap.setdefault("language", cfg["transcription"]["language"])
    cap.setdefault("dialect", "haryanvi")

    music = job.setdefault("music", {})
    music.setdefault("enabled", bool(music.get("src")))
    music.setdefault("volume", style["music_volume"])
    music.setdefault("duck", cfg["audio"]["duck_music"])
    job.setdefault("sfx", [])
    job.setdefault("auto_whoosh", cfg["audio"]["auto_whoosh"])

    pr = job.get("product_reveal") or {}
    if pr.get("enabled"):
        pr.setdefault("title", job["title"])
        pr.setdefault("subtitle", "")
        pr.setdefault("image", None)
        pr.setdefault("price", "")
        pr.setdefault("duration", 4.0)
        pr.setdefault("position", "start")  # start | end
    job["product_reveal"] = pr

    exp = job.setdefault("export", {})
    exp.setdefault("crf", d["crf"])
    exp.setdefault("preset", d["x264_preset"])
    exp.setdefault("audio_bitrate", d["audio_bitrate"])

    # Timeline: explicit list, or built from clips + images
    if not job.get("timeline"):
        tl = [{"type": "video", **c} for c in job.get("clips", [])]
        tl += [{"type": "image", **i} for i in job.get("images", [])]
        job["timeline"] = tl
    if not job["timeline"]:
        raise JobError("Timeline khali hai: kam se kam ek video ya photo do")
    if len(job["timeline"]) > cfg["limits"]["max_timeline_items"]:
        raise JobError("Timeline items limit se zyada hain")
    for it in job["timeline"]:
        if it["type"] == "video":
            safe_path(it["src"], "video")
            if it.get("greenscreen"):
                g = it["greenscreen"]
                g.setdefault("color", "0x00FF00")
                g.setdefault("similarity", 0.18)
                g.setdefault("blend", 0.08)
                if g.get("background"):
                    safe_path(g["background"])
        elif it["type"] == "image":
            safe_path(it["src"], "image")
            it.setdefault("duration", 3.0)
        elif it["type"] == "title":
            it.setdefault("duration", 2.5)
        else:
            raise JobError(f"Unknown timeline type: {it['type']}")
    if music.get("enabled") and music.get("src"):
        safe_path(music["src"], "audio")
    for s in job["sfx"]:
        safe_path(s["src"], "audio")
    if cap.get("script"):
        safe_path(cap["script"], "text")
    if job.get("lut"):
        safe_path(job["lut"], "lut")
    return job


def build_plan(job: dict) -> dict:
    """Human readable plan (Hinglish) + machine steps."""
    steps = []
    if job["logo"]["intro"]:
        steps.append(f"Intro: Remotion logo animation ({job['logo']['intro_duration']}s)")
    if job["product_reveal"].get("enabled") and job["product_reveal"]["position"] == "start":
        steps.append(f"Product reveal: '{job['product_reveal']['title']}' (Remotion)")
    for i, it in enumerate(job["timeline"], 1):
        if it["type"] == "video":
            extra = []
            if job["remove_silence"]:
                extra.append("silence cut")
            if it.get("greenscreen"):
                extra.append("green screen replace")
            if job["punch_in"]:
                extra.append("jump-cut punch-in zoom")
            if job["zoom"]:
                extra.append("slow camera push-in")
            steps.append(f"Clip {i}: {it['src']} -> {', '.join(extra) or 'as-is'}")
        elif it["type"] == "image":
            steps.append(f"Photo {i}: {it['src']} -> Ken Burns animation {it['duration']}s")
        else:
            steps.append(f"Title card {i}: '{it.get('title', '')}'")
    if job["product_reveal"].get("enabled") and job["product_reveal"]["position"] == "end":
        steps.append(f"Product reveal: '{job['product_reveal']['title']}' (Remotion)")
    if job["logo"]["outro"]:
        steps.append("Outro: logo + Subscribe CTA (Remotion)")
    steps.append(f"Transitions: {', '.join(job['transitions']['types'])} ({job['transitions']['duration']}s)")
    steps.append(f"Color grade: {job['grade']}" + (f" + LUT {job['lut']}" if job.get("lut") else ""))
    if job["captions"]["enabled"]:
        steps.append(f"Animated captions: source={job['captions']['source']} lang={job['captions']['language']}")
    if job["music"].get("enabled"):
        steps.append(f"Background music: {job['music'].get('src')} vol={job['music']['volume']} duck={job['music']['duck']}")
    if job["sfx"] or job["auto_whoosh"]:
        steps.append("Sound effects: transitions par whoosh + custom SFX")
    if job["logo"]["watermark"]:
        steps.append("Logo watermark (top-right)")
    steps.append(f"Export: {job['width']}x{job['height']} {job['fps']}fps H.264 + AAC, loudness {load_config()['audio']['loudness_lufs']} LUFS, max ~{job['target_duration']}s")
    return {"id": job["id"], "title": job["title"], "aspect": job["aspect"], "style": job["style"],
            "notes": job.get("notes", []), "steps": steps}
