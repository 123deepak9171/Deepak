# 🎬 DESI MINING WALA — AI Video Studio

Cloud-based, multi-agent video editing studio. Aap raw videos, photos, script aur logo do, Hinglish me bolo kya chahiye — studio khud edit karke **professional MP4** bana deta hai.

Sab kuch **free & open-source** tools se: FFmpeg, Remotion, Faster-Whisper, Python, Node.js. Koi paid API nahi, koi subscription nahi.

---

## 1. Ye kaam kaise karta hai (ek nazar me)

```
Aapka phone (Chrome)
   │  media upload + instructions
   ▼
Dashboard (docs/index.html)  ──►  jobs/<naam>.json  (GitHub pe commit)
                                        │
                                        ▼
                        GitHub Actions (free cloud computer)
   ┌──────────── AI agents (pipeline/dmw/) ─────────────┐
   │ Planner → Editor → Motion (Remotion) → Captions     │
   │ (Whisper) → Sound → Colorist → QA                   │
   └─────────────────────────────────────────────────────┘
                                        │
                                        ▼
                MP4 download: Actions "Artifacts" ya Release link
```

Doosra tareeka: **Claude Code se seedha bolo** — "ye videos le ke 30 sec ki reel banao" — Claude yahi pipeline chalaayega aur MP4 aapko chat me bhej dega.

---

## 2. Kya kya features hain

| Feature | Kaise hota hai |
|---|---|
| Automatic cutting | `start`/`end` trim + target duration ke hisaab se auto-fit |
| Silence removal | FFmpeg `silencedetect` → khamoshi wale hisse kaat ke jump-cut |
| Cinematic editing | Style presets: `desi-mining`, `cinematic`, `energetic`, `minimal`, `documentary` |
| Animated captions | Har shabd highlight (gold) + pop animation, Hindi Devanagari + Hinglish (Mukta font) |
| Motion graphics | Remotion: Logo reveal, Product reveal, Title card, Outro + Subscribe CTA |
| Product reveal | Curtain wipe + product photo rise + price tag |
| Logo animation | Intro me logo pop + brand name typing; video me watermark |
| Camera zoom | Slow push-in (zoompan) + jump-cut punch-in zoom |
| Color grading | Presets (`earthy-mining`, `teal-orange`, `vibrant`, `bw`…) + `.cube` LUT support |
| Audio mixing | Voice cleanup (highpass + compressor), loudness −14 LUFS (YouTube/Insta standard) |
| Background music | Loop + fade in/out + **auto ducking** (aawaaz aate hi music dheema) |
| Sound effects | Har transition par auto "whoosh" + apne SFX kisi bhi time par |
| Image animation | Ken Burns: zoom-in, zoom-out, pan-left, pan-right |
| Transitions | 50+ FFmpeg xfade transitions (fade, slide, circleopen, zoomin…) |
| Green screen | Chromakey + despill, background photo/video se replace |
| Video merging | Multiple clips + photos + titles ek timeline me |
| Vertical conversion | 16:9 → 9:16 (blur background / crop / pad) |
| Final export | H.264 High + AAC, yuv420p, `+faststart` (mobile pe turant chalta hai) |

---

## 3. Folder structure

```
Deepak/
├── README.md                ← ye file
├── CLAUDE.md                ← Claude ke liye rules
├── studio.config.json       ← brand colors, styles, captions, audio, limits
├── assets/                  ← PERMANENT media folders
│   ├── raw-videos/  photos/  logos/  music/  sfx/  scripts/  luts/
│   └── fonts/               ← Mukta, Poppins, Noto Sans Devanagari (OFL)
├── jobs/                    ← yahan job JSON commit karo = render shuru
├── templates/jobs/          ← ready-made job examples (copy karke use karo)
├── pipeline/                ← Python video engine (FFmpeg)
│   ├── studio.py            ← CLI: doctor | probe | plan | render | demo | transcribe
│   └── dmw/                 ← agents: planner, editor, motion, captions, render(sound+QA)
├── remotion/                ← motion graphics (React/Remotion)
├── docs/index.html          ← mobile dashboard
├── samples/                 ← test demo MP4 (download karke dekh sakte ho)
├── tests/                   ← unit tests
├── .claude/skills/          ← Remotion official skills + dmw-video-editor skill
├── .claude/agents/          ← planner, motion-designer, qa-reviewer agents
└── .github/workflows/       ← render.yml (cloud render), whisper-test.yml
```

---

## 4. Mobile se use kaise karein (3 tareeke)

### Tareeka A — Claude Code se bolo (sabse aasaan)
1. Claude Code (claude.ai/code) me ye repo kholo.
2. Media bhejo/upload karo aur likho, jaise:
   > "assets/raw-videos/clip1.mp4 aur clip2.mp4 se 30 sec ki energetic reel banao, silence hatao, Haryanvi captions, logo aur music ke saath."
3. Claude plan dikhayega → aap "haan" bolo → render hoga → **MP4 file chat me aayegi** (download button).

### Tareeka B — Dashboard + GitHub Actions (bina Claude ke)
1. Dashboard kholo (neeche "Dashboard kaise kholein" dekho).
2. **⬆ Video upload** se media GitHub par daalo → **↻ Media list** → files timeline me add karo.
3. Instructions likho, style / format / duration chuno.
4. **👁 Plan preview** → plan check karo.
5. **🎬 Render request** → GitHub ka page khulega → neeche **Commit changes** dabao.
6. **▶ Render status** → Actions me run dikhega (5–15 min). Hara ✔ aane par MP4 ready.

### Tareeka C — Actions se manually
GitHub → **Actions** → **Render Video** → **Run workflow** → job path likho (jaise `jobs/demo-9x16.json`).

---

## 5. MP4 mobile pe download kaise karein ⬇

Cloud session ki files seedhe phone pe download nahi hoti. Isliye ye supported raste hain:

| Tareeka | Kaise | Note |
|---|---|---|
| **Claude chat file** | Claude render ke baad MP4 chat me bhejta hai | Turant, sabse simple |
| **Actions Artifact** | Actions → run kholo → neeche **Artifacts** → `rendered-videos-N` | ZIP milta hai; Android **Files** app me tap karke "Extract" karo. GitHub login chahiye. 14 din rehta hai |
| **GitHub Release** | Job me `"export": {"publish_release": true}` ya Run workflow me ✔ | **Direct MP4 link** — tap karo, download. ⚠ Public repo me release public hoti hai |
| **Repo file** | `samples/` jaisi chhoti files → file kholo → **⋯ → Download** | Sirf chhoti, non-private demo files ke liye |

---

## 6. Media upload kaise karein

- **25 MB tak**: GitHub repo → `assets/raw-videos` folder → **Add file → Upload files** (dashboard ka ⬆ button yahi kholta hai).
- **25 MB se badi video** (phone ki videos aksar badi hoti hain): GitHub → **Releases → Draft a new release** → tag `media-01` → video ko **Attach binaries** me daalo → Publish (ya draft save). Phir us file ka link (`https://github.com/.../releases/download/media-01/clip.mp4`) job ke `src` me daalo. Pipeline khud download kar lega (max 4 GB).
- ⚠ **Privacy**: ye repo abhi **PUBLIC** hai. Private/company media upload karne se pehle **Settings → General → Danger Zone → Change visibility → Private** karo. Private repo me bhi GitHub Actions free minutes milte hain (monthly limit ke andar).

---

## 7. Dashboard kaise kholein

- **GitHub Pages (recommended)**: Repo **Settings → Pages → Source: Deploy from a branch → Branch: (main branch) / `docs`** → Save. 1–2 min baad link milega: `https://123deepak9171.github.io/Deepak/`. Phone ke home screen pe "Add to Home screen" kar lo.
- Dashboard aapki settings phone ke browser me yaad rakhta hai. Koi password/token nahi maangta.
- Dashboard me **Branch** field me wahi branch likho jisme `.github/workflows/render.yml` hai.

---

## 8. Job JSON (render ka recipe)

Dashboard ye file khud banata hai. Haath se likhni ho to `templates/jobs/` copy karo.

```jsonc
{
  "id": "crusher-reel",                 // output/crusher-reel/crusher-reel.mp4
  "title": "Naya Crusher",
  "instructions": "30 sec energetic reel, silence hatao, captions",  // Hinglish keywords samjhe jaate hain
  "style": "energetic",                 // desi-mining | cinematic | energetic | minimal | documentary
  "aspect": "9:16",                     // 9:16 | 16:9 | 1:1 | 4:5
  "target_duration": 30,                // seconds (max 900)
  "fit_mode": "blur",                   // vertical conversion: blur | crop | pad
  "remove_silence": true,
  "timeline": [
    { "type": "video", "src": "assets/raw-videos/clip1.mp4", "start": 0, "end": 25 },
    { "type": "video", "src": "assets/raw-videos/green.mp4",
      "greenscreen": { "background": "assets/photos/site.jpg", "color": "0x00FF00" } },
    { "type": "image", "src": "assets/photos/crusher.jpg", "duration": 3, "animation": "zoom-in" },
    { "type": "title", "title": "Price Kitna?", "subtitle": "", "duration": 2.5 }
  ],
  "logo": { "src": "assets/logos/logo.png", "intro": true, "outro": true, "watermark": true },
  "product_reveal": { "enabled": true, "title": "DMW CRUSHER X1", "subtitle": "Ghana Powerful!",
                      "image": "assets/photos/crusher.jpg", "price": "₹ 4.5 Lakh", "position": "start" },
  "captions": { "enabled": true, "source": "auto", "language": "hi", "dialect": "haryanvi",
                "script": "assets/scripts/crusher.txt" },   // ya "srt": "assets/scripts/x.srt"
  "music": { "enabled": true, "src": "assets/music/track.mp3", "volume": 0.2, "duck": true },
  "sfx": [ { "src": "assets/sfx/boom.wav", "at": 4.5, "volume": 0.7 } ],
  "grade": "earthy-mining",             // optional override; "lut": "assets/luts/film.cube"
  "export": { "crf": 20, "preset": "medium", "publish_release": false }
}
```

**Instructions keywords** (planner samajhta hai): `reel / shorts / vertical` → 9:16 · `youtube / horizontal` → 16:9 · `square` → 1:1 · `cinematic / filmy` · `energetic / josh / tez / viral` · `minimal / saaf` · `documentary / news` · `30 sec`, `2 minute` · `silence / gap hatao` · `caption` · `music mat` · `product / launch` · `black and white`.

---

## 9. Captions — Hindi & Haryanvi (Faster-Whisper)

- Engine: **Faster-Whisper** (MIT license), CPU pe free chalta hai. Language `hi`, aur Haryanvi ke liye ek special prompt (`studio.config.json → transcription.haryanvi_prompt`) jo Haryanvi shabd (thaara, mhara, ghana, sai…) pehchanne me madad karta hai.
- Model: default `small`. Better Hindi accuracy ke liye `medium` (dheema). `DMW_WHISPER_MODEL=medium` ya config me badlo.
- Fallback order (`source: "auto"`): Whisper → `srt` file → `script` .txt (script ke shabd boli hui jagah par auto-time hote hain) → captions skip.
- Output aksar **Devanagari** me aata hai. Hinglish (Roman) captions chahiye to apna script/SRT do.
- Manual transcription: `python pipeline/studio.py transcribe video.mp4 --language hi --dialect haryanvi` → `.srt`.

---

## 10. Safe rendering workflow (kya protection hai)

1. Job validate: har path repo ke andar hona chahiye (`../` blocked), file types check, limits (duration ≤ 900s, items ≤ 60, input ≤ 4 GB).
2. Disk space check (min 2 GB free).
3. Lock file: ek job ek time pe ek hi baar render.
4. Original media kabhi overwrite nahi hota — sab kaam `output/<id>/work/` me.
5. Har FFmpeg/Remotion command pe timeout, bina shell (no command injection).
6. Final MP4 pehle `.partial.mp4` me banta hai, poora hone par hi rename.
7. Remotion fail ho to FFmpeg title-card fallback (render rukta nahi).
8. QA agent: codec, resolution, fps, audio, duration, poora decode check → `report.json`.
9. Remote media sirf GitHub hosts se (https), size limit ke saath.

---

## 11. Commands (Claude ya developer ke liye)

```bash
python3 -m venv .venv && .venv/bin/pip install -r pipeline/requirements.txt
(cd remotion && npm ci)

.venv/bin/python pipeline/studio.py doctor                 # tools check
.venv/bin/python pipeline/studio.py demo                   # demo assets + render
.venv/bin/python pipeline/studio.py plan jobs/x.json       # plan preview
.venv/bin/python pipeline/studio.py render jobs/x.json     # render
.venv/bin/python pipeline/studio.py probe output/x/x.mp4   # duration/resolution/codec
.venv/bin/python -m unittest discover -s tests             # unit tests
node pipeline/tools/verify_playback.cjs output/x/x.mp4     # browser playback test
(cd remotion && npx remotion studio)                       # motion graphics preview
```

---

## 12. Test results (is cloud session me)

| Test | Result |
|---|---|
| Demo 9:16 reel (logo intro, product reveal, silence cut, green screen, Ken Burns, captions, music ducking, whoosh SFX, outro) | ✅ PASS — 1080x1920, H.264 High + AAC 48 kHz, 30 fps, ~20.8 s, ~7.7 MB, −13.8 LUFS |
| 16:9 cinematic (title card, SRT captions Hindi+Hinglish, custom SFX, pan photo) | ✅ PASS — 1920x1080, H.264/AAC, 10.4 s |
| Full decode (`ffmpeg -v error … -f null`) | ✅ 0 errors |
| Chromium browser playback | ✅ play hua, duration 20.77 s, 1080x1920 |
| Devanagari caption shaping (राम राम भाई) | ✅ sahi render |
| Unit tests | ✅ 7/7 |

Demo video: [`samples/demo-9x16.mp4`](samples/demo-9x16.mp4) (synthetic test pattern + tones, koi private media nahi).

---

## 13. Cloud session ki rukawatein (blockers) aur alternative

| Blocker | Kya hua | Alternative (ho chuka hai) |
|---|---|---|
| `huggingface.co` blocked | Whisper model download nahi hua (403 proxy) | GitHub Actions me Whisper chalta hai (`whisper-test.yml`); session me script/SRT captions fallback. Ya environment me `huggingface.co` allow karwao |
| `remotion.media` blocked | Remotion ka apna Chrome download nahi hua | Pre-installed Chromium headless shell auto-detect hota hai; Actions me Remotion apna browser khud download karta hai |
| Cloud files seedhe download nahi | — | Claude chat file, Actions Artifact, Release link (section 5) |
| GitHub web upload 25 MB limit | — | Release assets + `src` me https link |

---

## 14. Licenses ⚖

- **FFmpeg** (LGPL/GPL build, Ubuntu package) — free use.
- **Faster-Whisper** (MIT), Whisper models (MIT) — free.
- **Fonts**: Mukta, Poppins, Noto Sans Devanagari — SIL Open Font License (`assets/fonts/OFL-*.txt`).
- **Remotion** — ⚠ *source-available*, MIT nahi. **Free**: individuals, aur **3 employees tak** wali for-profit companies. **4+ employees** wali company ko **Remotion Company License** khareedna padega (remotion.pro). Agar DESI MINING WALA me 4 ya zyada log hain, to license lo — ya Remotion scenes band karke (`logo.intro/outro: false`, product reveal off) sirf FFmpeg se render karo (FFmpeg fallback cards available).
- **Music/SFX**: sirf royalty-free ya apni banayi hui music use karo. YouTube Audio Library / Pixabay Music jaisi sites ka license padh ke.

---

## 15. Aapki approval chahiye (abhi pending)

1. **Repo Private karna** — private media upload karne se pehle (Settings → Change visibility).
2. **GitHub Pages ON karna** — dashboard ka link paane ke liye (Settings → Pages → `/docs`).
3. **Remotion license** — company me 4+ log ho to Company License.
4. (Optional) Claude environment me `huggingface.co` allow — taaki Whisper Claude session ke andar bhi chale.
