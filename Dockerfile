# Use a Python base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential pkg-config default-libmysqlclient-dev \
        && rm -rf /var/lib/apt/lists/*

# Copy the dependency file and install dependencies (including gunicorn)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the Flask application and Gunicorn config file
COPY . .

# Expose the port Gunicorn will listen on (for documentation)
EXPOSE 5000

# The command that runs when the container starts.
# -c tells gunicorn to load the configuration from the file.
CMD ["gunicorn", "-c", "./gunicorn_config.py"]