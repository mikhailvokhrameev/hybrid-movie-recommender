#!/bin/sh
set -e

# Start Ollama server in the background
ollama serve &
SERVER_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama server..."
until ollama list > /dev/null 2>&1; do
    sleep 1
done
echo "Ollama server is ready"

# Pull the model if not already present
MODEL="${OLLAMA_MODEL:-qwen2.5:7b}"
if ! ollama list | grep -q "$MODEL"; then
    echo "Pulling model: $MODEL"
    ollama pull "$MODEL"
    echo "Model $MODEL is ready"
else
    echo "Model $MODEL already available"
fi

# Wait for the server process
wait $SERVER_PID
