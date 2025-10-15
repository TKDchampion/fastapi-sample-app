FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY app/ ./app/

COPY alembic.ini .
COPY alembic/ ./alembic/

ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port $PORT"]