# backend/Dockerfile

# ── Base image ──────────────────────────────
# Python 3.11 slim = Python installed on a minimal Linux
# "slim" means no unnecessary extras — keeps image size small
FROM python:3.11-slim

# ── Working directory ────────────────────────
# All subsequent commands run from inside /app
# This is the folder inside the container, not your actual machine
WORKDIR /app

# ── System dependencies ──────────────────────
# psycopg2 (PostgreSQL driver) needs these Linux packages to compile
# --no-install-recommends keeps it lean
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    poppler-utils \
    libpoppler-dev \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ──────────────────────
# Copy requirements first — before copying app code
# Why? Docker caches each step. If requirements didn't change,
# Docker skips reinstalling them even if your code changed.
# This makes rebuilds much faster.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── App code ─────────────────────────────────
# Copy everything else into /app inside the container
COPY . .

# ── Port ─────────────────────────────────────
# Tells Docker this container listens on port 8000
# Doesn't actually open the port — docker-compose does that
EXPOSE 8000

# ── Start command ─────────────────────────────
# uvicorn = the server that runs FastAPI
# app.main:app = "in the app/main.py file, find the variable called app"
# --host 0.0.0.0 = accept connections from outside the container
# --port 8000 = listen on port 8000
# --reload = auto restart when code changes (remove this in production)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]