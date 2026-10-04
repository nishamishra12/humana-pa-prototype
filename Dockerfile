# PA Desk prototype. Runs anywhere that runs Docker. Keep PA_DATA_DIR on a persistent disk so cases survive restarts.
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils && rm -rf /var/lib/apt/lists/*
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY pipeline ./pipeline
COPY policies ./policies
COPY packets ./packets
COPY evals ./evals
COPY web ./web
ENV PYTHONUNBUFFERED=1 PA_DATA_DIR=/data
EXPOSE 8000
CMD ["sh", "-c", "mkdir -p $PA_DATA_DIR && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
