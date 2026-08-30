# Pramana prototype: builds the UI, then serves it from the same FastAPI process.
FROM node:20-slim AS ui
WORKDIR /ui
COPY web/ui/package.json web/ui/package-lock.json* ./
RUN npm install
COPY web/ui/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
# The prototype serves precomputed JSON; the heavy scientific stack is only
# needed to regenerate results, so the container installs the serving subset.
RUN pip install --no-cache-dir fastapi==0.115.6 uvicorn==0.34.0
COPY web/api ./web/api
COPY results ./results
COPY PREREGISTRATION.md CHANGELOG.md ./
COPY docs ./docs
COPY config ./config
COPY --from=ui /ui/dist ./web/ui/dist
EXPOSE 7860
CMD ["uvicorn", "web.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
