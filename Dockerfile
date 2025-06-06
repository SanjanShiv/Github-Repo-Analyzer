FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies, including Tkinter
RUN apt-get update && \
    apt-get install -y build-essential libglib2.0-0 libsm6 libxext6 libxrender-dev tesseract-ocr poppler-utils python3-tk && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements.txt
COPY requirements_gui.txt requirements_gui.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install --no-cache-dir -r requirements_gui.txt

# Copy project files
COPY . .

# Expose port for GUI (if using web-based GUI, e.g., with Flask or Streamlit)
# EXPOSE 8501

# Default command (update as needed for your GUI entrypoint)
CMD ["python", "github_analyzer_gui.py"]
