# Master Director Routing Table — pick the SMALLEST set

| Request type (examples) | Agents (in stage order, ‖ = parallel) | Count |
|---|---|---|
| **Quick edit**: "ye clips jod ke reel bana do" | asset-management → video-editor → rendering → quality-control → final-export | 5 |
| **Quick edit + captions** | asset-management ‖ speech-transcription → animated-subtitle → video-editor → rendering → quality-control → final-export | 7 |
| **Captions only** on an existing video | speech-transcription → animated-subtitle → video-editor → rendering → quality-control | 5 |
| **Thumbnail only** | viral-hook → image-generation → branding | 3 |
| **Script / hooks only** | script-writer ‖ viral-hook | 2 |
| **Vertical reframe** of a landscape video | face-object-tracking → video-editor → rendering → quality-control | 4 |
| **Color fix** | color-grading → video-editor → rendering → quality-control | 4 |
| **Audio fix / add music** | background-music ‖ sound-effects → video-editor → rendering → quality-control | 5 |
| **Lip-sync offset fix** | lip-sync → quality-control | 2 |
| **Green screen shot** | background-reference → visual-effects → video-editor → rendering → quality-control | 5 |
| **Product launch reel** | script-writer ‖ viral-hook ‖ asset-management → storyboard ‖ product-showcase ‖ color-grading → motion-graphics ‖ sound-effects ‖ background-music ‖ voiceover → animated-subtitle → video-editor → branding → rendering → quality-control → final-export ‖ marketing-advertisement | 16 |
| **Full YouTube production from idea** | add cinematic-camera, character-consistency, image-generation (thumbnail), speech-transcription | 15-20 |
| **Missing shots / AI visuals wanted** | ai-prompt-engineer → (USER APPROVAL) → ai-video-generation / image-generation fallback | 2-3 |
| **New animation style** | remotion-animation → motion-graphics | 2 |
| **Ad campaign copy** | marketing-advertisement → branding | 2 |

Rules
- Start from the closest row, add an agent only if the brief needs its output, remove ones whose output
  already exists in `productions/<id>/`.
- Never call an agent whose only result would be "UNSUPPORTED" without telling the user first.
- All 30 agents only when the user explicitly asks for every department.
