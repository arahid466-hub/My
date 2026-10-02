#!/bin/sh
set -eu

export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
export OLLAMA_MODELS="${OLLAMA_MODELS:-/data/aether/ollama}"

mkdir -p "$OLLAMA_MODELS"

echo "=== Starting Ollama ==="
ollama serve >/tmp/ollama.log 2>&1 &

echo "=== Waiting for Ollama ==="
i=0
until ollama list >/dev/null 2>&1; do
    i=$((i+1))
    if [ "$i" -ge 60 ]; then
        echo "Ollama failed to start"
        cat /tmp/ollama.log || true
        exit 1
    fi
    sleep 2
done

MODEL="${OLLAMA_MODEL:-llama3.2}"

if ! ollama list | awk 'NR>1 {print $1}' | grep -qx "$MODEL"; then
    echo "=== Downloading model: $MODEL ==="
    ollama pull "$MODEL"
fi

echo "=== Starting Aether API ==="
exec uvicorn server.main:app --host 0.0.0.0 --port "${PORT:-8000}"
