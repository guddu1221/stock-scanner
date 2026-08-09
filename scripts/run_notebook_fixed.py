#!/usr/bin/env python3
"""Run a supplied notebook outside Colab.

Google/Colab publishing cells are skipped. For automation, pass
--market india or --market usa; the value is exposed to the notebook as
SCAN_MARKET.
"""
import argparse
import os
import re
import sys
import traceback
from pathlib import Path

import nbformat
from nbclient import NotebookClient

SKIP_PATTERNS = [
    r"google\.colab",
    r"gspread",
    r"googleapiclient",
    r"auth\.authenticate_user",
    r"google\.auth",
    r"MediaInMemoryUpload",
    r"open_by_key",
    r"set_with_dataframe",
    r"drive\.mount",
    r"build\(['\"]drive",
    r"SAVE TO GOOGLE DRIVE",
    r"PUBLISH — Write results to Google Sheets",
    r"PUBLISH —",
    r"AUTOMATION:\s*skip",
]

def should_skip(source: str) -> bool:
    return any(re.search(p, source, re.I) for p in SKIP_PATTERNS)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("notebook")
    ap.add_argument("--market", choices=("india", "usa"), default="usa",
                    help="scan universe: india=Nifty 500 only; usa=S&P 500 + Russell 2000")
    ap.add_argument("--max-cell", type=int, default=None,
                    help="execute code cells through this zero-based cell index")
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()

    os.environ["SCAN_MARKET"] = args.market

    nb_path = Path(args.notebook)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    nb = nbformat.read(nb_path, as_version=4)

    cells = []
    for idx, c in enumerate(nb.cells):
        if c.cell_type != "code":
            continue
        if args.max_cell is not None and idx > args.max_cell:
            continue
        src = c.source
        if should_skip(src):
            print(f"[migration] SKIP cell {idx}: Google/Colab/publish/automation-only cell")
            continue
        cells.append(c)

    run_nb = nbformat.v4.new_notebook(metadata=nb.metadata, cells=cells)

    client = NotebookClient(
        run_nb,
        timeout=60 * 60 * 3,
        kernel_name="python3",
        resources={"metadata": {"path": str(Path.cwd())}},
    )

    try:
        client.execute()
    except Exception:
        print("[migration] notebook execution failed")
        traceback.print_exc()
        sys.exit(1)

    executed = outdir / (nb_path.stem + ".executed.ipynb")
    nbformat.write(run_nb, executed)
    print(f"[migration] executed notebook saved: {executed}")

if __name__ == "__main__":
    main()
