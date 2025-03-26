FROM python:3.7.17-slim

RUN apt-get update

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt --no-deps --ignore-installed

RUN pip install fastapi # This is just not to reinstall all dependencies
RUN pip install uvicorn
RUN ldconfig

EXPOSE 8000

COPY pretrained_models/ pretrained_models/
COPY vocab/ vocab/
COPY instance/ instance/
COPY src src/
ENV CONFIG_FILE=/app/instance/config.yaml


CMD [ \
    "uvicorn", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--workers", "1", \
    "--app-dir", "/app/src", \
    "--timeout-keep-alive", "300", \
    "--root-path", "/api/v1/nlp", \
    "main:app" \
]
