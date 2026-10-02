FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /data/aether && chmod +x aether scripts/*.sh
ENV AETHER_DATA_DIR=/data/aether
EXPOSE 8000
CMD ["sh","-c","uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
