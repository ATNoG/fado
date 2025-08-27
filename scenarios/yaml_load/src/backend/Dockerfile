FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy code
COPY . .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Set environment (Chalice local server)
ENV PYTHONUNBUFFERED=1

# Expose the Chalice local port
EXPOSE 8000

# Command to run the Chalice app
CMD ["chalice", "local", "--host", "0.0.0.0"]
