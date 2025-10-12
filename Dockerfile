FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install LiveKit agents and dependencies
RUN pip install --no-cache-dir \
    livekit-agents[silero,turn-detector]~=1.2 \
    livekit-plugins-noise-cancellation~=0.2 \
    livekit-plugins-google~=1.2 \
    livekit-plugins-elevenlabs~=1.2 \
    python-dotenv

# Copy application code
COPY src/ ./src/
COPY .env.local ./

# Download model files
RUN python src/agent.py download-files

# Run the agent
CMD ["python", "src/agent.py", "start"]