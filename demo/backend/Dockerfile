FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy local package and demo backend
# Context is expected to be the project root
COPY . /app/source

# Install the local package and backend requirements
WORKDIR /app/source/demo/backend
RUN pip install -r requirements.txt

# Run the server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
