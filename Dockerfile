FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required by OpenCV and EasyOCR
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Using opencv-python-headless to avoid GUI dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-multipart \
    pymupdf \
    spacy \
    opencv-python-headless \
    easyocr \
    psutil

# Download the required spaCy model
RUN python -m spacy download en_core_web_md

# Copy application code
COPY . .

# Ensure upload directories exist
RUN mkdir -p resumes_to_process archive/profile_pics

# Expose the API port
EXPOSE 3001

# Start the FastAPI server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "3001"]
