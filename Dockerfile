# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# 1. Qt dependencies for PySide6
# 2. Tesseract OCR dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libegl1 \
    libopengl0 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xinput0 \
    libxcb-xfixes0 \
    libxcb-shape0 \
    libxcb-cursor0 \
    libxcb-shm0 \
    libxcb-sync1 \
    libxcb-util1 \
    libxcb-render0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-present0 \
    libxcb-composite0 \
    libxcb-damage0 \
    libxcb-glx0 \
    libxcb-dri3-0 \
    libxcb-dri2-0 \
    libfontconfig1 \
    libxrender1 \
    libxi6 \
    libxext6 \
    libx11-6 \
    tesseract-ocr \
    libtesseract-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the command to run the application
CMD ["python", "main.py"]
