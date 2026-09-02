#!/usr/bin/env python3
"""Single entrypoint: init pipeline state, advance phases, deliver with hard gates."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common import product_dir_name
from gate import (
    PHASE_LABELS,
    artifact_errors,
    format_status,
    load_state,
    mark_phase,
    new_state,
    pre_deliver_errors,
    product_dir_from_path,
    qa_json_path,
    record_deliver,
    record_validation,
    save_state,
    try_advance,
    _gists_path,
    _screened_path,
)


def _run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, cwd=str(ROOT)).returncode


def cmd_init(args: argparse.Namespace) -> int:
    title = args.title.strip()
    batch = args.batch.strip()
    if not title or not batch:
        print("need --title and --batch", file=sys.stderr)
        return 1
    product_dir = ROOT / "output" / product_dir_name(title)
    product_dir.mkdir(parents=True, exist_ok=True)
    (product_dir / "dossiers").mkdir(exist_ok=True)

    state = new_state(title=title, batch=batch)
    save_state(product_dir, state)
    print(f"init {product_dir}")

    if args.skip_env:
        mark_phase(product_dir, "1", note="skip env check")
        print(format_status(product_dir))
        return 0

    rc = _run([sys.executable, str(ROOT / "scripts" / "check_env.py")])
    if rc != 0:
        print("Phase 0 failed: fix env/.env and Windows user env vars", file=sys.stderr)
        return rc
    mark_phase(product_dir, "1", note="check_env OK")
    print(format_status(product_dir))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    product_dir = Path(args.product_dir)
    if not product_dir.is_dir():
        print(f"not a directory: {product_dir}", file=sys.stderr)
        return 1
    print(format_status(product_dir))
    return 0


def cmd_advance(args: argparse.Namespace) -> int:
    product_dir = Path(args.product_dir)
    if args.phase:
        mark_phase(product_dir, args.phase, note="manual mark")
        print(format_status(product_dir))
        return 0
    phase, msg = try_advance(product_dir)
    print(msg)
    print(format_status(product_dir))
    return 0 if "advanced" in msg or "already" in msg else 1


def cmd_deliver(args: argparse.Namespace) -> int:
    qa_json = Path(args.qa_json).resolve()
    if not qa_json.is_file():
        print(f"missing {qa_json}", file=sys.stderr)
        return 1
    product_dir = product_dir_from_path(qa_json, ROOT / "output")
    state = load_state(product_dir)

    errs = pre_deliver_errors(product_dir, state)
    if errs:
        print("deliver blocked:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        print(
            "\nComplete pipeline artifacts first, or for legacy batches:\n"
            f"  python scripts/run_autoqa.py bootstrap-legacy --qa-json {qa_json}",
            file=sys.stderr,
        )
        return 1

    expected = qa_json_path(product_dir, state)
    if qa_json != expected.resolve():
        print(f"qa json must be {expected}", file=sys.stderr)
        return 1

    rc = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_qa.py"),
            str(qa_json),
            "--require-zh",
        ]
    )
    record_validation(product_dir, qa_json, passed=(rc == 0))
    if rc != 0:
        print("validation failed; deliver aborted", file=sys.stderr)
        return rc

    batch = str(state.get("batch") or qa_json.stem.replace("_qa", ""))
    xlsx = product_dir / f"{batch}_qa.xlsx"
    docx = product_dir / f"{batch}_qa_review.docx"

    rc = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "write_qa_sheet.py"),
            "--input",
            str(qa_json),
            "--output",
            str(xlsx),
            "--gate-ok",
        ]
    )
    if rc != 0:
        return rc
    rc = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "write_review_docx.py"),
            "--input",
            str(qa_json),
            "--output",
            str(docx),
            "--gate-ok",
        ]
    )
    if rc != 0:
        return rc

    record_deliver(product_dir, xlsx=xlsx, docx=docx)
    print(format_status(product_dir))
    print(f"\nDelivered:\n  {xlsx}\n  {docx}")
    return 0


def cmd_bootstrap_legacy(args: argparse.Namespace) -> int:
    """One-time backfill for batches created before gate system."""
    qa_json = Path(args.qa_json).resolve()
    if not qa_json.is_file():
        print(f"missing {qa_json}", file=sys.stderr)
        return 1
    data = json.loads(qa_json.read_text(encoding="utf-8"))
    items = data.get("items") or []
    if not items:
        print("no items in qa json", file=sys.stderr)
        return 1

    product_dir = product_dir_from_path(qa_json, ROOT / "output")
    title = str(data.get("title") or product_dir.name)
    batch = args.batch or qa_json.stem.replace("_qa", "")

    (product_dir / "dossiers").mkdir(parents=True, exist_ok=True)
    asins = sorted({str(r.get("asin") or "").upper() for r in items if r.get("asin")})
    mp = str(items[0].get("marketplace") or "US").upper()
    for asin in asins:
        dp = product_dir / "dossiers" / f"{asin}_{mp}.json"
        if not dp.is_file():
            dp.write_text(
                json.dumps(
                    {
                        "asin": asin,
                        "marketplace": mp,
                        "sources_used": ["legacy_bootstrap"],
                        "gaps": ["legacy_bootstrap_no_mcp_archive"],
                        "listing": {"title": title},
                        "pain_points": [],
                        "gists": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

    gists = []
    for r in items:
        gists.append(
            {
                "asin": r.get("asin"),
                "intent": r.get("note") or "legacy",
                "question_gist": r.get("question_zh") or r.get("question"),
                "answer_facts": [r.get("answer_zh") or r.get("answer")],
                "keep": True,
                "drop_reason": None,
            }
        )
    _gists_path(product_dir).write_text(
        json.dumps({"gists": gists}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    screened = []
    for r in items:
        screened.append({**r, "keep": True, "screen_scores": {"legacy": True}})
    _screened_path(product_dir).write_text(
        json.dumps({"items": screened, "keep_count": len(screened)}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    state = new_state(title=title, batch=batch)
    for ph in ("1", "2", "3", "4", "5"):
        state["phase"] = ph
    save_state(product_dir, state)
    print(f"bootstrap-legacy OK for {product_dir} ({len(items)} rows)")
    print("Next: python scripts/run_autoqa.py deliver --qa-json", qa_json)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="AutoQA pipeline orchestrator (mandatory path)")
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init", help="create output/{产品名}/ and Phase 0→1")
    i.add_argument("--title", required=True, help="product name / JSON title")
    i.add_argument("--batch", required=True, help="file prefix e.g. ASHEWIG_US")
    i.add_argument("--skip-env", action="store_true", help="skip check_env (not recommended)")
    i.set_defaults(func=cmd_init)

    s = sub.add_parser("status", help="show phase and blockers")
    s.add_argument("--product-dir", required=True)
    s.set_defaults(func=cmd_status)

    a = sub.add_parser("advance", help="advance one phase if artifacts ready")
    a.add_argument("--product-dir", required=True)
    a.add_argument("--phase", choices=list(PHASE_LABELS.keys()), help="manual mark (expert)")
    a.set_defaults(func=cmd_advance)

    d = sub.add_parser("deliver", help="validate + write xlsx + docx (Phase 5b→6)")
    d.add_argument("--qa-json", required=True)
    d.set_defaults(func=cmd_deliver)

    b = sub.add_parser("bootstrap-legacy", help="backfill gates for pre-gate batches")
    b.add_argument("--qa-json", required=True)
    b.add_argument("--batch", help="override batch id")
    b.set_defaults(func=cmd_bootstrap_legacy)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
