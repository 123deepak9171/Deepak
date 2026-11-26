# DESI MINING WALA Video Studio — Claude instructions

- Owner talks in Hinglish from an Android phone (Chrome, desktop mode). Reply in simple Hinglish.
- Main workflow skill: `.claude/skills/dmw-video-editor/SKILL.md`. Remotion skills: `.claude/skills/remotion-*`.
- Pipeline CLI: `python pipeline/studio.py {doctor|probe|plan|render|demo|transcribe|manifest}`.
- Config: `studio.config.json` (brand colors, styles, captions, audio, limits).
- Cloud session limits: `huggingface.co` and `remotion.media` may be blocked → Whisper falls back to
  script/SRT captions, Remotion uses the preinstalled Chromium headless shell (auto-detected).
  GitHub Actions (`.github/workflows/render.yml`) has full internet and renders jobs from `jobs/*.json`.
- Never commit private media while the repo is public; never use paid APIs without approval.
