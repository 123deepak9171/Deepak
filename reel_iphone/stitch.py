"""reel_iphone/clips/*.mp4 (क्रम से) + endcard.mp4 → final_reel.mp4 (1080x1920, 30fps)"""
import subprocess
from pathlib import Path

D = Path(__file__).resolve().parent
clips = sorted((D / "clips").glob("*.mp4")) + [D / "endcard.mp4"]
inputs, chains = [], []
for i, c in enumerate(clips):
    inputs += ["-i", str(c)]
    chains.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,"
                  f"setsar=1,format=yuv420p[v{i}];"
                  f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo[a{i}]")
# जिन क्लिप में आवाज़ नहीं है, उनके लिए खामोश ऑडियो
def probe(c, args):
    return subprocess.run(["ffprobe", "-v", "error", *args, "-of", "csv=p=0", str(c)],
                          capture_output=True, text=True).stdout.strip()


for i, c in enumerate(clips):
    if not probe(c, ["-select_streams", "a", "-show_entries", "stream=index"]):
        dur = float(probe(c, ["-show_entries", "format=duration"]))
        chains[i] = chains[i].split(";")[0] + f";aevalsrc=0:c=stereo:s=44100:d={dur}[a{i}]"
fc = ";".join(chains) + ";" + "".join(f"[v{i}][a{i}]" for i in range(len(clips))) + \
    f"concat=n={len(clips)}:v=1:a=1[v][a]"
out = D / "final_reel.mp4"
subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", str(out)], check=True)
print(f"तैयार: {out}  ({len(clips) - 1} शॉट + एंड-कार्ड)")
