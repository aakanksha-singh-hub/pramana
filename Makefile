PY := .venv/bin/python
export PYTHONPATH := .

.PHONY: test tune ablation sweep agentic fidelity figures inspector docx ui api all clean

test:            ; $(PY) -m pytest tests/ -q
tune:            ; $(PY) -W ignore experiments/00_tune_baseline.py
ablation:        ; $(PY) -W ignore experiments/01_baseline_ablation.py
sweep:           ; $(PY) -W ignore experiments/02_phase_study.py
agentic:         ; $(PY) -W ignore experiments/03_agentic_conformance.py
fidelity:        ; $(PY) -W ignore experiments/04_fidelity_report.py
figures:         ; $(PY) -W ignore experiments/05_figures.py
inspector:       ; $(PY) -W ignore experiments/06_inspector_export.py
docx:            ; $(PY) -W ignore experiments/07_build_docx.py
ui:              ; cd web/ui && npm install && npm run build
api:             ; $(PY) -m uvicorn web.api.main:app --port 8000
all: test tune ablation sweep agentic fidelity figures inspector docx ui
clean:           ; rm -rf data/cache/* results/raw/*
