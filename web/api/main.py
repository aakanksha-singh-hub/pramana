"""FastAPI service for the Pramana prototype.

Serves precomputed JSON only. No model is trained and no data is generated at
request time: every number the interface shows was produced by an experiment
script in this repository and written to results/, so the prototype cannot
show anything the committed artefacts do not contain.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
UI_DIST = ROOT / "web" / "ui" / "dist"

app = FastAPI(title="Pramana", version="1.0",
              description="When is declared payment context worth collecting?")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])


@lru_cache(maxsize=32)
def _load(name: str) -> dict:
    path = RESULTS / name
    if not path.exists():
        raise HTTPException(404, f"{name} not generated yet — run the experiments")
    return json.loads(path.read_text())


@app.get("/api/health")
def health() -> dict:
    return {"ok": True,
            "available": sorted(p.name for p in RESULTS.glob("*.json"))}


@app.get("/api/phase")
def phase() -> dict:
    """Phase surface, rho*, ablation and every cell."""
    return _load("phase_surface.json")


@app.get("/api/ablation")
def ablation() -> dict:
    return _load("ablation.json")


@app.get("/api/agentic")
def agentic() -> dict:
    """Conformance coverage, false positives, bounded loss, demo frames."""
    return _load("agentic_conformance.json")


@app.get("/api/fidelity")
def fidelity() -> dict:
    return _load("fidelity.json")


@app.get("/api/inspector")
def inspector() -> dict:
    """Worked consistency cases, including ones where B4 misleads."""
    return _load("inspector.json")


@app.get("/api/provenance")
def provenance() -> dict:
    """Everything needed to check the work: the frozen pre-registration, the
    frozen hyperparameters, and the disclosed post-hoc changes."""
    def read(p: Path) -> str:
        return p.read_text() if p.exists() else ""
    return {
        "preregistration": read(ROOT / "PREREGISTRATION.md"),
        "changelog": read(ROOT / "CHANGELOG.md"),
        "limitations": read(ROOT / "docs" / "LIMITATIONS.md"),
        "data_card": read(ROOT / "docs" / "DATA_CARD.md"),
        "model_card": read(ROOT / "docs" / "MODEL_CARD.md"),
        "frozen_params": json.loads(read(ROOT / "config" / "frozen_params.json") or "{}"),
    }


if UI_DIST.exists():
    app.mount("/assets", StaticFiles(directory=UI_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        return FileResponse(UI_DIST / "index.html")
