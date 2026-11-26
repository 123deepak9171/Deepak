"""रोज़ का कॉमेडी स्क्रिप्ट लिखने वाला एजेंट।

1) अगर GEMINI_API_KEY है (Google AI Studio से बिल्कुल फ्री मिलती है) → AI नया स्किट लिखता है,
   आपके कैरेक्टर-बाइबल और आपकी वीडियो के एनालिसिस को पढ़कर।
2) वरना (या AI फेल हो जाए) → config/skits.yaml वाले बैंक से दिन के हिसाब से स्किट।
हर हाल में आखिरी लाइन = देसी माइनिंग वाला से मशीन लेने का CTA।
"""
import datetime as dt
import json
import os
import random
import re
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEAKERS = {"wala", "pappu", "bijli"}
EMOTIONS = {"normal", "happy", "shocked", "angry", "sad"}

HASHTAGS = ["#bitcoin", "#bitcoinmining", "#cryptoindia", "#desicomedy", "#comedyreels",
            "#asicminer", "#mining", "#hindicomedy", "#reelsindia", "#desiminingwala"]


def load_yaml(name):
    data = yaml.safe_load((ROOT / "config" / name).read_text(encoding="utf-8"))
    learned = ROOT / "config" / "learned_style.json"
    if name == "character.yaml" and learned.exists():  # agent/analyze.py का आउटपुट
        data["style"]["learned_from_my_videos"] = json.loads(learned.read_text(encoding="utf-8"))
    return data


def _history():
    p = ROOT / "output" / "history.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def _cta_line(char):
    opts = [
        "बिटकॉइन माइनिंग मशीन चाहिए? सही मशीन, सही सलाह — DM करो @desi.mining.wala",
        "मशीन लेनी है तो देसी माइनिंग वाला! प्रोफ़ाइल पे जाओ, DM करो!",
        "असली ASIC मशीन, सेटअप और सपोर्ट — सब मिलेगा @desi.mining.wala पर!",
    ]
    return random.choice(opts)


def _finish(script, char, source):
    script["source"] = source
    lines = [l for l in script["lines"] if l.get("text", "").strip()]
    lines.append({"speaker": "wala", "emotion": "happy", "text": _cta_line(char)})
    script["lines"] = lines
    hook = lines[0]["text"]
    script.setdefault(
        "caption",
        f"{script['title']} 😂\n\n{hook}\n\nबिटकॉइन माइनिंग मशीन के लिए DM करें 👉 {char['brand']['handle']}\n\n"
        f"⚠️ {char['brand']['disclaimer']}\n\n" + " ".join(HASHTAGS))
    return script


def offline_script(char, day=None):
    bank = load_yaml("skits.yaml")["skits"]
    used = {h.get("title") for h in _history()[-len(bank) + 1:]} if len(bank) > 1 else set()
    day = day or dt.date.today().toordinal()
    order = bank[day % len(bank):] + bank[:day % len(bank)]
    skit = next((s for s in order if s["title"] not in used), order[0])
    lines = [{"speaker": s, "emotion": e, "text": t} for s, e, t in skit["lines"]]
    return _finish({"title": skit["title"], "lines": lines}, char, "offline-bank")


PROMPT = """तुम इंस्टाग्राम पेज {handle} के लिए देसी हिंदी कॉमेडी रील लिखने वाले राइटर हो।
बिज़नेस: {product}

कैरेक्टर:
- wala = {wala_role}. तकिया कलाम: {catch}
- pappu = {pappu_role}
- bijli = {bijli_role} (ज़रूरत हो तभी)

स्टाइल: {tone}. {hook_rule}.
पेज की असली वीडियो से सीखी बातें (इनके जैसा बोलचाल/टॉपिक रखो): {learned}

पिछले टाइटल (ये दोहराना मत): {recent}
आज का थीम आइडिया: {theme}

नियम:
- 5 से 7 लाइनें, हर लाइन 18 शब्द से कम, देवनागरी में लिखो।
- आखिरी पंच ऐसा हो कि बात बिटकॉइन माइनिंग मशीन ख़रीदने पर आए (CTA लाइन हम खुद जोड़ेंगे)।
- कभी मत बोलो: {never}. मुनाफ़े का कोई वादा नहीं, किसी धर्म/जाति/व्यक्ति का मज़ाक नहीं।
- emotion में सिर्फ़: normal, happy, shocked, angry, sad

सिर्फ़ यह JSON लौटाओ:
{{"title": "...", "lines": [{{"speaker": "pappu", "emotion": "shocked", "text": "..."}}]}}"""

THEMES = ["बिजली बिल", "शादी/रिश्ते", "मम्मी-पापा", "WhatsApp फ़र्ज़ी स्कीम से बचना", "पड़ोसी",
          "त्योहार", "क्रिकेट", "दोस्तों की पार्टी", "गर्मी/सर्दी में मशीन", "बिटकॉइन हॉल्विंग",
          "ऑफिस वाला बॉस", "गाँव vs शहर", "नई मशीन की डिलीवरी", "मशीन की आवाज़", "स्कूल के टीचर"]


def gemini_script(char, api_key):
    hist = _history()
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    c = char["characters"]
    prompt = PROMPT.format(
        handle=char["brand"]["handle"], product=char["brand"]["product"],
        wala_role=c["wala"]["role"], catch=", ".join(c["wala"]["catchphrases"]),
        pappu_role=c["pappu"]["role"], bijli_role=c["bijli"]["role"],
        tone=char["style"]["tone"], hook_rule=char["style"]["hook_rule"],
        learned=json.dumps(char["style"].get("learned_from_my_videos") or {}, ensure_ascii=False)[:1500],
        recent=", ".join(h.get("title", "") for h in hist[-20:]) or "कोई नहीं",
        theme=random.choice(THEMES), never=", ".join(char["style"]["never_say"]))
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": api_key}, timeout=90,
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"temperature": 1.0, "responseMimeType": "application/json"}})
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    data = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
    lines = []
    for l in data["lines"][:8]:
        sp = l.get("speaker", "wala") if l.get("speaker") in SPEAKERS else "wala"
        em = l.get("emotion", "normal") if l.get("emotion") in EMOTIONS else "normal"
        t = str(l.get("text", "")).strip()
        if any(bad in t for bad in char["style"]["never_say"]):
            raise ValueError("unsafe line from model: " + t)
        lines.append({"speaker": sp, "emotion": em, "text": t})
    if len(lines) < 3:
        raise ValueError("too few lines")
    return _finish({"title": data.get("title", "आज का धमाका"), "lines": lines}, char, f"gemini:{model}")


def write_script():
    char = load_yaml("character.yaml")
    key = os.getenv("GEMINI_API_KEY")
    if key:
        try:
            return gemini_script(char, key)
        except Exception as e:  # noqa: BLE001
            print(f"[script] Gemini फेल ({e}) → offline बैंक से स्किट")
    return offline_script(char)


if __name__ == "__main__":
    print(json.dumps(write_script(), ensure_ascii=False, indent=2))
