# Pramana web prototype

FastAPI serving precomputed JSON from `results/`; React + Vite + Tailwind +
Recharts front end. No training or data generation happens at request time.

## Run locally

```
# backend
PYTHONPATH=. .venv/bin/uvicorn web.api.main:app --reload --port 8000

# frontend (separate shell)
cd web/ui && npm install && npm run dev
```

The dev server proxies `/api` to port 8000. `npm run build` emits `dist/`,
which the FastAPI app serves directly, so a production deploy is one process.

## Deploy

`render.yaml` (Render) and `Dockerfile` (Hugging Face Spaces or any container
host) are in the repository root. Both build the UI and serve it from the same
FastAPI process.
