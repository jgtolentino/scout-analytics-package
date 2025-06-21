# ─── Dockerfile ────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# 1. install deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. copy source
COPY . /app

# 3. run the API with Gunicorn + Uvicorn worker
#    ⚠️  `main:app` =  path.to.file:FastAPI/Flask-ASGI variable
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", \
     "main:app", "--bind", "0.0.0.0:8000", "--access-logfile", "-"]

