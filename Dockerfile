FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/aether /data/aether/ollama && \
    chmod +x aether scripts/*.sh scripts/railway-start.sh

ENV AETHER_DATA_DIR=/data/aether
ENV OLLAMA_HOST=127.0.0.1:11434
ENV OLLAMA_MODELS=/data/aether/ollama
ENV OLLAMA_MODEL=llama3.2

EXPOSE 8000

CMD ["./scripts/railway-start.sh"]
