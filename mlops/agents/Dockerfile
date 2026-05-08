FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY agents/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/ ./agents/
COPY aiops/system_logs.txt ./mlops/aiops/system_logs.txt

EXPOSE 8080

CMD ["uvicorn", "agents.agent_api:app", "--host", "0.0.0.0", "--port", "8080"]
