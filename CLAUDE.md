# DESI MINING WALA Video Studio — Claude instructions

- Owner talks in Hinglish from an Android phone (Chrome, desktop mode). Reply in simple Hinglish.
- Main workflow skill: `.claude/skills/dmw-video-editor/SKILL.md`. Remotion skills: `.claude/skills/remotion-*`.
- Pipeline CLI: `python pipeline/studio.py {doctor|probe|plan|render|demo|transcribe|manifest}`.
- Config: `studio.config.json` (brand colors, styles, captions, audio, limits).
- Cloud session limits: `huggingface.co` and `remotion.media` may be blocked → Whisper falls back to
  script/SRT captions, Remotion uses the preinstalled Chromium headless shell (auto-detected).
  GitHub Actions (`.github/workflows/render.yml`) has full internet and renders jobs from `jobs/*.json`.
- Never commit private media while the repo is public; never use paid APIs without approval.

## Multi-agent studio (30 subagents)
- Agents: `.claude/agents/*.md` (generated from `workflow/tools/build_agents.py` — edit the generator, then
  run it and `python workflow/tools/validate_agents.py`).
- For any video production request, delegate to the **master-director** subagent (or start the CLI with
  `claude --agent master-director`). It reads `workflow/ROUTING.md`, picks the MINIMUM agents and runs
  independent ones in parallel. Do not call all 30 agents for simple tasks.
- Shared protocol: `workflow/PROTOCOL.md` (file ownership, handoffs), tools: `workflow/TOOLS.md`,
  brand: `brand/BRAND_RULES.md`, templates: `workflow/templates/`.
- Subagents cannot send files to the phone: the main session delivers the final MP4 (SendUserFile) after QC.
