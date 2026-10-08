# Render.com Gateway — Ultra-lightweight (no ML dependencies)
FROM python:3.10-slim

WORKDIR /app

# Only install gateway dependencies (~20 MB total)
RUN pip install --no-cache-dir \
    Flask==3.1.3 \
    flask-cors==6.0.5 \
    requests==2.34.2 \
    gunicorn==23.0.0

# Copy only the gateway file
COPY gateway.py .

EXPOSE 10000

# Render sets PORT=10000 by default
CMD exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 2 --timeout 310 gateway:app
