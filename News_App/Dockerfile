FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code

# Install system dependencies for MySQL
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /code/

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]