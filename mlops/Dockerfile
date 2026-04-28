FROM python:3.11-slim

WORKDIR /app

COPY mlops/requirements.txt .
RUN pip install --no-cache-dir scikit-learn fastapi uvicorn pydantic pyyaml

COPY mlops/serve.py .
COPY models/model.pkl models/model.pkl

EXPOSE 8080

CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8080"]
