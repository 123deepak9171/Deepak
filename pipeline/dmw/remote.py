"""Download remote media (e.g. big phone videos uploaded as GitHub Release assets).

A timeline/music/logo "src" may be an https URL from an allowed host. It is downloaded
once into assets/_cache/ (gitignored) and replaced by the local path.
"""
from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from .config import ROOT, JobError, load_config

CACHE = ROOT / "assets" / "_cache"


def _download(url: str, cfg: dict, log=None) -> str:
    host = urlparse(url).hostname or ""
    allowed = cfg.get("remote_media", {}).get("allowed_hosts", [])
    if urlparse(url).scheme != "https" or host not in allowed:
        raise JobError(f"Remote media host allowed nahi hai: {host} (studio.config.json -> remote_media.allowed_hosts)")
    CACHE.mkdir(parents=True, exist_ok=True)
    name = Path(urlparse(url).path).name or "media"
    dest = CACHE / f"{hashlib.sha1(url.encode()).hexdigest()[:10]}_{name}"
    if dest.exists():
        return str(dest.relative_to(ROOT))
    limit = cfg["limits"]["max_input_mb"] * 1024 * 1024
    if log:
        log.say(f"  [Fetch] download: {url}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
        total = 0
        while chunk := r.read(1 << 20):
            total += len(chunk)
            if total > limit:
                tmp.unlink(missing_ok=True)
                raise JobError(f"File {cfg['limits']['max_input_mb']} MB limit se badi hai: {url}")
            f.write(chunk)
    tmp.replace(dest)
    return str(dest.relative_to(ROOT))


def resolve_remote(raw: dict, log=None) -> dict:
    cfg = load_config()

    def fix(d: dict, key: str = "src"):
        if isinstance(d, dict) and isinstance(d.get(key), str) and d[key].startswith(("http://", "https://")):
            d[key] = _download(d[key], cfg, log)

    for k in ("timeline", "clips", "images"):
        for it in raw.get(k, []) or []:
            fix(it)
            if it.get("greenscreen"):
                fix(it["greenscreen"], "background")
    for k in ("music", "logo"):
        fix(raw.get(k) or {})
    fix(raw.get("product_reveal") or {}, "image")
    for s in raw.get("sfx", []) or []:
        fix(s)
    return raw
