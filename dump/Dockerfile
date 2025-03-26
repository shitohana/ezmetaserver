FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt --no-deps --ignore-installed

RUN pip install gunicorn
COPY src/ src/

RUN ldconfig
EXPOSE 8001

CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "3", "--worker-class", "uvicorn.workers.UvicornWorker", "--pythonpath", "/app/src", "--preload", "--timeout", "300", "main:app", "--forwarded-allow-ips", "*"]
