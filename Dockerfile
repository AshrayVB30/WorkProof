# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for Tesseract and OpenCV (if needed)
RUN apt-get update && apt-get install -y --fix-missing \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# We skip PySide6 and pyinstaller in Docker as they are for the GUI version
RUN sed -i '/PySide6/d' requirements.txt && \
    sed -i '/pyinstaller/d' requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run server.py when the container launches
CMD ["python", "server.py"]
