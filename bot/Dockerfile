FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

ENV APP_DIR=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR ${APP_DIR}

COPY requirements.txt ${APP_DIR}/

RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY . ${APP_DIR}

ENTRYPOINT ["python", "-u", "main.py"]