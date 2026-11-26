# Agent system test report (2026-11-26)

## 1. Structure validation
| Check | Result |
|---|---|
| `python workflow/tools/validate_agents.py` (frontmatter, unique names, tools, model, colour, sections, no file-ownership overlap, director can reach all 29 specialists, specialists cannot spawn agents, registry matches) | ✅ 30/30 valid, 75 owned paths, 0 errors |
| Official parser: `claude plugin validate` on a copy of `.claude/agents` | ✅ passed, **30 agents recognised** (only plugin README/LICENSE/icon warnings for the temporary wrapper) |
| Claude Code session reload | ✅ all 30 appeared as available agent types |
| Unit tests (`python -m unittest discover -s tests`) | ✅ 9/9 |

## 2. Real delegation tests (headless `claude -p`, stream-json logs)
| Test | What happened | Files really created |
|---|---|---|
| **T1** main session → `sound-effects` | 1 delegation; agent ran `studio.py sfx` twice | `deleg-test-1/audio/sfx_boom.wav` (1.8 s), `sfx_ding.wav`, `sfx-cues.json`, `handoffs/sound-effects.md` |
| **T2** `claude --agent master-director`, request "20s script + 5 hooks + thumbnail, no render, price unknown" | Director wrote brief + delegation plan, chose **4 of 30** agents (routing rows "Script/hooks only" + "Thumbnail only"). **script-writer ‖ viral-hook launched in the same message (parallel)**, then image-generation, then branding | `00-brief.md`, `delegation-plan.json`, `01-script.md`, `script.txt`, `02-hooks.md`, `images/thumbnail.png` (1920x1080, Remotion), `11-brand-check.md`, 5 handoffs |

Observations
- Price/specs were kept as `[CONFIRM]`; script contains PPE/safety line and brand CTA → brand rules were applied.
- Branding agent correctly FLAGGED the thumbnail because the demo "product photo" is a synthetic test pattern, not a crusher.
- T2 cost ≈ $0.97 of Claude usage (4 agents, ~3 min). T1 ≈ $0.09.

## 3. Real tool tests (`productions/_tests/tooltest`)
sfx ×7, music-bed, voiceover (espeak-ng Hindi), storyboard, track (motion 19/20 samples; face 30/30 on a real face photo) + 9:16 reframe, grade-preview, shift-audio, Remotion Thumbnail still, qc (PASS, -13.7 LUFS), export (master/reels/whatsapp/youtube), render with voiceover + audio-timing (PASS, 1080x1920).
