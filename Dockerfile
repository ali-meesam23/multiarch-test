# Dockerfile
FROM python:3.11-slim-bookworm

ENV PIP_NO_CACHE_DIR=1 PIP_PREFER_BINARY=1 \
    # helps avoid OpenBLAS autodetect problems on some ARM cores (harmless on x86)
    OPENBLAS_CORETYPE=ARMV8

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /app/app.py
COPY current_time.py /app/current_time.py
COPY whatsmyip.py /app/whatsmyip.py

CMD ["python", "app.py"]
