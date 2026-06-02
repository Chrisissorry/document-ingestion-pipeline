from __future__ import annotations

import json
import sys

from .graph import run


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: python -m ingest <pdf-path>", file=sys.stderr)
        return 2
    result = run(argv[0])
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0
