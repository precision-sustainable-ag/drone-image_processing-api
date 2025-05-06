FROM python:3.9-slim

ARG ENVIRONMENT
ARG STORAGE_PATH
ENV ENVIRONMENT=${ENVIRONMENT}
ENV STORAGE_PATH=${STORAGE_PATH}
RUN echo "environment: $ENVIRONMENT"

WORKDIR /app

# Install system dependencies including GDAL
RUN apt-get update && apt-get install -y \
    build-essential \
    libgdal-dev \
    gdal-bin \
    python3-gdal \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV GDAL_VERSION=3.6.2

COPY requirements.txt ./
COPY *.requirements.txt ./
RUN pip install -r ${ENVIRONMENT}.requirements.txt

COPY . .

# Create logs directory if it doesn't exist
RUN mkdir -p /app/logs
# allow all users to write to logs
RUN chmod 777 /app/logs
# Setup log rotation
# RUN echo '#!/bin/sh\nfind /app/logs -type f -name "*.log" -mtime +7 -delete' > /app/cleanup_logs.sh && \
#     chmod +x /app/cleanup_logs.sh && \
#     echo '0 0 * * * /app/cleanup_logs.sh' | crontab -

# Set proxies
ENV http_proxy=http://proxy.oit.ncsu.edu:3128
ENV https_proxy=http://proxy.oit.ncsu.edu:3128
ENV no_proxy=localhost,127.0.0.1,169.254.169.254,169.254.170.2,.ncsu.edu

# dev is hotloaded, prod is "compiled"
CMD if [ "$ENVIRONMENT" = "dev" ]; then \
        export FLASK_APP=app.py && \
        export FLASK_DEBUG=1 && \
        export PYTHONUNBUFFERED=1 && \
        echo $ENVIRONMENT && \
        flask run --host=0.0.0.0 --port=5000 --debug; \
    else \
        echo "================" && \
        echo $ENVIRONMENT && \
        echo "================" && \
        gunicorn --bind 0.0.0.0:5000 app:app; \
    fi

# Add healthcheck
# HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
#   CMD curl -f http://localhost:5000/ping || exit 1