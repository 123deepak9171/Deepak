---
name: dmw-video-editor
description: DESI MINING WALA video studio. Use when the user gives raw videos/photos/scripts/logos and Hinglish editing instructions and wants an edited MP4 (reel, shorts, YouTube video, product reveal, captions, music, green screen, vertical conversion).
---

# DMW Video Editor (multi-agent workflow)

You are the **Director**. Work through these agent roles in order. Each role maps to code in `pipeline/dmw/`.

1. **Planner** (`planner.py`): Read the user's Hinglish instructions. Write a job JSON in `jobs/<id>.json`
   (schema: `templates/jobs/*.json`, full reference in README "Job JSON"). Run
   `python pipeline/studio.py plan jobs/<id>.json` and show the plan steps to the user in simple Hinglish.
   Ask before rendering only if something important is ambiguous (aspect, duration, which clips).
2. **Editor** (`editor.py`): cutting, silence removal, vertical conversion (`fit_mode`: blur|crop|pad),
   green screen, punch-in/zoom, Ken Burns photos, transitions, merging.
3. **Motion designer** (`remotion/src/compositions/*`): LogoReveal, ProductReveal, TitleCard, Outro.
   For new motion graphics, follow `.claude/skills/remotion-best-practices` (frame-driven animation only,
   no CSS animations) and register the composition in `remotion/src/Root.tsx` with `calculateMetadata`.
4. **Caption agent** (`captions.py`): Faster-Whisper (`language=hi`, Haryanvi prompt) → animated ASS
   captions; fallback to `script` (.txt) or `srt`.
5. **Sound agent** (`render.py:final_mix`): voice cleanup, music ducking, whoosh SFX, -14 LUFS.
6. **QA agent** (`render.py:qa_check`): codec/resolution/duration/decode checks → `output/<id>/report.json`.
   Optional browser check: `node pipeline/tools/verify_playback.cjs output/<id>/<id>.mp4`.

## Commands
```bash
python pipeline/studio.py doctor
python pipeline/studio.py probe assets/raw-videos/x.mp4
python pipeline/studio.py plan jobs/<id>.json
python pipeline/studio.py render jobs/<id>.json      # -> output/<id>/<id>.mp4
python pipeline/studio.py transcribe <media> --language hi --dialect haryanvi
```
Use `.venv/bin/python` if a venv exists (`python3 -m venv .venv && .venv/bin/pip install -r pipeline/requirements.txt`).

## Delivering the MP4 to a mobile user
Files inside a cloud session are NOT directly downloadable. Use one of:
- Send the file with the SendUserFile tool (shows a file card in the Claude app).
- Commit the job JSON to `jobs/` and let `.github/workflows/render.yml` render it; MP4 appears in the
  Actions run Artifacts (or a Release if `export.publish_release` is true).

## Safety rules
- Never commit the user's private media while the repo is public. Ask first.
- Never spend paid API credits or buy subscriptions. Whisper/FFmpeg/Remotion run locally for free.
- Remotion license: free for individuals and companies with up to 3 employees; bigger for-profit
  companies need a Remotion Company License (remind the user if team size is unknown).
