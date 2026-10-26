# Stage 1: install dependencies
FROM python:3.11-slim AS deps
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: final image (only what we need to run)
FROM python:3.11-slim
WORKDIR /app
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY app/ .

# Run as a non-root user
RUN useradd -m appuser
USER appuser

CMD ["python", "monitor.py", "--help"]
