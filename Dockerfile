FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer is cached if requirements don't change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

CMD ["python3", "main.py"]
