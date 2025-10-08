FROM python:3.12.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY dev/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Environment variables
ENV WEAVIATE_CLOUD_URL=<url to weaviate instance>
ENV WEAVIATE_CLOUD_API_KEY=<weaviate admin api key>

# Run the application
CMD ["python", "app.py", "--client", "cloud", "--debug"]
