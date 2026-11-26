---
name: desi-mining-reel
description: Desi Mining Wala (@desi.mining.wala) Instagram के लिए रोज़ की हिंदी कॉमेडी रील बनाता है — पुरानी वीडियो एनालाइज़ करना, कैरेक्टर (मिनिंग वाले भैया, पप्पू, बिजली अंकल) के साथ नया स्किट लिखना, आवाज़ + कार्टून वीडियो रेंडर करना, और आख़िर में बिटकॉइन माइनिंग मशीन ख़रीदने का CTA। Use when the user asks for a new reel, a comedy video, a new skit, video analysis of their Instagram, or to change the character.
---

# Desi Mining Wala — Reel Agent

यह रिपो एक पूरा फ्री वीडियो-एजेंट है। तुम (Claude) इसके "डायरेक्टर" हो।

## रोज़ की रील बनाना
1. `config/character.yaml` पढ़ो — ब्रांड, कैरेक्टर, `style` और `learned_from_my_videos`।
2. `output/history.json` से पिछले टाइटल देखो, कोई टॉपिक दोहराना नहीं।
3. नया स्किट खुद लिखो और `output/next_script.json` में सेव करो:
   ```json
   {"title": "...", "lines": [{"speaker": "pappu", "emotion": "shocked", "text": "..."}],
    "caption": "... #bitcoinmining ... DM @desi.mining.wala ... सूचना: Crypto unregulated है ..."}
   ```
   - speaker: `wala` | `pappu` | `bijli`; emotion: `normal|happy|shocked|angry|sad`
   - 5–7 लाइन, देवनागरी, हर लाइन < 18 शब्द, पहली लाइन ज़ोरदार हुक
   - आखिरी लाइन `wala` की हो और बात **देसी माइनिंग वाला से बिटकॉइन माइनिंग मशीन लेने** पर ख़त्म हो
   - कभी नहीं: "पैसा डबल", "गारंटीड प्रॉफिट", "रिस्क फ्री", किसी धर्म/जाति/व्यक्ति का मज़ाक
   - कैप्शन में `brand.disclaimer` ज़रूर
4. रेंडर: `python run_daily.py --script output/next_script.json`
5. `output/<date>/reel.mp4` से 3–4 फ्रेम निकालकर (ffmpeg) देखो कि टेक्स्ट कटा नहीं, फिर यूज़र को वीडियो + कैप्शन दो।

बिना Claude के भी चलता है: `python run_daily.py` (Gemini फ्री key हो तो AI स्क्रिप्ट, वरना `config/skits.yaml` बैंक)।

## पुरानी वीडियो एनालाइज़ करना
यूज़र की वीडियो `my_videos/` में हों → `pip install faster-whisper && python -m agent.analyze`।
फिर `analysis/report.md` और `analysis/frames/` देखो, और ज़रूरत हो तो `character.yaml`
(तकिया-कलाम, रंग, टोन) और `config/skits.yaml` में नए स्किट जोड़ो।

## कैरेक्टर बदलना
लुक `agent/character.py` में है (Pillow ड्रॉइंग)। बदलने के बाद `python agent/character.py`
से `character_sheet.png` बनाकर चेक करो।
