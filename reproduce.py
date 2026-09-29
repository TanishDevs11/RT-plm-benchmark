"""Regenerate every result in this repository from data/, reading no stored result.

Equivalent to `make reproduce`, provided because `make` is not available on every
platform and the Makefile could not be exercised on the machine these results were
produced on. Each stage is run as a subprocess so a failure names the stage that
failed rather than aborting silently.

    python reproduce.py            run everything
    python reproduce.py --quick    skip the two multi-hour stages

The heavy stages are the search-capacity null sweep and the embedding extraction.
Run them one at a time: extraction loads a 650M parameter model, and on a memory
constrained machine running stages in parallel will get them terminated.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

STAGES = [
    ("protocol tests, including the peeking positive control", ["bench/test_protocol.py"], False),
    ("search-null instrument self-check", ["bench/search_null.py", "--self-check"], False),
    ("leakage audit of the inherited tree", ["audit/leakage_audit.py"], False),
    ("metric properties at n=57", ["audit/metric_properties.py"], False),
    ("embedding extraction", ["bench/embeddings.py"], True),
    ("search-capacity null sweep", ["bench/search_null.py"], True),
    ("baseline ladder", ["bench/baselines.py"], False),
    ("representation benchmark", ["bench/representations.py"], False),
    ("scale projection", ["bench/scale_projection.py"], False),
]


def main():
    quick = "--quick" in sys.argv
    failures = []
    t0 = time.time()
    for name, args, heavy in STAGES:
        if quick and heavy:
            print(f"SKIP  {name} (heavy stage, --quick)")
            continue
        print(f"\n=== {name} ===", flush=True)
        t = time.time()
        proc = subprocess.run([sys.executable, "-u", *args], cwd=str(ROOT))
        status = "ok" if proc.returncode == 0 else f"exit {proc.returncode}"
        print(f"--- {name}: {status} in {time.time() - t:.1f}s", flush=True)
        if proc.returncode != 0:
            failures.append((name, proc.returncode))

    print(f"\ntotal {time.time() - t0:.1f}s")
    if failures:
        for name, code in failures:
            print(f"FAILED  {name} (exit {code})")
        return 1
    print("all stages completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
