PY := .venv/bin/python
export PYTHONPATH := .

.PHONY: test tune ablation sweep agentic fidelity figures inspector docx artifact scorer site audit audit ui api all clean

test:            ; $(PY) -m pytest tests/ -q
tune:            ; $(PY) -W ignore experiments/00_tune_baseline.py
ablation:        ; $(PY) -W ignore experiments/01_baseline_ablation.py
sweep:           ; $(PY) -W ignore experiments/02_phase_study.py
agentic:         ; $(PY) -W ignore experiments/03_agentic_conformance.py
fidelity:        ; $(PY) -W ignore experiments/04_fidelity_report.py
figures:         ; $(PY) -W ignore experiments/05_figures.py
inspector:       ; $(PY) -W ignore experiments/06_inspector_export.py
docx:            ; $(PY) -W ignore experiments/07_build_docx.py
artifact:        ; $(PY) experiments/08_build_artifact.py
scorer:          ; $(PY) -W ignore experiments/10_export_scorer.py
site:            ; $(PY) experiments/09_build_site.py
audit:           ; $(PY) -W ignore experiments/11_audit_claims.py
ui:              ; cd web/ui && npm install && npm run build
api:             ; $(PY) -m uvicorn web.api.main:app --port 8000
all: test tune ablation sweep agentic fidelity figures inspector docx artifact scorer site audit audit ui
clean:           ; rm -rf data/cache/* results/raw/*
