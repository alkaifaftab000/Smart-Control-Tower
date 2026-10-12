# Smart Control Tower - Deployment Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Set production environment defaults
ENV PYTHONUNBUFFERED=1 \
    SMART_TOWER_HOST=0.0.0.0 \
    PORT=4173

# Copy application files
COPY prototype.html ai_local_server.py ./
COPY assets/ ./assets/

# Optional: install lightweight helpers if needed
RUN pip install --no-cache-dir openpyxl

EXPOSE 4173

# Run the control tower server
CMD ["python", "ai_local_server.py"]
