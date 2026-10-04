#!/bin/bash
# Runs the multi-illness evals 5 times in a row so we can report a flake rate, not one lucky pass.
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8 PYTHONPATH=.
for i in 1 2 3 4 5; do
  python scripts/run_evals.py > evals/reports/stability_run_$i.txt 2>&1
done
echo done > evals/reports/stability_done.txt
