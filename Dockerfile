FROM python:3.13-slim

COPY ./requirements.txt /tmp/requirements.txt
COPY ./src /app/src

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install gcc and curl for building and downloading packages
# Use --no-install-recommends to avoid installing unnecessary packages
# Clean up apt cache to reduce image size
# Use pip to install Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc curl && \
    pip install --upgrade pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app

ENV PYTHONPATH=/app

EXPOSE 7860

# Create a non-root user 'appuser' and switch to this user
RUN useradd --create-home appuser
USER appuser

# CMD
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "7860"]