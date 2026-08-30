#!/bin/bash
# Wait for the sweep to finish, then run every downstream step.
cd /Users/aakankshasingh/Documents/Projects/mastercard
export PYTHONPATH=.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=.venv/bin/python

while pgrep -f "02_phase_study" > /dev/null; do sleep 30; done
echo "=== sweep finished at $(date +%H:%M) with $(ls results/raw | wc -l) cells ==="

echo "=== ablation ==="; $PY -W ignore experiments/01_baseline_ablation.py 2>&1 | tail -30
echo "=== figures ===";  $PY -W ignore experiments/05_figures.py 2>&1 | tail -40
echo "=== inspector ==="; $PY -W ignore experiments/06_inspector_export.py 2>&1 | tail -10
echo "=== fidelity ==="; $PY -W ignore experiments/04_fidelity_report.py 2>&1 | tail -20
echo "=== agentic ==="; $PY -W ignore experiments/03_agentic_conformance.py 2>&1 | tail -12
echo "=== docx ==="; $PY -W ignore experiments/07_build_docx.py 2>&1 | tail -5
echo "=== artifact ==="; $PY experiments/08_build_artifact.py 2>&1 | tail -3
echo "=== ui ==="; (cd web/ui && npm run build 2>&1 | tail -4)
echo "=== ALL DONE $(date +%H:%M) ==="
