"""CAPTION AGENT: Hindi/Haryanvi transcription (Faster-Whisper) + animated ASS captions.

Sources (job.captions.source):
  auto    -> try Whisper; if unavailable use script file; else skip
  whisper -> Faster-Whisper only (fails if model cannot load)
  script  -> plain text script timed across detected speech
  srt     -> existing .srt file
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from . import ff
from .config import ROOT, hex_to_ass, safe_path


def transcribe(media: Path, cfg: dict, language: str = "hi", dialect: str | None = None, log=None) -> list[dict]:
    """Word level transcription. Model download needs huggingface.co (or a local model dir)."""
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as e:
        raise RuntimeError("faster-whisper install nahi hai: pip install -r pipeline/requirements.txt") from e
    tc = cfg["transcription"]
    model_name = os.environ.get("DMW_WHISPER_MODEL") or tc["model"]
    local = ROOT / tc["local_model_dir"] / model_name
    model_ref = str(local) if (local / "model.bin").exists() else model_name
    if log:
        log.say(f"  [Caption] Faster-Whisper model '{model_ref}' load ho raha hai...")
    model = WhisperModel(model_ref, device="cpu", compute_type=tc["compute_type"],
                         download_root=str(ROOT / tc["local_model_dir"]))
    prompt = tc["haryanvi_prompt"] if dialect == "haryanvi" else None
    segments, _ = model.transcribe(str(media), language=language, word_timestamps=True, vad_filter=True,
                                   beam_size=tc["beam_size"], initial_prompt=prompt)
    words = []
    for seg in segments:
        for w in seg.words or []:
            t = w.word.strip()
            if t:
                words.append({"text": t, "start": float(w.start), "end": float(w.end)})
    return words


def words_from_script(text: str, speech: list[tuple[float, float]]) -> list[dict]:
    """Distribute script words over speech intervals proportional to word length."""
    tokens = text.split()
    if not tokens or not speech:
        return []
    total = sum(e - s for s, e in speech)
    weights = [max(len(t), 2) for t in tokens]
    wsum = sum(weights)
    words, ti = [], 0
    for s, e in speech:
        span = e - s
        share = round(len(tokens) * span / total) if total else 0
        chunk = tokens[ti: ti + share] if (s, e) != speech[-1] else tokens[ti:]
        cw = weights[ti: ti + len(chunk)]
        ti += len(chunk)
        t, csum = s, sum(cw) or 1
        for tok, w in zip(chunk, cw):
            d = span * w / csum
            words.append({"text": tok, "start": round(t, 3), "end": round(t + d, 3)})
            t += d
    _ = wsum
    return words


def words_from_srt(path: Path) -> list[dict]:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    out = []
    pat = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)\s*\n(.+?)(?:\n\s*\n|\Z)", re.S)
    for m in pat.finditer(txt):
        g = list(map(int, m.groups()[:8]))
        s = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        e = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        toks = re.sub(r"<[^>]+>", "", m.group(9)).split()
        for i, t in enumerate(toks):
            out.append({"text": t, "start": s + (e - s) * i / len(toks), "end": s + (e - s) * (i + 1) / len(toks),
                        "eol": i == len(toks) - 1})
    return out


def chunk_words(words: list[dict], max_words: int) -> list[list[dict]]:
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or w["start"] - cur[-1]["end"] > 0.6):
            chunks.append(cur)
            cur = []
        cur.append(w)
        if w.get("eol") or re.search(r"[.!?।,]$", w["text"]):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def _ts(t: float) -> str:
    t = max(t, 0)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _esc(t: str) -> str:
    return t.replace("\\", "").replace("{", "(").replace("}", ")")


def write_ass(words: list[dict], job: dict, cfg: dict, out: Path, offset: float = 0.0) -> int:
    """Animated 'active word' captions: chunk pops in, current word highlighted gold + bigger."""
    c = cfg["captions"]
    W, H = job["width"], job["height"]
    vertical = H > W
    size = int((W if vertical else H) * (0.115 if vertical else 0.1))
    margin_v = int(H * (0.22 if vertical else 0.08))
    hl = hex_to_ass(c["highlight"])
    maxw = c["max_words_vertical"] if vertical else c["max_words_horizontal"]
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: DMW,{c['font']},{size},{hex_to_ass(c['color'])},{hl},{hex_to_ass(c['outline'])},&H96000000,-1,0,0,0,100,100,0,0,1,{max(3, size//14)},{max(2, size//24)},2,{int(W*0.06)},{int(W*0.06)},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for ch in chunk_words(words, maxw):
        cs, ce = ch[0]["start"] + offset, ch[-1]["end"] + offset
        for j, w in enumerate(ch):
            ws = cs if j == 0 else w["start"] + offset
            we = (ch[j + 1]["start"] + offset) if j + 1 < len(ch) else ce
            if we - ws < 0.04:
                continue
            parts = []
            for k, x in enumerate(ch):
                t = _esc(x["text"])
                parts.append(f"{{\\c{hl}\\fscx112\\fscy112}}{t}{{\\r}}" if k == j else t)
            anim = "{\\fad(60,0)\\fscx70\\fscy70\\t(0,140,\\fscx100\\fscy100)}" if j == 0 else ""
            lines.append(f"Dialogue: 0,{_ts(ws)},{_ts(we)},DMW,,0,0,0,,{anim}{' '.join(parts)}")
    out.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def build_captions(merged: Path, job: dict, cfg: dict, work: Path, speech_window: tuple[float, float], log) -> Path | None:
    cap = job["captions"]
    if not cap.get("enabled") or cap.get("source") == "none":
        return None
    words: list[dict] = []
    src = cap.get("source", "auto")
    if src in ("auto", "whisper"):
        try:
            words = transcribe(merged, cfg, cap.get("language", "hi"), cap.get("dialect"), log)
            log.say(f"  [Caption] Whisper ne {len(words)} words pakde")
        except Exception as e:  # noqa: BLE001 - network/model errors are expected in sandbox
            if src == "whisper":
                raise
            log.say(f"  [Caption] Whisper available nahi ({type(e).__name__}): script/SRT fallback")
    if not words and cap.get("srt"):
        words = words_from_srt(safe_path(cap["srt"], "text"))
    if not words and (cap.get("script") or cap.get("text")):
        text = cap.get("text") or safe_path(cap["script"], "text").read_text(encoding="utf-8")
        sc = cfg["silence"]
        a, b = speech_window
        if job.get("voiceover"):  # narration comes from VO tracks -> time captions to them
            speech = []
            for vo in job["voiceover"]:
                p = safe_path(vo["src"], "audio")
                at = float(vo.get("at", 0))
                vsil = ff.detect_silence(p, sc["noise_db"], 0.35, log)
                speech += [(at + s0, at + e0) for s0, e0 in
                           ff.speech_intervals(0, ff.media_info(p)["duration"], vsil, 0.0, 0.25)]
        else:
            sil = ff.detect_silence(merged, sc["noise_db"], 0.35, log)
            speech = ff.speech_intervals(a, b, sil, 0.0, 0.25)
        speech = speech or [(a, b)]
        words = words_from_script(text, speech)
        log.say(f"  [Caption] Script se {len(words)} words ko {len(speech)} speech parts me time kiya")
    if not words:
        log.say("  [Caption] Koi caption source nahi mila - captions skip")
        return None
    words = [w for w in words if w["start"] >= speech_window[0] - 0.05 and w["end"] <= speech_window[1] + 0.3]
    out = work / "captions.ass"
    n = write_ass(words, job, cfg, out)
    log.say(f"  [Caption] {n} animated caption events banaye")
    return out
