"""Validate the Westminster Leningrad Codex bundle required by hb_align."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

REQUIRED_TOKEN_FIELDS = {
    "index",
    "hebrew",
    "translit",
    "ipa_modern",
    "ipa_ashkenazi",
    "ipa_sephardi",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wlc-root",
        type=Path,
        default=Path("resources/wlc"),
        help="Location of the normalized WLC bundle.",
    )
    parser.add_argument(
        "--checksums",
        type=Path,
        default=None,
        help="Optional explicit path to checksums.txt (defaults to <wlc-root>/checksums.txt)",
    )
    return parser.parse_args()


def load_checksums(path: Path) -> Dict[str, str]:
    entries: Dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            filename, digest = line.split()
        except ValueError as exc:  # pragma: no cover - defensive parsing
            raise ValueError(f"Malformed checksum entry: {line}") from exc
        entries[filename] = digest.lower()
    return entries


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_jsonl(path: Path) -> List[str]:
    errors: List[str] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path.name}:{line_no}: invalid JSON ({exc})")
                continue
            for field in ("book", "chapter", "verse", "tokens"):
                if field not in payload:
                    errors.append(f"{path.name}:{line_no}: missing '{field}' field")
            tokens = payload.get("tokens", [])
            if not isinstance(tokens, list):
                errors.append(f"{path.name}:{line_no}: 'tokens' must be a list")
                continue
            for token in tokens:
                missing = REQUIRED_TOKEN_FIELDS - token.keys()
                if missing:
                    errors.append(
                        f"{path.name}:{line_no}: token missing fields {sorted(missing)}"
                    )
    return errors


def main() -> int:
    args = parse_args()
    wlc_root: Path = args.wlc_root.expanduser().resolve()
    if not wlc_root.exists():
        print(f"WLC root not found: {wlc_root}", file=sys.stderr)
        return 2

    checksum_path = args.checksums or (wlc_root / "checksums.txt")
    if not checksum_path.exists():
        print(f"Checksum file missing: {checksum_path}", file=sys.stderr)
        return 2

    checksums = load_checksums(checksum_path)
    if not checksums:
        print("No checksum entries found.", file=sys.stderr)
        return 2

    all_errors: List[str] = []
    for relative_name, expected_digest in checksums.items():
        candidate = (wlc_root / relative_name).resolve()
        if not candidate.exists():
            all_errors.append(f"Missing file referenced in checksums: {relative_name}")
            continue
        actual = sha256sum(candidate)
        if actual.lower() != expected_digest:
            all_errors.append(
                f"Checksum mismatch for {relative_name}: expected {expected_digest}, got {actual}"
            )
        all_errors.extend(validate_jsonl(candidate))

    if all_errors:
        print("WLC validation failed:", file=sys.stderr)
        for error in all_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(checksums)} WLC JSONL file(s) in {wlc_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
