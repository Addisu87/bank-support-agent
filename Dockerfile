FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential git ffmpeg tesseract-ocr && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml /app/
RUN python -m pip install --upgrade pip
RUN pip install pydantic fastapi uvicorn[standard] sqlalchemy asyncpg aiocache[redis] celery[redis] PyJWT bcrypt prometheus_client httpx
COPY . /app
ENV PYTHONPATH=/app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
