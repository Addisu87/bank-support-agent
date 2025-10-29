FROM python:3.13-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Download UV install script
ADD https://astral.sh/uv/install.sh /install.sh

# Run the UV installer
RUN chmod +x /install.sh && /install.sh && rm /install.sh

# Set up the UV environment path correctly
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY . .

# Initialize UV environment
RUN uv sync

# Expose FastAPI port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default CMD to run FastAPI with migrations and seed script
CMD ["sh", "-c", "source /app/.venv/bin/activate && alembic upgrade head && python scripts/seed_banks.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]

