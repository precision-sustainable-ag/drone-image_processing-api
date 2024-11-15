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
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV GDAL_VERSION=3.6.2

COPY requirements.txt ./
COPY *.requirements.txt ./
RUN pip install -r ${ENVIRONMENT}.requirements.txt

COPY . .

# dev is hotloaded, prod is "compiled"
# TODO: bind gunicorn to localhost - blocking prod access
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

# add log cleanup
# add healthcheck