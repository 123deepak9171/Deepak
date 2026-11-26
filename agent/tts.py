"""फ्री आवाज़ (Text-to-Speech)।
1) edge-tts — Microsoft की नेचुरल हिंदी आवाज़ें, फ्री, कोई key नहीं (GitHub Actions पर चलता है)
2) espeak-ng — पूरी तरह ऑफलाइन बैकअप (रोबोटिक आवाज़)
3) कुछ न चले तो खामोशी (वीडियो फिर भी बनेगा, कैप्शन के साथ)
"""
import asyncio
import shutil
import subprocess
from pathlib import Path

import numpy as np

SR = 24000


def _decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def _edge(text, voice, pitch, rate, out):
    import edge_tts

    async def go():
        await edge_tts.Communicate(text, voice, pitch=pitch, rate=rate).save(str(out))
    asyncio.run(asyncio.wait_for(go(), timeout=60))


def _espeak(text, pitch, out):
    p = 50 + int(pitch.replace("Hz", "").replace("+", "") or 0)
    subprocess.run(["espeak-ng", "-v", "hi", "-s", "165", "-p", str(max(0, min(99, p))),
                    "-w", str(out), text], check=True, capture_output=True)


def speak(text, voice, pitch, rate, out_dir, idx):
    """लाइन को आवाज़ में बदलो → (samples float32, engine का नाम)"""
    out_dir = Path(out_dir)
    mp3 = out_dir / f"line_{idx:02d}.mp3"
    try:
        _edge(text, voice, pitch, rate, mp3)
        return _decode(mp3), "edge-tts"
    except Exception as e:  # noqa: BLE001
        print(f"[tts] edge-tts नहीं चला ({type(e).__name__}) → espeak-ng")
    if shutil.which("espeak-ng"):
        wav = out_dir / f"line_{idx:02d}.wav"
        try:
            _espeak(text, pitch, wav)
            return _decode(wav), "espeak-ng"
        except Exception as e:  # noqa: BLE001
            print(f"[tts] espeak-ng फेल: {e}")
    secs = max(1.6, len(text.split()) * 0.42)
    return np.zeros(int(SR * secs), dtype=np.float32), "silent"
