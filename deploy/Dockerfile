FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/backend /app/frontend

WORKDIR /app/backend

EXPOSE 8000

CMD ["sh", "-c", "cd db && alembic upgrade head && cd .. && uvicorn app:app --host 0.0.0.0 --port 8000"]
