"""आपकी पुरानी Instagram वीडियो देखकर एनालाइज़ करो → कैरेक्टर/स्टाइल अपडेट करो।

    1. अपनी वीडियो (mp4) `my_videos/` फ़ोल्डर में डालो
       (Instagram → Settings → Your activity → Download your information → Media)
    2. pip install faster-whisper     (फ्री, आपके कंप्यूटर/GitHub पर ही चलता है)
    3. python -m agent.analyze

आउटपुट: analysis/report.md, analysis/frames/*.jpg, और config/learned_style.json
(आपका सीखा हुआ स्टाइल) बनता है — जिसे स्क्रिप्ट-राइटर हर दिन पढ़ता है।
GEMINI_API_KEY हो तो Gemini वीडियो के फ्रेम + बातें देखकर आपके स्टाइल का सार भी लिखता है।
"""
import base64
import collections
import json
import os
import re
import subprocess
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
VID_DIR, OUT = ROOT / "my_videos", ROOT / "analysis"
STOP = set("है हैं का की के को में से और तो भी ये वो यह वह था थी नहीं हो कर एक पर ना न जो कि तुम मैं हम आप भाई "
           "ही तक लिए अब क्या बस the a to and is of".split())


def duration(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def frames(p, d, n=3):
    paths = []
    for i in range(n):
        f = OUT / "frames" / f"{p.stem}_{i}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(d * (i + 0.5) / n), "-i", str(p),
                        "-frames:v", "1", "-vf", "scale=360:-1", str(f)])
        if f.exists():
            paths.append(f)
    return paths


def transcribe(p, model):
    if model is None:
        return ""
    segs, _ = model.transcribe(str(p), language="hi", vad_filter=True)
    return " ".join(s.text.strip() for s in segs)


def gemini_summary(items, key):
    parts = [{"text": "ये एक इंस्टाग्राम पेज (बिटकॉइन माइनिंग मशीन बेचने वाला, देसी अंदाज़) की वीडियो हैं। "
                      "हर वीडियो के फ्रेम और बोली गई बातें दी हैं। हिंदी में JSON लौटाओ: "
                      '{"look": "", "speaking_style": "", "common_topics": [], "best_hooks": [], '
                      '"catchphrases": [], "what_works": "", "ideas_for_new_comedy": []}'}]
    for it in items[:15]:
        parts.append({"text": f"\nवीडियो {it['file']} ({it['duration']}s): {it['transcript'][:800]}"})
        for f in it["frames"][:2]:
            parts.append({"inline_data": {"mime_type": "image/jpeg",
                                          "data": base64.b64encode(Path(f).read_bytes()).decode()}})
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                      params={"key": key}, timeout=180,
                      json={"contents": [{"parts": parts}], "generationConfig": {"responseMimeType": "application/json"}})
    r.raise_for_status()
    return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])


def main():
    vids = sorted([p for p in VID_DIR.glob("**/*") if p.suffix.lower() in (".mp4", ".mov", ".mkv", ".webm")])
    if not vids:
        print(f"कोई वीडियो नहीं मिली। अपनी रील्स {VID_DIR} में डालो और फिर चलाओ।")
        return
    (OUT / "frames").mkdir(parents=True, exist_ok=True)
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(os.getenv("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")
    except Exception as e:  # noqa: BLE001
        print(f"[analyze] faster-whisper नहीं मिला ({e}) — सिर्फ़ फ्रेम/लंबाई एनालाइज़ होगी")
        model = None
    items = []
    for v in vids:
        d = duration(v)
        print(f"[analyze] {v.name} ({d:.0f}s)")
        items.append({"file": v.name, "duration": round(d, 1), "frames": [str(f) for f in frames(v, d)],
                      "transcript": transcribe(v, model)})
    words = collections.Counter(w for it in items for w in re.findall(r"[\wऀ-ॿ]+", it["transcript"].lower())
                                if w not in STOP and len(w) > 2)
    learned = {
        "videos_analyzed": len(items),
        "avg_length_seconds": round(sum(i["duration"] for i in items) / len(items), 1),
        "top_words": [w for w, _ in words.most_common(25)],
        "sample_openings": [i["transcript"][:90] for i in items if i["transcript"]][:8],
    }
    key = os.getenv("GEMINI_API_KEY")
    if key:
        try:
            learned["ai_style_summary"] = gemini_summary(items, key)
        except Exception as e:  # noqa: BLE001
            print(f"[analyze] Gemini सार नहीं बना: {e}")
    (ROOT / "config" / "learned_style.json").write_text(json.dumps(learned, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["# मेरी वीडियो का एनालिसिस\n", f"- कुल वीडियो: {len(items)}",
          f"- औसत लंबाई: {learned['avg_length_seconds']} सेकंड",
          f"- सबसे ज़्यादा बोले गए शब्द: {', '.join(learned['top_words'])}\n"]
    if "ai_style_summary" in learned:
        md += ["## AI स्टाइल सार", "```json", json.dumps(learned["ai_style_summary"], ensure_ascii=False, indent=2), "```\n"]
    md.append("## हर वीडियो")
    for it in items:
        md += [f"### {it['file']} ({it['duration']}s)", it["transcript"] or "_(ट्रांसक्रिप्ट नहीं)_",
               " ".join(f"![]({Path(f).relative_to(OUT)})" for f in it["frames"]), ""]
    (OUT / "report.md").write_text("\n".join(md), encoding="utf-8")
    print(f"[analyze] हो गया → {OUT/'report.md'} और config/learned_style.json")


if __name__ == "__main__":
    main()
