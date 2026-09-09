# -*- coding: utf-8 -*-
r"""Run the pipeline notebooks without Jupyter.

    py -u run_pipeline.py 1 2 3 4 5
    py -u run_pipeline.py 2 3 4 --only Population
    py -u run_pipeline.py 5 --only Population --only Labor

A run takes minutes and its progress bar has to stay readable while it goes, so
the notebooks are executed cell by cell from here and the output redirected to a
log that can be polled:

    PYTHONIOENCODING=utf-8 PYTHONUTF8=1 py -u run_pipeline.py 2 3 4 > run.log 2>&1

Each notebook gets a fresh namespace - they share nothing but the files on disk,
which is the point of splitting them. --only overrides CHAPTERS straight after
the config cell, so limiting a run to one chapter never means editing a
notebook and forgetting to put it back.
"""
import argparse
import json
import sys
from pathlib import Path

CODES = Path(__file__).resolve().parent

NOTEBOOKS = {
    "1": "Compendium_1_Long_Files.ipynb",
    "2": "Compendium_2_New_Indicators.ipynb",
    "3": "Compendium_3_Translation.ipynb",
    "4": "Compendium_4_Tabulations.ipynb",
    "5": "Compendium_5_Charts.ipynb",
}


def run(number, only):
    """Execute one notebook's code cells in order, into a namespace of its own."""
    name = NOTEBOOKS[number]
    print("\n" + "=" * 78, flush=True)
    print(f"NOTEBOOK {number}: {name}", flush=True)
    print("=" * 78, flush=True)

    notebook = json.loads((CODES / name).read_text(encoding="utf-8"))
    namespace = {}
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        exec(compile(source, f"{name}:{cell.get('id')}", "exec"), namespace)

        # The config cell is where CHAPTERS is set. Overriding it here rather
        # than editing the notebook keeps the committed default honest.
        if cell.get("id") == "config" and only:
            namespace["CHAPTERS"] = list(only)
            print(f"  (CHAPTERS overridden to {list(only)} for this run)", flush=True)
    return namespace


parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("notebooks", nargs="+", choices=sorted(NOTEBOOKS),
                    help="which notebooks to run, in the order given")
parser.add_argument("--only", action="append", metavar="CHAPTER",
                    help="limit the run to this chapter; repeatable")
arguments = parser.parse_args()

for number in arguments.notebooks:
    run(number, arguments.only)

print("\nDONE", flush=True)
