#!/usr/bin/env python3
"""Execute a Jupyter notebook in GitHub Actions.

Pass --market india or --market usa. Colab-only publishing cells are skipped,
while the actual scanner cells are retained. The hourly scan cell is explicitly
protected so it cannot be mistaken for a publishing cell.
"""

import argparse
import os
import re
import sys
import traceback
from pathlib import Path

import nbformat
from nbclient import NotebookClient


# Skip cells whose primary purpose is publishing/authentication/automation.
# Do NOT broadly skip a cell just because it mentions Google/Colab.
SKIP_PATTERNS = [
    r"^\s*#\s*PUBLISH\s*[—-]",
    r"^\s*#\s*PUBLISH\b",
    r"^\s*#\s*SAVE TO GOOGLE DRIVE\b",
    r"^\s*#\s*AUTOMATION:\s*SKIP\b",
]

# The actual scanner invocation must always be retained.
FORCE_RUN_PATTERNS = [
    r"^\s*#\s*CELL\s*8\s*[—-]\s*RUN HOURLY SCANS\b",
    r"run_hourly_scans\s*\(",
]


def first_nonempty_line(source):
    for line in source.splitlines():
        if line.strip():
            return line.strip()
    return ""


def is_force_run_cell(source):
    return any(re.search(p, source, re.I | re.M) for p in FORCE_RUN_PATTERNS)

def should_skip(source, idx=None):
    if is_force_run_cell(source):
        return False

    # Explicitly skip cell 9 and cell 10
    if idx in ( 25,30):
        return True

    # Remove the old standalone keep-alive reference.
    if first_nonempty_line(source).lower() == "colab_keepalive.ipynb":
        return True

    # Explicit publish/automation cells only.
    return any(re.search(p, source, re.I | re.M) for p in SKIP_PATTERNS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("notebook")
    ap.add_argument(
        "--market",
        choices=("india", "usa"),
        default="usa",
        help="india=Nifty 500 only; usa=S&P 500 + Russell 2000",
    )
    ap.add_argument("--max-cell", type=int, default=None)
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()

    os.environ["SCAN_MARKET"] = args.market

    nb_path = Path(args.notebook)
    if not nb_path.is_file():
        print(f"[runner] ERROR: notebook not found: {nb_path}", file=sys.stderr)
        sys.exit(2)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"[runner] Notebook : {nb_path}")
    print(f"[runner] Market   : {args.market}")
    print(f"[runner] Outdir   : {outdir}")

    nb = nbformat.read(str(nb_path), as_version=4)

    selected = []
    skipped = []

    for idx, cell in enumerate(nb.cells):
        if args.max_cell is not None and idx > args.max_cell:
            continue
        if cell.cell_type != "code":
            continue

        source = cell.source or ""

        if should_skip(source, idx=idx):
            skipped.append(idx)
            print(f"[runner] SKIP original cell {idx}: Colab/publishing-only")
        else:
            selected.append((idx, cell))

    print("\n[runner] Cells selected for execution:")
    print("  " + ", ".join(str(i) for i, _ in selected))

    # Original notebook Cell 8 is the actual hourly scan invocation.
    if len(nb.cells) > 8:
        if any(i == 8 for i, _ in selected):
            print("[runner] OK: original Cell 8 WILL RUN.")
        else:
            print("[runner] ERROR: original Cell 8 was excluded.", file=sys.stderr)
            sys.exit(3)

    run_nb = nbformat.v4.new_notebook(
        metadata=nb.metadata,
        cells=[cell for _, cell in selected],
    )

    client = NotebookClient(
        run_nb,
        timeout=60 * 60 * 3,
        kernel_name="python3",
        resources={"metadata": {"path": str(Path.cwd())}},
        allow_errors=False,
    )

    try:
        client.execute()
    except Exception:
        print("\n[runner] NOTEBOOK EXECUTION FAILED", file=sys.stderr)
        traceback.print_exc()

        executed = outdir / (nb_path.stem + ".executed.ipynb")
        try:
            nbformat.write(run_nb, str(executed))
            print(f"[runner] Partial executed notebook saved: {executed}")
        except Exception:
            pass

        sys.exit(1)

    executed = outdir / (nb_path.stem + ".executed.ipynb")
    nbformat.write(run_nb, str(executed))
    print(f"\n[runner] SUCCESS: executed notebook saved: {executed}")


if __name__ == "__main__":
    main()
