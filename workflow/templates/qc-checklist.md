# QC checklist (quality-control agent)
- [ ] `report.json` passed = true (codec h264, yuv420p, AAC, resolution, fps, duration, full decode)
- [ ] `studio.py qc` status PASS (or WARN explained): loudness -14 ±2 LUFS, no black/freeze mid-video, no long silence, faststart
- [ ] Contact sheet viewed: captions readable & inside safe area, logo visible, no stretched/garbled frames
- [ ] Brand check (11-brand-check.md) PASS; no unconfirmed claims on screen
- [ ] Playback test (verify_playback.cjs) plays
- [ ] Duration within ±1s of plan; aspect correct for platform
Result: PASS | WARN | FAIL  + reasons + owner agent for each fix
