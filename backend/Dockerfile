FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first (much smaller, prevents timeout)
# This avoids downloading 2GB+ of CUDA packages
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install remaining Python dependencies
COPY requirements.txt .
# Install other packages (sentence-transformers will use the CPU PyTorch we just installed)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check - Railway handles its own healthchecks via /health endpoint
# This Docker healthcheck uses a simple port check, Railway will use /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 \
    CMD sh -c "python -c \"import socket; s=socket.socket(); s.connect(('127.0.0.1', int('${PORT:-8000}'))); s.close()\"" || exit 1

# Run the application
# Railway provides PORT via environment variable
# Use shell form to ensure PORT variable expansion works
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

