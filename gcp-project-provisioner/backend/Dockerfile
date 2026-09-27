FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY job.py .

# Cloud Run Job runs this as a one-shot process, then exits.
ENTRYPOINT ["python", "job.py"]
