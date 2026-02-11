FROM python:3.12-slim

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install all system dependencies in one layer to optimize
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    libxcb1 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    websockify \
    net-tools \
    procps \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Setup NoVNC
RUN ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html

WORKDIR /app

# Copy and install Python requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Final environment tweaks
RUN chmod +x /app/docker-entrypoint.sh
ENV PYTHONUNBUFFERED=1

EXPOSE 6080

ENTRYPOINT ["/app/docker-entrypoint.sh"]
