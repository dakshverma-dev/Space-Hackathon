FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends software-properties-common curl ca-certificates \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3.11 python3.11-venv \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python3.11 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r /app/requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend

EXPOSE 8000

CMD ["/opt/venv/bin/uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
