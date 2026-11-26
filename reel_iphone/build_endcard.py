"""असली दुकान/मशीन/लोगो से 10 सेकंड का सिनेमैटिक एंड-कार्ड (1080x1920)।
    python reel_iphone/build_endcard.py  → reel_iphone/endcard.mp4
"""
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "assets" / "brand"
FONT = str(ROOT / "assets" / "fonts" / "Baloo2-ExtraBold.ttf")
VW, VH, FPS, DUR = 1080, 1920, 30, 10.0
PHONE = "80590 44144"          # लोगो + बैनर पर यही नंबर है
PHONE2 = ""                     # दूसरा नंबर कन्फर्म हो तो यहाँ डालें
SITE, INSTA = "desiminingwala.com", "@desi.mining.wala"
GOLD, WHITE = (255, 196, 0), (255, 255, 255)


def F(s):
    return ImageFont.truetype(FONT, s, layout_engine=ImageFont.Layout.RAQM)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ctext(d, y, t, f, fill, a=1.0, stroke=0):
    w = f.getlength(t)
    d.text(((VW - w) / 2, y), t, font=f, fill=fill + (int(255 * a),), stroke_width=stroke,
           stroke_fill=(0, 0, 0, int(255 * a)))


def vignette():
    v = Image.new("L", (VW, VH), 0)
    ImageDraw.Draw(v).ellipse([-300, -200, VW + 300, VH + 200], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(220))
    out = Image.new("RGBA", (VW, VH), (0, 0, 0, 255))
    out.putalpha(Image.eval(v, lambda p: 255 - p))
    return out


shop = Image.open(B / "shop.jpg").convert("RGB")
machine = Image.open(B / "machine.png").convert("RGB")
logo = Image.open(B / "logo.png").convert("RGB")
VIG = vignette()
grad = Image.new("RGBA", (VW, VH))
gd = ImageDraw.Draw(grad)
for y in range(VH):
    a = int(230 * max(0, (y - 1150) / 770) ** 1.3)
    gd.line([0, y, VW, y], fill=(0, 0, 0, a))

# मशीन: सफ़ेद बैकग्राउंड हटाओ
m = machine.resize((900, 900), Image.LANCZOS).convert("RGBA")
px = [(r, g, b, 0 if r > 238 and g > 238 and b > 238 else 255) for r, g, b, _ in m.getdata()]
m.putdata(px)
MACH = m
lg = logo.resize((760, 760), Image.LANCZOS)
mask = Image.new("L", lg.size, 0)
ImageDraw.Draw(mask).ellipse([0, 0, 759, 759], fill=255)
LOGO = lg.convert("RGBA")
LOGO.putalpha(mask)


def scene_shop(t):  # 0 → 3.6s: दुकान पर धीमा कैमरा पैन + ज़ूम
    p = t / 3.6
    h = int(2304 / (1.0 + 0.12 * p))
    w = int(h * VW / VH)
    x = int(1450 + 650 * ease(p))
    y = (2304 - h) // 2
    fr = shop.crop((x, y, x + w, y + h)).resize((VW, VH), Image.LANCZOS).convert("RGBA")
    fr.alpha_composite(grad)
    d = ImageDraw.Draw(fr)
    a = ease((t - 0.5) / 0.6)
    ctext(d, 1480, "असली दुकान, असली मशीन", F(96), WHITE, a, 4)
    ctext(d, 1610, "अर देसी भरोसा!", F(110), GOLD, ease((t - 1.2) / 0.6), 4)
    return fr


def scene_machine(t):  # 3.6 → 6.8s
    p = (t - 3.6) / 3.2
    fr = Image.new("RGBA", (VW, VH), (8, 12, 28, 255))
    d = ImageDraw.Draw(fr)
    for r in range(700, 0, -20):  # सुनहरी चमक
        c = int(70 * (1 - r / 700))
        d.ellipse([VW / 2 - r, 1000 - r, VW / 2 + r, 1000 + r], fill=(20 + c * 2, 20 + c, 30, 255))
    s = 0.82 + 0.16 * ease(p)
    mm = MACH.resize((int(900 * s), int(900 * s)), Image.LANCZOS)
    fr.alpha_composite(mm, ((VW - mm.width) // 2, 1000 - mm.height // 2 + int(10 * math.sin(t * 2))))
    d = ImageDraw.Draw(fr)
    a1 = ease((t - 3.8) / 0.4)
    ctext(d, 170, "₹2 लाख का फ़ोन?", F(100), WHITE, a1, 3)
    if t > 4.6:  # स्ट्राइक-थ्रू
        w = F(100).getlength("₹2 लाख का फ़ोन?") * ease((t - 4.6) / 0.35)
        d.line([(VW - F(100).getlength("₹2 लाख का फ़ोन?")) / 2, 240, (VW - F(100).getlength("₹2 लाख का फ़ोन?")) / 2 + w, 240],
               fill=(230, 40, 40, 255), width=14)
    a2 = ease((t - 5.0) / 0.5)
    ctext(d, 310, "या कमावण आळी मशीन?", F(104), GOLD, a2, 3)
    ctext(d, 1560, "बिटकॉइन माइनिंग मशीन", F(70), WHITE, ease((t - 5.4) / 0.5), 3)
    return fr


def scene_logo(t):  # 6.8 → 10s
    p = ease((t - 6.8) / 0.7)
    fr = Image.new("RGBA", (VW, VH), (6, 10, 24, 255))
    d = ImageDraw.Draw(fr)
    for i in range(40):  # हल्के चमकते कण
        x = (i * 263 + t * 40 * (1 + i % 3)) % VW
        y = (i * 541 - t * 60) % VH
        r = 2 + i % 4
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 200, 60, 90))
    s = 0.7 + 0.3 * p
    lgi = LOGO.resize((int(760 * s), int(760 * s)), Image.LANCZOS)
    fr.alpha_composite(lgi, ((VW - lgi.width) // 2, 140 + (760 - lgi.height) // 2))
    d = ImageDraw.Draw(fr)
    a = ease((t - 7.3) / 0.5)
    d.rounded_rectangle([110, 990, VW - 110, 1170], 50, fill=(37, 211, 102, int(255 * a)))
    ctext(d, 1008, "WhatsApp " + PHONE, F(84), WHITE, a)
    y = 1210
    if PHONE2:
        ctext(d, y, PHONE2, F(70), WHITE, a)
        y += 100
    a2 = ease((t - 7.8) / 0.5)
    ctext(d, y + 20, SITE, F(76), GOLD, a2, 2)
    ctext(d, y + 130, INSTA, F(76), WHITE, a2, 2)
    f = F(34)
    for i, ln in enumerate(["Crypto unregulated है और जोखिम भरा हो सकता है।",
                            "कमाई की कोई गारंटी नहीं — बिजली और BTC रेट पर निर्भर।"]):
        ctext(d, 1700 + i * 48, ln, f, (190, 190, 190), ease((t - 8.2) / 0.5))
    return fr


def frame(t):
    if t < 3.6:
        fr = scene_shop(t)
        if t > 3.2:
            fr = Image.blend(fr, scene_machine(3.6), (t - 3.2) / 0.4)
    elif t < 6.8:
        fr = scene_machine(t)
        if t > 6.4:
            fr = Image.blend(fr, scene_logo(6.8), (t - 6.4) / 0.4)
    else:
        fr = scene_logo(t)
    fr = fr.convert("RGBA")
    fr.alpha_composite(VIG)
    return fr.convert("RGB")


if __name__ == "__main__":
    out = Path(__file__).parent / "endcard.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}",
                           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close()
    ff.wait()
    print("saved", out)
