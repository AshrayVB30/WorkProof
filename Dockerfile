FROM python:3.12-slim

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for:
# 1. Tesseract OCR
# 2. Qt/PySide6 (GUI)
# 3. Virtual Display (Xvfb, VNC, Fluxbox, NoVNC)
RUN apt-get update && apt-get install -y \
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
    && rm -rf /var/lib/apt/lists/*

# Fix NoVNC location (Debian/Ubuntu specific)
RUN ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure entrypoint is executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose NoVNC port
EXPOSE 6080

# Use the entrypoint script to start the virtual display and the app
ENTRYPOINT ["/app/docker-entrypoint.sh"]
