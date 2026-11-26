"""तैयार रील को भेजना/पोस्ट करना — दोनों तरीके फ्री।

Telegram (सबसे आसान): TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID
    → रोज़ वीडियो + कैप्शन आपके फ़ोन पर, बस Instagram पर शेयर कर दो (ट्रेंडिंग म्यूज़िक भी जोड़ सकते हो)।

Instagram ऑटो-पोस्ट (Meta Graph API, फ्री): IG_USER_ID + IG_ACCESS_TOKEN + PUBLIC_VIDEO_URL
    → अकाउंट Professional (Business/Creator) होना चाहिए और Facebook पेज से जुड़ा होना चाहिए।
"""
import os
import time

import requests

GRAPH = "https://graph.facebook.com/" + os.getenv("GRAPH_API_VERSION", "v21.0")


def send_telegram(video, caption):
    tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (tok and chat):
        return False
    with open(video, "rb") as f:
        r = requests.post(f"https://api.telegram.org/bot{tok}/sendVideo", timeout=300,
                          data={"chat_id": chat, "caption": caption[:1000], "supports_streaming": "true"},
                          files={"video": ("reel.mp4", f, "video/mp4")})
    r.raise_for_status()
    print("[post] Telegram पर भेज दिया ✔")
    return True


def post_instagram(caption):
    uid, tok, url = os.getenv("IG_USER_ID"), os.getenv("IG_ACCESS_TOKEN"), os.getenv("PUBLIC_VIDEO_URL")
    if not (uid and tok and url):
        return False
    r = requests.post(f"{GRAPH}/{uid}/media", timeout=60, data={
        "media_type": "REELS", "video_url": url, "caption": caption[:2200], "share_to_feed": "true",
        "access_token": tok})
    r.raise_for_status()
    cid = r.json()["id"]
    for _ in range(40):  # Instagram वीडियो प्रोसेस करता है, इंतज़ार
        st = requests.get(f"{GRAPH}/{cid}", params={"fields": "status_code", "access_token": tok}, timeout=30).json()
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram processing error: {st}")
        time.sleep(15)
    r = requests.post(f"{GRAPH}/{uid}/media_publish", data={"creation_id": cid, "access_token": tok}, timeout=60)
    r.raise_for_status()
    print(f"[post] Instagram पर रील पोस्ट हो गई ✔ id={r.json().get('id')}")
    return True


def publish(video, caption):
    done = False
    for fn, args in ((post_instagram, (caption,)), (send_telegram, (video, caption))):
        try:
            done = fn(*args) or done
        except Exception as e:  # noqa: BLE001
            print(f"[post] {fn.__name__} फेल: {e}")
    if not done:
        print("[post] कोई secret सेट नहीं — वीडियो GitHub Actions के 'Artifacts' से डाउनलोड करें।")


if __name__ == "__main__":  # python -m agent.poster output/2026-11-26
    import sys
    from pathlib import Path
    d = Path(sys.argv[1])
    publish(d / "reel.mp4", (d / "caption.txt").read_text(encoding="utf-8"))
