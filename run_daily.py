"""रोज़ चलने वाला एजेंट: स्क्रिप्ट लिखो → आवाज़ → वीडियो → (ऑप्शनल) Telegram/Instagram पर भेजो।

    python run_daily.py              # आज की रील बनाओ
    python run_daily.py --post       # बनाकर पोस्ट/भेज भी दो (secrets चाहिए)
"""
import argparse
import datetime as dt
import json
import shutil
from pathlib import Path

from agent import poster
from agent.render import render
from agent.script_writer import load_yaml, write_script

ROOT = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true", help="Telegram/Instagram पर भेजो")
    ap.add_argument("--script", help="अपनी JSON स्क्रिप्ट फ़ाइल से वीडियो बनाओ")
    args = ap.parse_args()

    char = load_yaml("character.yaml")
    script = json.loads(Path(args.script).read_text(encoding="utf-8")) if args.script else write_script()
    today = dt.date.today().isoformat()
    out_dir = ROOT / "output" / today
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "_work"
    print(f"[agent] आज का स्किट: {script['title']} ({script.get('source', 'manual')})")
    info = render(script, char, out_dir / "reel.mp4", work)
    shutil.rmtree(work, ignore_errors=True)
    (out_dir / "caption.txt").write_text(script["caption"], encoding="utf-8")
    (out_dir / "script.json").write_text(json.dumps({**script, **info}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[agent] वीडियो तैयार: {out_dir/'reel.mp4'}  ({info['duration']}s, आवाज़: {info['tts']})")

    hist_p = ROOT / "output" / "history.json"
    hist = json.loads(hist_p.read_text(encoding="utf-8")) if hist_p.exists() else []
    hist.append({"date": today, "title": script["title"], "source": script.get("source")})
    hist_p.write_text(json.dumps(hist[-200:], ensure_ascii=False, indent=1), encoding="utf-8")

    if args.post:
        poster.publish(out_dir / "reel.mp4", script["caption"])


if __name__ == "__main__":
    main()
