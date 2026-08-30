PY := .venv/bin/python
export PYTHONPATH := .

.PHONY: test tune ablation sweep agentic fidelity figures all clean

test:            ; $(PY) -m pytest tests/ -q
tune:            ; $(PY) -W ignore experiments/00_tune_baseline.py
ablation:        ; $(PY) -W ignore experiments/01_baseline_ablation.py
sweep:           ; $(PY) -W ignore experiments/02_phase_study.py
agentic:         ; $(PY) -W ignore experiments/03_agentic_conformance.py
fidelity:        ; $(PY) -W ignore experiments/04_fidelity_report.py
figures:         ; $(PY) -W ignore experiments/05_figures.py
all: test tune ablation sweep agentic fidelity figures
clean:           ; rm -rf data/cache/* results/raw/*
