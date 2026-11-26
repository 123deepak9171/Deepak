# Real tools available to agents (`python pipeline/studio.py <cmd>`)

| Command | Agent | What it really does |
|---|---|---|
| `doctor` | any | Checks ffmpeg, node, remotion, faster-whisper, browser |
| `probe <file>` | any | Duration, resolution, codecs (ffprobe) |
| `assets` | asset-management | `assets/manifest.json` with metadata + duplicate detection |
| `plan <job>` | video-editor, master-director | Validates a timeline and prints the edit plan |
| `render <job>` | rendering | Full FFmpeg + Remotion render with QA report |
| `merge-audio <prod_dir>` | rendering | Merges vo/sfx/music cue files → `audio/audio-timing.json` |
| `storyboard <job> --out <dir>` | storyboard | Real frame contact sheet + markdown table |
| `still <Comp> --props <json> --out <png>` | image-generation, motion-graphics, product-showcase, remotion-animation | Remotion still (Thumbnail, ProductReveal, TitleCard, LogoReveal, Outro) |
| `grade-preview <clip> --grades a,b --out <jpg>` | color-grading | Side-by-side grade comparison |
| `track <clip> --out <json> [--reframe 9:16]` | face-object-tracking | OpenCV face/motion tracking + subject-following crop |
| `shift-audio <clip> --ms N --out <mp4>` | lip-sync | Audio offset correction |
| `voiceover --text/--text-file --out <wav>` | voiceover | espeak-ng offline guide voice (robotic) |
| `music-bed --mood calm/energetic/epic/desi` | background-music | Synthetic placeholder music bed |
| `sfx whoosh/swipe/boom/riser/ding/click/cash` | sound-effects | Synthesised SFX |
| `transcribe <media>` | speech-transcription | Faster-Whisper Hindi/Haryanvi → SRT (model download needs huggingface.co) |
| `qc <mp4> --out-dir <dir>` | quality-control | Loudness, black/freeze/silence, faststart, contact sheet |
| `export <mp4> --presets ... --out-dir <dir>` | final-export | master/youtube/shorts/reels/whatsapp/square + sha256 |
| `node pipeline/tools/verify_playback.cjs <mp4>` | quality-control | Chromium playback test |

Render job fields agents may set: see README "Job JSON" + `voiceover: [{src, at, volume}]`,
`audio_timing: "productions/<id>/audio/audio-timing.json"`.

NOT available (report UNSUPPORTED): text-to-image / text-to-video AI, human-quality TTS or voice
cloning, generative lip-sync, AI matting/rotoscoping, auto-posting to social media.
