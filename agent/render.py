"""स्क्रिप्ट + आवाज़ → 1080x1920 इंस्टाग्राम रील (MP4)। सिर्फ़ Pillow + ffmpeg (फ्री)।"""
import math
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .character import get_sprite
from .tts import SR, speak

ROOT = Path(__file__).resolve().parent.parent
FONT = str(ROOT / "assets" / "fonts" / "Baloo2-ExtraBold.ttf")
VW, VH, FPS = 1080, 1920, 30
GAP, LEAD, ENDCARD = 0.28, 0.35, 3.0
NAME_COLORS = {"wala": (245, 124, 0), "pappu": (46, 125, 50), "bijli": (109, 76, 65)}


def font(size):
    return ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)


def wrap(text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.getlength(t) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def centered(d, y, text, f, fill, stroke=0, stroke_fill=None):
    w = f.getlength(text)
    d.text(((VW - w) / 2, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)


def _miner(d, x, y, w=210, h=130):
    d.rounded_rectangle([x, y, x + w, y + h], 12, fill=(120, 130, 140), outline=(30, 30, 30), width=5)
    d.rectangle([x + 10, y + 12, x + 40, y + h - 12], fill=(80, 88, 96))
    for i, c in enumerate([(0, 230, 118), (255, 193, 7)]):
        d.ellipse([x + 18, y + 20 + i * 26, x + 32, y + 34 + i * 26], fill=c)
    return (x + w - 70, y + h // 2)  # पंखे का सेंटर


def background(char):
    bg = Image.new("RGB", (VW, VH))
    d = ImageDraw.Draw(bg)
    for y in range(VH):  # दीवार का ग्रेडिएंट
        t = y / VH
        d.line([0, y, VW, y], fill=(int(255 - 40 * t), int(236 - 70 * t), int(179 - 90 * t)))
    d.rectangle([0, 1520, VW, VH], fill=(141, 94, 58))  # फर्श
    for x in range(0, VW, 120):
        d.line([x, 1520, x - 200, VH], fill=(120, 78, 46), width=4)
    # साइनबोर्ड
    d.rounded_rectangle([40, 40, VW - 40, 300], 30, fill=(198, 40, 40), outline=(255, 215, 0), width=10)
    centered(d, 58, "देसी माइनिंग वाला", font(118), (255, 255, 255), 6, (90, 10, 10))
    centered(d, 215, char["brand"]["handle"] + "  •  Bitcoin Mining Machines", font(46), (255, 235, 59))
    # रैक पर मशीनें
    fans = []
    for row, y in enumerate((1000, 1170)):
        d.rectangle([20, y + 135, VW - 20, y + 150], fill=(93, 64, 55))
        for i in range(4):
            fans.append(_miner(d, 40 + i * 260, y))
    return bg, fans


def draw_fans(d, fans, t):
    a = t * 14
    for cx, cy in fans:
        d.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], fill=(50, 55, 60), outline=(20, 20, 20), width=4)
        for k in range(4):
            ang = a + k * math.pi / 2
            d.line([cx, cy, cx + 44 * math.cos(ang), cy + 44 * math.sin(ang)], fill=(170, 175, 180), width=14)
        d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(255, 193, 7))


def caption_card(speaker_name, color, text):
    f = font(66)
    lines = wrap(text, f, VW - 200)
    h = 110 + len(lines) * 84
    img = Image.new("RGBA", (VW - 80, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 40, VW - 80, h + 40], 36, fill=(255, 255, 255, 240), outline=(30, 30, 30), width=6)
    nf = font(44)
    d.rounded_rectangle([40, 0, 80 + nf.getlength(speaker_name), 80], 24, fill=color + (255,))
    d.text((60, 6), speaker_name, font=nf, fill="white")
    for i, ln in enumerate(lines):
        d.text((60, 100 + i * 84), ln, font=f, fill=(25, 25, 25))
    return img


def end_card(char):
    img = Image.new("RGBA", (VW, VH), (10, 10, 30, 225))
    d = ImageDraw.Draw(img)
    centered(d, 520, "बिटकॉइन माइनिंग", font(110), (255, 193, 7), 5, (0, 0, 0))
    centered(d, 650, "मशीन चाहिए?", font(110), (255, 193, 7), 5, (0, 0, 0))
    d.rounded_rectangle([120, 860, VW - 120, 1040], 40, fill=(198, 40, 40))
    centered(d, 885, "DM करो →", font(90), (255, 255, 255))
    centered(d, 1100, char["brand"]["handle"], font(96), (255, 255, 255), 4, (198, 40, 40))
    centered(d, 1240, "मशीन • सेटअप • सपोर्ट", font(60), (200, 230, 255))
    f = font(34)
    for i, ln in enumerate(wrap("सूचना: " + char["brand"]["disclaimer"], f, VW - 160)):
        centered(d, 1640 + i * 46, ln, f, (220, 220, 220))
    return img


def build_audio(script, char, work):
    chunks, timeline, t, engines = [np.zeros(int(SR * LEAD), np.float32)], [], LEAD, set()
    for i, line in enumerate(script["lines"]):
        c = char["characters"].get(line["speaker"], char["characters"]["wala"])
        samples, eng = speak(line["text"], c["voice"], c.get("voice_pitch", "+0Hz"),
                             c.get("voice_rate", "+0%"), work, i)
        engines.add(eng)
        dur = len(samples) / SR
        timeline.append({**line, "start": t, "end": t + dur})
        chunks += [samples, np.zeros(int(SR * GAP), np.float32)]
        t += dur + GAP
    chunks.append(np.zeros(int(SR * ENDCARD), np.float32))
    audio = np.concatenate(chunks)
    peak = float(np.max(np.abs(audio))) or 1.0
    audio = audio / peak * 0.9
    wav = work / "voice.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(SR)
        w.writeframes((audio * 32767).astype(np.int16).tobytes())
    return audio, timeline, wav, engines


def render(script, char, out_mp4, work):
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    audio, timeline, wav, engines = build_audio(script, char, work)
    total = len(audio) / SR
    n = int(total * FPS)
    # हर फ्रेम की आवाज़ की ताकत → मुँह खुला/बंद
    hop = SR // FPS
    rms = np.array([np.sqrt(np.mean(audio[i * hop:(i + 1) * hop] ** 2) + 1e-9) for i in range(n)])
    thr = max(0.02, 0.18 * (rms.max() or 1))

    bg, fans = background(char)
    cast = []
    for l in timeline:
        if l["speaker"] not in cast:
            cast.append(l["speaker"])
    cast = sorted(cast, key=lambda s: {"wala": 0, "pappu": 1, "bijli": 2}.get(s, 3))
    scale = 0.86 if len(cast) <= 2 else 0.64
    sw, sh = int(640 * scale), int(980 * scale)
    xs = {1: [(VW - sw) // 2], 2: [10, VW - sw - 10], 3: [0, (VW - sw) // 2, VW - sw]}[min(len(cast), 3)]
    pos = {s: xs[i] for i, s in enumerate(cast[:3])}
    names = {k: v["display_name"] for k, v in char["characters"].items()}
    cards = [caption_card(names.get(l["speaker"], l["speaker"]), NAME_COLORS.get(l["speaker"], (0, 0, 0)), l["text"])
             for l in timeline]
    endc = end_card(char)
    title_f = font(58)
    last_emotion = {s: "normal" for s in cast}

    out_mp4 = Path(out_mp4)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}",
         "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest",
         "-movflags", "+faststart", str(out_mp4)], stdin=subprocess.PIPE)
    end_start = timeline[-1]["end"] + 0.4
    for fi in range(n):
        t = fi / FPS
        frame = bg.copy()
        d = ImageDraw.Draw(frame)
        draw_fans(d, fans, t)
        cur = next((i for i, l in enumerate(timeline) if l["start"] - GAP <= t < l["end"] + GAP), None)
        if cur is not None:
            last_emotion[timeline[cur]["speaker"]] = timeline[cur]["emotion"]
        frame = frame.convert("RGBA")
        for s in cast[:3]:
            speaking = cur is not None and timeline[cur]["speaker"] == s and timeline[cur]["start"] <= t < timeline[cur]["end"]
            mouth = bool(speaking and rms[fi] > thr)
            spr = get_sprite(s, last_emotion[s], mouth, scale)
            bounce = int(abs(math.sin(t * 9)) * 18) if speaking else int(math.sin(t * 2 + pos[s]) * 4)
            frame.alpha_composite(spr, (pos[s], VH - sh - 30 - bounce))
        # हुक/टाइटल पट्टी
        if t < 2.5:
            d2 = ImageDraw.Draw(frame)
            d2.rounded_rectangle([60, 330, VW - 60, 430], 30, fill=(0, 0, 0, 200))
            centered(d2, 335, script["title"], title_f, (255, 235, 59))
        if cur is not None and t < end_start:
            card = cards[cur]
            pop = min(1.0, (t - timeline[cur]["start"] + GAP) / 0.15)
            y = 470
            if pop < 1:
                card = card.resize((max(1, int(card.width * (0.85 + 0.15 * pop))), max(1, int(card.height * (0.85 + 0.15 * pop)))))
            frame.alpha_composite(card, ((VW - card.width) // 2, y))
        if t >= end_start:
            a = min(1.0, (t - end_start) / 0.4)
            ec = endc if a >= 1 else Image.blend(Image.new("RGBA", endc.size, (0, 0, 0, 0)), endc, a)
            frame.alpha_composite(ec)
        ff.stdin.write(frame.convert("RGB").tobytes())
    ff.stdin.close()
    ff.wait()
    if ff.returncode:
        raise RuntimeError("ffmpeg failed")
    return {"duration": round(total, 1), "tts": sorted(engines), "timeline": timeline}
