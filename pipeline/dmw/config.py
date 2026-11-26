"""Config loading, path safety and job validation."""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "studio.config.json"

ALLOWED_MEDIA = {
    "video": {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi", ".3gp"},
    "image": {".jpg", ".jpeg", ".png", ".webp", ".bmp"},
    "audio": {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus"},
    "text": {".txt", ".srt", ".vtt", ".md"},
    "lut": {".cube"},
}


class JobError(ValueError):
    """Raised when a job file is invalid or unsafe."""


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def safe_path(rel: str | None, kind: str | None = None, must_exist: bool = True) -> Path | None:
    """Resolve a repo-relative path and refuse anything outside the repository."""
    if not rel:
        return None
    p = (ROOT / rel).resolve() if not os.path.isabs(rel) else Path(rel).resolve()
    if ROOT not in p.parents and p != ROOT:
        raise JobError(f"Path repo ke bahar hai (unsafe): {rel}")
    if kind and p.suffix.lower() not in ALLOWED_MEDIA[kind]:
        raise JobError(f"'{rel}' ka extension {kind} ke liye allowed nahi hai")
    if must_exist and not p.exists():
        raise JobError(f"File nahi mili: {rel}")
    return p


def rel(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip()).strip("-").lower()
    return s[:60] or "job"


def check_disk(cfg: dict, where: Path) -> None:
    need = cfg["limits"]["min_free_disk_gb"] * 1024**3
    free = shutil.disk_usage(where).free
    if free < need:
        raise JobError(f"Disk space kam hai: {free/1024**3:.1f} GB free, {cfg['limits']['min_free_disk_gb']} GB chahiye")


def hex_to_ass(color: str, alpha: int = 0) -> str:
    c = color.lstrip("#")
    r, g, b = c[0:2], c[2:4], c[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()
