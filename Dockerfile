FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

WORKDIR /app

# Install system dependencies & python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

# Copy application files
COPY . .

# Expose Web Port
EXPOSE 8000

# Run FastAPI server
CMD ["python", "run_server.py"]
