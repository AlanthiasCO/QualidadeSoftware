from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "results" / "paper_final"
CHECKSUMS = PACKAGE / "SHA256SUMS"


def main() -> int:
    failures: list[str] = []
    for raw_line in CHECKSUMS.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        expected, relative = line.split("  ", 1)
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing: {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            failures.append(f"mismatch: {relative}")
    if failures:
        raise SystemExit("checksum verification failed:\n" + "\n".join(failures))
    print("paper-final checksums: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
