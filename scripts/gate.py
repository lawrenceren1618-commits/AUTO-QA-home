#!/usr/bin/env python3
"""Phase gates and .autoqa_state.json for mandatory AutoQA pipeline."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_FILE = ".autoqa_state.json"
PHASES = ("0", "1", "2", "3", "4", "5", "5b", "6")
PHASE_LABELS = {
    "0": "env",
    "1": "dossier",
    "2": "gists",
    "3": "screened",
    "4": "draft",
    "5": "dedupe",
    "5b": "language_pass",
    "6": "deliver",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _phase_index(phase: str) -> int:
    try:
        return PHASES.index(phase)
    except ValueError:
        raise SystemExit(f"unknown phase {phase!r}; expected one of {PHASES}")


def product_dir_from_path(path: Path, output_root: Path) -> Path:
    resolved = path.resolve()
    root = output_root.resolve()
    try:
        rel = resolved.relative_to(root)
    except ValueError as e:
        raise SystemExit(f"path must be under output/: {resolved}") from e
    if len(rel.parts) < 2:
        raise SystemExit(f"path must be output/{{产品名}}/{{file}}: {resolved}")
    return root / rel.parts[0]


def state_path(product_dir: Path) -> Path:
    return product_dir / STATE_FILE


def load_state(product_dir: Path) -> dict[str, Any]:
    p = state_path(product_dir)
    if not p.is_file():
        raise SystemExit(
            f"missing {STATE_FILE} in {product_dir}. Run: python scripts/run_autoqa.py init --title ... --batch ..."
        )
    return json.loads(p.read_text(encoding="utf-8"))


def save_state(product_dir: Path, state: dict[str, Any]) -> None:
    product_dir.mkdir(parents=True, exist_ok=True)
    state_path(product_dir).write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def new_state(*, title: str, batch: str) -> dict[str, Any]:
    return {
        "version": 1,
        "title": title,
        "batch": batch,
        "phase": "0",
        "phase_history": [{"phase": "0", "at": _now(), "note": "init"}],
        "validation": {"passed": False, "qa_json": None, "at": None},
        "deliver": {"xlsx": None, "docx": None, "at": None},
    }


def _dossier_files(product_dir: Path) -> list[Path]:
    d = product_dir / "dossiers"
    if not d.is_dir():
        return []
    return sorted(p for p in d.glob("*.json") if p.is_file())


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _gists_path(product_dir: Path) -> Path:
    return product_dir / "gists.json"


def _screened_path(product_dir: Path) -> Path:
    return product_dir / "screened.json"


def qa_json_path(product_dir: Path, state: dict[str, Any]) -> Path:
    batch = str(state.get("batch") or "").strip()
    if not batch:
        raise SystemExit("state.batch empty")
    return product_dir / f"{batch}_qa.json"


def artifact_errors(product_dir: Path, state: dict[str, Any], target_phase: str) -> list[str]:
    """Errors that block entering target_phase (phase 1 = env done, no dossier yet)."""
    errs: list[str] = []
    idx = _phase_index(target_phase)

    if idx >= _phase_index("2"):
        dossiers = _dossier_files(product_dir)
        if not dossiers:
            errs.append("Phase 1→2: need at least one dossiers/*.json (MCP listing archive)")

    if idx >= _phase_index("3"):
        gp = _gists_path(product_dir)
        if not gp.is_file():
            errs.append("Phase 2→3: missing gists.json")
        else:
            data = _read_json(gp)
            items = data if isinstance(data, list) else data.get("gists") or data.get("items") or []
            if not items:
                errs.append("Phase 2→3: gists.json has no gist rows")

    if idx >= _phase_index("4"):
        sp = _screened_path(product_dir)
        if not sp.is_file():
            errs.append("Phase 3→4: missing screened.json")
        else:
            data = _read_json(sp)
            items = data if isinstance(data, list) else data.get("items") or data.get("gists") or []
            kept = [x for x in items if x.get("keep") is not False]
            n = len(kept)
            if n < 30 or n > 45:
                errs.append(f"Phase 3→4: screened keep count {n} not in 30-45")

    if idx >= _phase_index("5"):
        qjp = qa_json_path(product_dir, state)
        if not qjp.is_file():
            errs.append(f"Phase 4→5: missing {qjp.name}")

    if idx >= _phase_index("5b"):
        qjp = qa_json_path(product_dir, state)
        if not qjp.is_file():
            errs.append(f"Phase 5→5b: missing {qjp.name}")
        v = state.get("validation") or {}
        if not v.get("passed"):
            errs.append("Phase 5b: validation not passed — run run_autoqa.py deliver")
        elif v.get("qa_json") and Path(v["qa_json"]).resolve() != qjp.resolve():
            errs.append("Phase 5b: validation is for a different qa json; re-run deliver")

    if idx >= _phase_index("6"):
        d = state.get("deliver") or {}
        if not d.get("xlsx") or not d.get("docx"):
            errs.append("Phase 6: deliver outputs not recorded")

    return errs


def pre_deliver_errors(product_dir: Path, state: dict[str, Any]) -> list[str]:
    """All creative/screening artifacts required before validate + write."""
    errs: list[str] = []
    for target in ("2", "3", "4", "5"):
        errs.extend(artifact_errors(product_dir, state, target))
    return errs


def require_phase_at_least(product_dir: Path, minimum: str) -> dict[str, Any]:
    state = load_state(product_dir)
    cur = str(state.get("phase") or "0")
    if _phase_index(cur) < _phase_index(minimum):
        raise SystemExit(
            f"pipeline at phase {cur} ({PHASE_LABELS.get(cur, cur)}), need >= {minimum} ({PHASE_LABELS.get(minimum, minimum)}). "
            f"Run: python scripts/run_autoqa.py status --product-dir {product_dir}"
        )
    return state


def mark_phase(product_dir: Path, target_phase: str, *, note: str = "") -> dict[str, Any]:
    if target_phase not in PHASES:
        raise SystemExit(f"invalid phase {target_phase!r}")
    state = load_state(product_dir)
    cur = str(state.get("phase") or "0")
    if _phase_index(target_phase) <= _phase_index(cur):
        return state
    if _phase_index(target_phase) != _phase_index(cur) + 1:
        raise SystemExit(
            f"cannot skip phases: current {cur}, requested {target_phase}. Advance one phase at a time."
        )
    errs = artifact_errors(product_dir, state, target_phase)
    if errs:
        raise SystemExit("gate blocked:\n- " + "\n- ".join(errs))
    state["phase"] = target_phase
    hist = state.setdefault("phase_history", [])
    hist.append({"phase": target_phase, "at": _now(), "note": note or PHASE_LABELS.get(target_phase, "")})
    save_state(product_dir, state)
    return state


def try_advance(product_dir: Path) -> tuple[str, str | None]:
    """If artifacts for next phase are ready, advance. Returns (phase, message)."""
    state = load_state(product_dir)
    cur = str(state.get("phase") or "0")
    i = _phase_index(cur)
    if i >= len(PHASES) - 1:
        return cur, "already at final phase"
    nxt = PHASES[i + 1]
    errs = artifact_errors(product_dir, state, nxt)
    if errs:
        return cur, "blocked: " + "; ".join(errs)
    state["phase"] = nxt
    state.setdefault("phase_history", []).append(
        {"phase": nxt, "at": _now(), "note": f"auto-advance to {PHASE_LABELS.get(nxt, nxt)}"}
    )
    save_state(product_dir, state)
    return nxt, f"advanced to phase {nxt} ({PHASE_LABELS.get(nxt, nxt)})"


def record_validation(product_dir: Path, qa_json: Path, *, passed: bool) -> None:
    state = load_state(product_dir)
    state["validation"] = {
        "passed": passed,
        "qa_json": str(qa_json.resolve()),
        "at": _now(),
    }
    if passed:
        state["phase"] = "5b"
        state.setdefault("phase_history", []).append(
            {"phase": "5b", "at": _now(), "note": "validate_qa OK"}
        )
    save_state(product_dir, state)


def record_deliver(product_dir: Path, *, xlsx: Path, docx: Path) -> None:
    state = load_state(product_dir)
    state["deliver"] = {
        "xlsx": str(xlsx.resolve()),
        "docx": str(docx.resolve()),
        "at": _now(),
    }
    state["phase"] = "6"
    state.setdefault("phase_history", []).append(
        {"phase": "6", "at": _now(), "note": "xlsx + docx written"}
    )
    save_state(product_dir, state)


def assert_can_deliver(product_dir: Path, qa_json: Path) -> dict[str, Any]:
    """Hard gate before write_qa_sheet / write_review_docx."""
    state = load_state(product_dir)
    errs = pre_deliver_errors(product_dir, state)
    if errs:
        raise SystemExit(
            "deliver blocked:\n- " + "\n- ".join(errs) + "\n"
            "Use run_autoqa.py deliver, not direct write_* scripts."
        )
    expected = qa_json_path(product_dir, state)
    if qa_json.resolve() != expected.resolve():
        raise SystemExit(
            f"qa json must be {expected.name} for this batch; got {qa_json.name}"
        )
    v = state.get("validation") or {}
    if not v.get("passed"):
        raise SystemExit(
            "deliver blocked: validation not passed. Run:\n"
            f"  python scripts/run_autoqa.py deliver --qa-json {qa_json}"
        )
    if v.get("qa_json") and Path(v["qa_json"]).resolve() != qa_json.resolve():
        raise SystemExit("deliver blocked: stale validation for another file; re-run deliver")
    return state


def format_status(product_dir: Path) -> str:
    state = load_state(product_dir)
    cur = str(state.get("phase") or "0")
    lines = [
        f"product_dir: {product_dir}",
        f"title: {state.get('title')}",
        f"batch: {state.get('batch')}",
        f"phase: {cur} ({PHASE_LABELS.get(cur, cur)})",
        f"dossiers: {len(_dossier_files(product_dir))}",
        f"gists.json: {_gists_path(product_dir).is_file()}",
        f"screened.json: {_screened_path(product_dir).is_file()}",
        f"qa.json: {qa_json_path(product_dir, state).is_file()}",
        f"validation.passed: {(state.get('validation') or {}).get('passed')}",
    ]
    nxt_i = _phase_index(cur) + 1
    if nxt_i < len(PHASES):
        nxt = PHASES[nxt_i]
        errs = artifact_errors(product_dir, state, nxt)
        if errs:
            lines.append(f"next ({nxt}): BLOCKED")
            lines.extend(f"  - {e}" for e in errs)
        else:
            lines.append(f"next ({nxt}): ready — run advance")
    return "\n".join(lines)
