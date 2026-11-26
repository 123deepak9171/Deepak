"""कार्टून कैरेक्टर — पूरी तरह code से बने (कोई पेड टूल नहीं)।

हर कैरेक्टर के लिए expression (normal/happy/shocked/angry/sad) और मुँह खुला/बंद
वाले वेरिएंट बनते हैं, ताकि आवाज़ के साथ होंठ हिलें (lip-sync)।
"""
from functools import lru_cache
from PIL import Image, ImageDraw

W, H = 640, 980  # एक कैरेक्टर का कैनवस
OUT = (25, 20, 20, 255)
EMOTIONS = ("normal", "happy", "shocked", "angry", "sad")


def _hex(c, a=255):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def _shade(rgba, f):
    return tuple(max(0, min(255, int(v * f))) for v in rgba[:3]) + (rgba[3],)


def _eyes(d, cx, cy, emotion, sep=78, glasses=False):
    for sx in (-1, 1):
        x = cx + sx * sep
        if emotion == "shocked":
            d.ellipse([x - 34, cy - 40, x + 34, cy + 40], fill="white", outline=OUT, width=6)
            d.ellipse([x - 11, cy - 11, x + 11, cy + 11], fill=OUT)
        elif emotion == "happy":
            d.arc([x - 32, cy - 22, x + 32, cy + 30], 200, 340, fill=OUT, width=9)
        else:
            d.ellipse([x - 28, cy - 30, x + 28, cy + 30], fill="white", outline=OUT, width=6)
            off = 6 if emotion != "sad" else 0
            d.ellipse([x - 13 + off * sx * -1, cy - 8, x + 13 + off * sx * -1, cy + 18], fill=OUT)
        # भौंहें
        if emotion == "angry":
            d.line([x - 40 * sx, cy - 70, x + 30 * sx * -1 + 70 * sx, cy - 42], fill=OUT, width=12)
        elif emotion == "sad":
            d.line([x - 34 * sx * -1, cy - 46, x + 34 * sx * -1, cy - 64], fill=OUT, width=10)
        elif emotion == "shocked":
            d.arc([x - 38, cy - 92, x + 38, cy - 38], 200, 340, fill=OUT, width=10)
        else:
            d.arc([x - 36, cy - 78, x + 36, cy - 40], 205, 335, fill=OUT, width=10)
    if glasses:
        for sx in (-1, 1):
            x = cx + sx * sep
            d.rounded_rectangle([x - 46, cy - 38, x + 46, cy + 38], 18, outline=OUT, width=7)
        d.line([cx - sep + 46, cy - 6, cx + sep - 46, cy - 6], fill=OUT, width=7)


def _mouth(d, cx, cy, emotion, open_, wide=70):
    if open_:
        h = 52 if emotion in ("shocked", "happy") else 38
        if emotion == "shocked":
            d.ellipse([cx - 34, cy - 10, cx + 34, cy + h + 20], fill=(120, 20, 30, 255), outline=OUT, width=6)
        else:
            d.chord([cx - wide, cy - 22, cx + wide, cy + h + 10], 0, 180, fill=(120, 20, 30, 255), outline=OUT, width=6)
            d.chord([cx - wide + 22, cy + h - 18, cx + wide - 22, cy + h + 10], 180, 360, fill=(235, 90, 100, 255))
    else:
        if emotion == "happy":
            d.arc([cx - wide, cy - 40, cx + wide, cy + 30], 20, 160, fill=OUT, width=9)
        elif emotion == "sad":
            d.arc([cx - 50, cy + 4, cx + 50, cy + 60], 200, 340, fill=OUT, width=9)
        elif emotion == "shocked":
            d.ellipse([cx - 16, cy, cx + 16, cy + 30], fill=(120, 20, 30, 255), outline=OUT, width=5)
        elif emotion == "angry":
            d.line([cx - 50, cy + 18, cx + 50, cy + 10], fill=OUT, width=10)
        else:
            d.arc([cx - 50, cy - 20, cx + 50, cy + 24], 25, 155, fill=OUT, width=9)


def _body(d, color, skin, arms_up=False):
    # धड़ (कुर्ता / शर्ट)
    d.rounded_rectangle([130, 560, 510, 980], 110, fill=color, outline=OUT, width=8)
    d.line([320, 600, 320, 760], fill=_shade(color, 0.7), width=8)
    for y in (630, 680, 730):
        d.ellipse([310, y, 330, y + 20], fill="white", outline=OUT, width=3)
    # हाथ
    if arms_up:
        d.line([150, 640, 40, 470], fill=color, width=70)
        d.line([490, 640, 600, 470], fill=color, width=70)
        d.ellipse([5, 420, 85, 500], fill=skin, outline=OUT, width=6)
        d.ellipse([555, 420, 635, 500], fill=skin, outline=OUT, width=6)
    else:
        d.line([150, 640, 90, 860], fill=color, width=70)
        d.line([490, 640, 550, 860], fill=color, width=70)
        d.ellipse([50, 830, 130, 910], fill=skin, outline=OUT, width=6)
        d.ellipse([510, 830, 590, 910], fill=skin, outline=OUT, width=6)


def draw_wala(emotion="normal", mouth_open=False, cfg=None):
    cfg = cfg or {}
    skin = _hex(cfg.get("skin", "#C68642"))
    turban = _hex(cfg.get("turban", "#F57C00"))
    kurta = _hex(cfg.get("kurta", "#1565C0"))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _body(d, kurta, skin, arms_up=emotion in ("happy", "shocked"))
    # गमछा
    d.polygon([(190, 575), (450, 575), (380, 650), (260, 650)], fill=(230, 57, 70, 255), outline=OUT)
    # सिर
    d.ellipse([140, 150, 500, 600], fill=skin, outline=OUT, width=8)
    d.ellipse([118, 340, 168, 420], fill=skin, outline=OUT, width=6)
    d.ellipse([472, 340, 522, 420], fill=skin, outline=OUT, width=6)
    # पगड़ी
    d.ellipse([120, 60, 520, 330], fill=turban, outline=OUT, width=8)
    for i in range(4):
        d.arc([150 + i * 10, 120 + i * 30, 490 - i * 10, 330 + i * 8], 190, 350, fill=_shade(turban, 0.75), width=8)
    d.ellipse([290, 150, 350, 210], fill=(255, 215, 0, 255), outline=OUT, width=5)  # बिटकॉइन बैज
    d.line([313, 165, 313, 197], fill=OUT, width=5)
    d.arc([305, 163, 335, 182], 270, 90, fill=OUT, width=5)
    d.arc([305, 180, 338, 199], 270, 90, fill=OUT, width=5)
    _eyes(d, 320, 375, emotion)
    # नाक + मूँछ
    d.ellipse([295, 400, 345, 455], fill=_shade(skin, 0.85), outline=OUT, width=5)
    _mouth(d, 320, 505, emotion, mouth_open)
    d.chord([195, 440, 325, 510], 180, 360, fill=OUT)
    d.chord([315, 440, 445, 510], 180, 360, fill=OUT)
    d.ellipse([180, 455, 215, 490], fill=OUT)
    d.ellipse([425, 455, 460, 490], fill=OUT)
    return img


def draw_pappu(emotion="normal", mouth_open=False, cfg=None):
    cfg = cfg or {}
    skin = _hex(cfg.get("skin", "#E0AC69"))
    cap = _hex(cfg.get("cap", "#2E7D32"))
    shirt = _hex(cfg.get("shirt", "#FBC02D"))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _body(d, shirt, skin, arms_up=emotion == "shocked")
    d.ellipse([160, 200, 480, 610], fill=skin, outline=OUT, width=8)
    d.ellipse([136, 360, 186, 440], fill=skin, outline=OUT, width=6)
    d.ellipse([454, 360, 504, 440], fill=skin, outline=OUT, width=6)
    # उल्टी टोपी
    d.chord([160, 150, 480, 400], 180, 360, fill=cap, outline=OUT, width=8)
    d.rounded_rectangle([90, 250, 250, 290], 20, fill=_shade(cap, 0.8), outline=OUT, width=6)
    d.ellipse([305, 145, 335, 175], fill=_shade(cap, 0.7), outline=OUT, width=4)
    # बाल की लट
    d.arc([300, 260, 380, 330], 90, 270, fill=OUT, width=9)
    _eyes(d, 320, 400, emotion, sep=70, glasses=True)
    d.ellipse([302, 430, 338, 470], fill=_shade(skin, 0.85), outline=OUT, width=5)
    # बड़े दाँत वाला भोला मुँह
    _mouth(d, 320, 515, emotion, mouth_open, wide=60)
    if not mouth_open and emotion in ("normal", "happy"):
        d.rectangle([305, 520, 335, 545], fill="white", outline=OUT, width=4)
    return img


def draw_bijli(emotion="normal", mouth_open=False, cfg=None):
    skin = _hex("#D19A6A")
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _body(d, _hex("#6D4C41"), skin, arms_up=emotion == "angry")
    d.ellipse([150, 180, 490, 610], fill=skin, outline=OUT, width=8)
    # गंजा सिर + साइड बाल
    d.chord([150, 230, 230, 420], 90, 270, fill=(220, 220, 220, 255), outline=OUT, width=5)
    d.chord([410, 230, 490, 420], 270, 90, fill=(220, 220, 220, 255), outline=OUT, width=5)
    _eyes(d, 320, 390, emotion, sep=72, glasses=True)
    d.ellipse([298, 420, 342, 470], fill=_shade(skin, 0.85), outline=OUT, width=5)
    _mouth(d, 320, 520, emotion, mouth_open, wide=58)
    d.rectangle([220, 470, 420, 490], fill=(200, 200, 200, 255))  # सफ़ेद मूँछ
    # हाथ में बिल
    d.rectangle([440, 700, 600, 900], fill="white", outline=OUT, width=6)
    for y in range(730, 880, 28):
        d.line([460, y, 580, y], fill=(150, 150, 150, 255), width=6)
    d.text((470, 850), "BILL", fill=(200, 0, 0, 255))
    return img


DRAWERS = {"wala": draw_wala, "pappu": draw_pappu, "bijli": draw_bijli}


@lru_cache(maxsize=128)
def get_sprite(who, emotion, mouth_open, scale=1.0):
    emotion = emotion if emotion in EMOTIONS else "normal"
    img = DRAWERS.get(who, draw_wala)(emotion, mouth_open)
    if scale != 1.0:
        img = img.resize((int(W * scale), int(H * scale)), Image.LANCZOS)
    return img


if __name__ == "__main__":  # सभी एक्सप्रेशन की शीट बनाओ
    sheet = Image.new("RGB", (W * 5, H * 3), (240, 240, 240))
    for r, who in enumerate(DRAWERS):
        for c, e in enumerate(EMOTIONS):
            sheet.paste(get_sprite(who, e, c % 2 == 1), (c * W, r * H), get_sprite(who, e, c % 2 == 1))
    sheet.save("character_sheet.png")
    print("saved character_sheet.png")
