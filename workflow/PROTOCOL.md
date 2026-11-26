# DMW Multi-Agent Protocol (communication rules)

## 1. Production folder = shared whiteboard
Every job lives in `productions/<id>/` (id = lowercase-kebab, e.g. `crusher-x1-reel`).
Agents talk **only through files** in this folder + their final reply to the Master Director.

```
productions/<id>/
├── 00-brief.md               master-director
├── delegation-plan.json      master-director
├── asset-selection.json      asset-management
├── 01-script.md, script.txt  script-writer
├── 02-hooks.md               viral-hook
├── 03-storyboard.md, storyboard.jpg   storyboard
├── 04-prompts.md             ai-prompt-engineer
├── 05-character-bible.md     character-consistency
├── 06-ai-video-requests.md   ai-video-generation   (+ generated/)
├── 07-product-showcase.md    product-showcase
├── 08-shot-list.md           cinematic-camera
├── 09-backgrounds.md         background-reference  (+ backgrounds/, refs/)
├── 10-vfx-plan.md            visual-effects        (+ vfx/)
├── 11-brand-check.md         branding
├── 12-marketing.md           marketing-advertisement
├── fragments/                product.json, camera.json, transitions.json, grade.json,
│                             motion.json, captions.json  (one owner each)
├── edit-timeline.json        video-editor (ONLY owner; render job format)
├── tracking/                 face-object-tracking
├── sync/                     lip-sync
├── audio/                    vo_*.wav + vo-cues.json (voiceover), bed_*.mp3 + music.json
│                             (background-music), sfx_*.wav + sfx-cues.json (sound-effects),
│                             audio-timing.json (rendering merges with `studio.py merge-audio`)
├── transcript.srt            speech-transcription
├── images/                   image-generation (+ previews from motion/product agents)
├── qc/                       quality-control
├── exports/                  final-export
└── handoffs/<agent>.md       every agent (status report)
```
Exact ownership is in `workflow/agent-registry.json` → `owns`.

## 2. Rules
1. **Single writer per file.** Never edit a file you do not own. Request changes in your handoff.
2. **Fragments, not shared edits.** Editing-team and visual agents write JSON fragments; only
   `video-editor` merges them into `edit-timeline.json`. Audio agents write cue files; only
   `rendering` merges them into `audio/audio-timing.json`.
3. **Handoff file is mandatory** (`workflow/templates/handoff.md`): status DONE | PARTIAL | FAILED |
   UNSUPPORTED, files created, commands run with exit status, open issues, next agent.
4. **Honesty:** a file is only "created" if it exists; a command only "worked" if it exited 0.
   Unsupported features (AI image/video generation, human-quality TTS, generative lip-sync) are reported
   as UNSUPPORTED with the real fallback used.
5. **Approvals:** paid services, external AI, publishing, making media public → stop and ask via the
   Master Director.
6. **Brand:** `brand/BRAND_RULES.md` applies to every output.
7. **Paths:** repo-relative paths only (`assets/...`, `productions/...`). Never `../`.

## 3. Parallel stages (no file overlap → safe to run together)
| Stage | Agents (parallel inside a stage) |
|---|---|
| A Brief | master-director |
| B Creative | script-writer ‖ viral-hook ‖ asset-management ‖ character-consistency |
| C Pre-visual | storyboard ‖ product-showcase ‖ background-reference ‖ face-object-tracking ‖ color-grading ‖ ai-prompt-engineer |
| D Production | image-generation ‖ ai-video-generation ‖ visual-effects ‖ cinematic-camera ‖ motion-graphics ‖ transition ‖ voiceover ‖ background-music ‖ sound-effects ‖ speech-transcription ‖ lip-sync ‖ remotion-animation |
| E Assembly | animated-subtitle → video-editor |
| F Review | branding |
| G Render | rendering → quality-control |
| H Delivery | final-export ‖ marketing-advertisement |
Only the agents chosen in `delegation-plan.json` run; empty stages are skipped.
