FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "finai_quality_api:app", "--host", "0.0.0.0", "--port", "8000"]
