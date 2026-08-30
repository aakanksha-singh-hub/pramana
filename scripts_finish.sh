#!/bin/bash
cd /Users/aakankshasingh/Documents/Projects/mastercard
export PYTHONPATH=. OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=.venv/bin/python

run_downstream () {
  echo "=== ablation ===";  $PY -W ignore experiments/01_baseline_ablation.py 2>&1 | tail -30
  echo "=== figures ===";   $PY -W ignore experiments/05_figures.py 2>&1 | tail -70
  echo "=== inspector ==="; $PY -W ignore experiments/06_inspector_export.py 2>&1 | tail -10
  echo "=== fidelity ===";  $PY -W ignore experiments/04_fidelity_report.py 2>&1 | tail -18
  echo "=== agentic ===";   $PY -W ignore experiments/03_agentic_conformance.py 2>&1 | tail -12
  echo "=== docx ===";      $PY -W ignore experiments/07_build_docx.py 2>&1 | tail -4
  echo "=== artifact ===";  $PY experiments/08_build_artifact.py 2>&1 | tail -2
  (cd web/ui && npm run build 2>&1 | tail -2)
}

# 1. wait for the pre-registered + prevalence sweep
while pgrep -f "02_phase_study" > /dev/null; do sleep 30; done
while pgrep -f "probe_matched" > /dev/null; do sleep 15; done
echo "=== sweep 1 finished $(date +%H:%M), $(ls results/raw | wc -l) cells ==="

# 2. pre-registered analysis, so it exists before the long third surface
run_downstream
echo "=== PRE-REGISTERED ANALYSIS COMPLETE $(date +%H:%M) ==="

# 3. the beneficiary-matched surface
PRAMANA_JOBS=4 $PY -W ignore experiments/02_phase_study.py matched > logs/sweep_matched.log 2>&1
echo "=== matched surface finished $(date +%H:%M), $(ls results/raw | wc -l) cells ==="

# 4. rebuild everything with all three surfaces
run_downstream
echo "=== ALL DONE $(date +%H:%M) ==="
