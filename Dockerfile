# Use official Python slim image
FROM python:3.13-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential \
        curl \
        gcc \
        libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install UV globally
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod +x /install.sh && /install.sh && rm /install.sh

# Add UV to PATH
ENV PATH="/root/.local/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Sync UV environment (install dependencies from pyproject.toml)
RUN uv sync

# Expose FastAPI port
EXPOSE 8000

# Healthcheck for Render
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default CMD: run migrations, seed database, and start FastAPI
CMD ["sh", "-c", "/root/.local/bin/uv run alembic upgrade head && /root/.local/bin/uv run python scripts/seed_banks.py && /root/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]