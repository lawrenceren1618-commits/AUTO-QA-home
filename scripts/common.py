"""Shared labels and output paths for AutoQA writers."""

from __future__ import annotations

import re
from pathlib import Path

SITE_LABEL = {
    "US": "美国",
    "UK": "英国",
    "DE": "德国",
    "FR": "法国",
    "IT": "意大利",
    "ES": "西班牙",
    "CA": "加拿大",
    "IN": "印度",
    "MX": "墨西哥",
    "BR": "巴西",
    "AU": "澳洲",
    "AE": "阿联酋",
    "JP": "日本",
}

LANG_SHORT = {
    "en-US": "英",
    "en-GB": "英",
    "en-CA": "英",
    "en-AU": "英",
    "en-IN": "英",
    "en-AE": "英",
    "es-US": "西",
    "es-ES": "西",
    "es-MX": "西",
    "de-DE": "德",
    "fr-FR": "法",
    "it-IT": "意",
    "ja-JP": "日",
    "pt-BR": "葡",
    "ar": "阿",
}

_INVALID_DIR = re.compile(r'[<>:"/\\|?*]')


def product_dir_name(title: str) -> str:
    name = _INVALID_DIR.sub("", str(title or "").strip())
    name = " ".join(name.split())
    return name or "unnamed"


def ensure_in_product_output(path: Path, output_root: Path) -> Path:
    """Require output/{产品名}/{file} — one product folder under output/."""
    out = path.resolve()
    root = output_root.resolve()
    try:
        rel = out.relative_to(root)
    except ValueError:
        raise SystemExit(f"output must live under output/: {out}")
    if len(rel.parts) != 2:
        raise SystemExit(f"output must be output/{{产品名}}/{{file}}: {out}")
    return out

