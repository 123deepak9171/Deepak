"""Generates small, synthetic (copyright-free) demo assets with FFmpeg only."""
from __future__ import annotations

import json
from pathlib import Path

from . import ff
from .config import ROOT

DEMO = ROOT / "assets" / "demo"
FONT = ROOT / "assets" / "fonts" / "Poppins-ExtraBold.ttf"


def make_assets(log=None) -> dict:
    DEMO.mkdir(parents=True, exist_ok=True)
    sfx_dir = ROOT / "assets" / "sfx"
    sfx_dir.mkdir(parents=True, exist_ok=True)
    p = {k: DEMO / v for k, v in {
        "talk": "talking_head.mp4", "green": "greenscreen.mp4", "bg": "mine_background.jpg",
        "photo": "product_photo.jpg", "logo": "dmw_logo.png", "music": "demo_music.mp3",
        "script": "script.txt"}.items()}
    p["whoosh"] = sfx_dir / "whoosh.wav"
    # 1) "Talking" clip: 10s test pattern; tone with 2 silent gaps (to test silence removal)
    ff.ffmpeg(["-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=10",
               "-f", "lavfi", "-i", "sine=f=220:r=48000:d=10",
               "-filter_complex", "[1:a]volume='if(between(t,2.5,4)+between(t,6.5,7.5),0,0.5)':eval=frame,"
               "tremolo=f=4:d=0.6[a];[0:v]drawtext=fontfile=" + str(FONT) + ":text='DEMO CLIP':fontsize=64:"
               "fontcolor=white:box=1:boxcolor=black@0.5:x=(w-tw)/2:y=h-120[v]",
               "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", p["talk"]], log=log)
    # 2) Green screen clip: moving orange "subject" on pure green
    ff.ffmpeg(["-f", "lavfi", "-i", "color=c=0x00FF00:s=1280x720:r=30:d=4",
               "-f", "lavfi", "-i", "color=c=0xFF6B1A:s=320x420:r=30:d=4",
               "-f", "lavfi", "-i", "sine=f=330:r=48000:d=4",
               "-filter_complex", "[0][1]overlay=x='300+t*120':y=200,"
               "drawtext=fontfile=" + str(FONT) + ":text='GREEN SCREEN':fontsize=56:fontcolor=white:x=(w-tw)/2:y=80[v]",
               "-map", "[v]", "-map", "2:a", "-af", "volume=0.4", "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-shortest", p["green"]], log=log)
    # 3) Background + product photo
    ff.ffmpeg(["-f", "lavfi", "-i", "gradients=s=1920x1080:c0=0x3B2A1A:c1=0xC08040:x0=0:y0=0:x1=1920:y1=1080:d=1",
               "-frames:v", "1", p["bg"]], log=log)
    ff.ffmpeg(["-f", "lavfi", "-i", "mandelbrot=s=1600x1200", "-frames:v", "1",
               "-vf", "drawtext=fontfile=" + str(FONT) + ":text='PRODUCT':fontsize=120:fontcolor=white:x=(w-tw)/2:y=h-200",
               p["photo"]], log=log)
    # 4) Logo (transparent PNG)
    ff.ffmpeg(["-f", "lavfi", "-i", "color=c=black@0.0:s=600x600,format=rgba", "-frames:v", "1",
               "-vf", "geq=r='245':g='166':b='35':a='255*lte(hypot(X-300,Y-300),280)*gte(hypot(X-300,Y-300),240)',"
               "drawtext=fontfile=" + str(FONT) + ":text='DMW':fontsize=190:fontcolor=0xF5A623:x=(w-tw)/2:y=(h-th)/2",
               p["logo"]], log=log)
    # 5) Royalty-free synthetic music (chord + beat) and whoosh SFX
    ff.ffmpeg(["-f", "lavfi", "-i", "sine=f=110:r=48000:d=40", "-f", "lavfi", "-i", "sine=f=164.8:r=48000:d=40",
               "-f", "lavfi", "-i", "sine=f=220:r=48000:d=40",
               "-filter_complex", "[0][1][2]amix=inputs=3,tremolo=f=2:d=0.8,volume=0.8[a]", "-map", "[a]",
               "-c:a", "libmp3lame", "-b:a", "128k", p["music"]], log=log)
    ff.ffmpeg(["-f", "lavfi", "-i", "anoisesrc=d=0.6:c=pink:r=48000:a=0.6",
               "-af", "highpass=f=300,lowpass=f=4000,afade=t=in:d=0.25,afade=t=out:st=0.3:d=0.3",
               "-ac", "2", p["whoosh"]], log=log)
    p["script"].write_text("Ram Ram bhai log! Aaj hum dekhenge DESI MINING WALA ka naya crusher. "
                           "Ye machine ghani powerful sai. Video poora dekho aur channel subscribe karo!", encoding="utf-8")
    return {k: str(v.relative_to(ROOT)) for k, v in p.items()}


def demo_job(a: dict, aspect: str = "9:16") -> dict:
    return {
        "id": f"demo-{aspect.replace(':', 'x')}",
        "title": "DMW Demo",
        "instructions": "Ek energetic reel banao, silence hatao, captions lagao, music aur logo ke saath. 20 sec.",
        "aspect": aspect,
        "style": "energetic",
        "target_duration": 22,
        "logo": {"src": a["logo"], "intro": True, "outro": True, "watermark": True,
                 "intro_duration": 2.5, "outro_duration": 2.5},
        "product_reveal": {"enabled": True, "title": "DMW CRUSHER X1", "subtitle": "Ghana Powerful!",
                           "image": a["photo"], "price": "₹ Best Price", "duration": 3, "position": "start"},
        "timeline": [
            {"type": "video", "src": a["talk"]},
            {"type": "video", "src": a["green"], "remove_silence": False,
             "greenscreen": {"background": a["bg"]}},
            {"type": "image", "src": a["photo"], "duration": 2.5, "animation": "zoom-in"},
        ],
        "captions": {"enabled": True, "source": "script", "script": a["script"], "language": "hi"},
        "music": {"enabled": True, "src": a["music"]},
        # Demo is synthetic (no private media) -> safe to publish as a Release for a direct MP4 link
        "export": {"publish_release": True},
    }


def write_demo_job(aspect: str = "9:16", log=None) -> Path:
    a = make_assets(log)
    job = demo_job(a, aspect)
    jobs = ROOT / "jobs"
    jobs.mkdir(exist_ok=True)
    path = jobs / f"{job['id']}.json"
    path.write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
