#!/usr/bin/env python3
"""Validate AutoQA JSON before writing the vendor sheet."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ASIN_RE = re.compile(r"^B0[0-9A-Z]{8,10}$", re.I)
NUM_RE = re.compile(
    r"(?:^|[\n\r])\s*(?:[1-9][0-9]?[\.、\)]\s+|[(（][1-9][0-9]?[)）]\s+|①|②|③)"
)
LABEL_RE = re.compile(
    r"(问题|答案|Question\s*:|Answer\s*:|^\s*Q\s*:|^\s*A\s*:|Pregunta\s*:|Respuesta\s*:|FAQ\s*:)",
    re.I | re.M,
)
FORBIDDEN = [
    r"\bFDA approved\b",
    r"\bclinically proven\b",
    r"\b#1\b",
    r"\bnumber one\b",
    r"\bworld'?s best\b",
    r"100%\s*safe",
    r"100%\s*guaranteed",
]

MARKETPLACES = {
    "US", "UK", "DE", "FR", "IT", "ES", "CA", "IN", "MX", "BR", "AU", "AE", "JP",
}


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {"items": data}
    return data


def check_item(i: int, row: dict) -> list[str]:
    errs: list[str] = []
    prefix = f"items[{i}]"
    asin = str(row.get("asin") or "").strip().upper()
    mp = str(row.get("marketplace") or "").strip().upper()
    q = str(row.get("question") or "").strip()
    a = str(row.get("answer") or "").strip()

    if not ASIN_RE.match(asin):
        errs.append(f"{prefix}.asin invalid: {asin!r}")
    if mp not in MARKETPLACES:
        errs.append(f"{prefix}.marketplace invalid: {mp!r}")
    if not q:
        errs.append(f"{prefix}.question empty")
    if not a:
        errs.append(f"{prefix}.answer empty")
    if len(q) > 200:
        errs.append(f"{prefix}.question too long ({len(q)} > 200)")
    words = len(a.split())
    if words > 80:
        errs.append(f"{prefix}.answer too long ({words} words > 80)")
    sentences = [s for s in re.split(r"[.!?。？！]+", a) if s.strip()]
    if len(sentences) > 3:
        errs.append(f"{prefix}.answer has {len(sentences)} sentences (max 3)")
    for field, text in (("question", q), ("answer", a)):
        if NUM_RE.search(text):
            errs.append(f"{prefix}.{field} has numbering")
        if LABEL_RE.search(text):
            errs.append(f"{prefix}.{field} has Q/A label words")
        for pat in FORBIDDEN:
            if re.search(pat, text, re.I):
                errs.append(f"{prefix}.{field} forbidden phrase /{pat}/")
    lang = str(row.get("language") or "")
    if "?" not in q and "？" not in q:
        errs.append(f"{prefix}.question missing ?")
    if lang.startswith("es") and q.startswith(("¿",)) is False and "¿" not in q[:2]:
        if re.match(r"^[A-ZÁÉÍÓÚÑ¿]", q) and not q.startswith("¿"):
            errs.append(f"{prefix}.question Spanish missing ¿")
    if re.search(r"\bdishwasher\b|\blavavajillas\b", q + " " + a, re.I):
        errs.append(f"{prefix} mentions dishwasher (use care wording)")
    if re.search(
        r"\bmessage us\b|\bcontact us\b|\bwe'll\b|\bwe will\b|\bour store\b|联系我们|我们会处理|contáctanos|escríbenos",
        q + " " + a,
        re.I,
    ):
        errs.append(f"{prefix} sounds like the seller, not a third-party buyer")
    if re.search(r"^(Same |Vintage-style mix|Thick glass and)", a):
        errs.append(f"{prefix}.answer looks like a sentence fragment")
    stuffed = re.findall(r"\bbud vases\b", q, re.I)
    if len(stuffed) >= 2:
        errs.append(f"{prefix}.question repeats 'bud vases'")
    return errs


def check_zh(i: int, row: dict) -> list[str]:
    prefix = f"items[{i}]"
    errs: list[str] = []
    if not str(row.get("question_zh") or "").strip():
        errs.append(f"{prefix}.question_zh empty")
    if not str(row.get("answer_zh") or "").strip():
        errs.append(f"{prefix}.answer_zh empty")
    return errs


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("json_path")
    p.add_argument("--min", type=int, default=1, help="min rows per ASIN")
    p.add_argument("--max", type=int, default=40, help="max rows per ASIN")
    p.add_argument("--total-min", type=int, default=30)
    p.add_argument("--total-max", type=int, default=45)
    p.add_argument("--require-zh", action="store_true", help="require question_zh/answer_zh")
    args = p.parse_args()
    path = Path(args.json_path)
    data = load(path)
    items = data.get("items") or []
    errs: list[str] = []
    if not items:
        errs.append("no items")
    n = len(items)
    if n < args.total_min or n > args.total_max:
        errs.append(f"total {n} not in {args.total_min}-{args.total_max}")
    by_asin: dict[tuple[str, str], int] = {}
    for i, row in enumerate(items):
        errs.extend(check_item(i, row))
        if args.require_zh:
            errs.extend(check_zh(i, row))
        key = (
            str(row.get("asin") or "").upper(),
            str(row.get("marketplace") or "").upper(),
        )
        by_asin[key] = by_asin.get(key, 0) + 1
    for key, n in by_asin.items():
        if n < args.min or n > args.max:
            errs.append(f"{key} count {n} not in {args.min}-{args.max}")
    if errs:
        print("FAIL")
        for e in errs:
            print("-", e)
        return 1
    print(f"OK {len(items)} rows, {len(by_asin)} ASIN-marketplace groups")
    return 0


if __name__ == "__main__":
    sys.exit(main())
