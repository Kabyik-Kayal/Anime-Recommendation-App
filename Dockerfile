FROM python:3.8-slim

# Declare build arguments for Comet ML credentials
ARG COMET_ML_API_KEY
ARG COMET_ML_PROJECT_NAME
ARG COMET_ML_WORKSPACE

# Set environment variables from build arguments
ENV COMET_ML_API_KEY=${COMET_ML_API_KEY}
ENV COMET_ML_PROJECT_NAME=${COMET_ML_PROJECT_NAME}
ENV COMET_ML_WORKSPACE=${COMET_ML_WORKSPACE}

# Set environment variables to prevent Python from writing .pyc files & Ensure Python output is not buffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies required by TensorFlow
RUN apt-get update && apt-get install -y \
    build-essential \
    libatlas-base-dev \
    libhdf5-dev \
    libprotobuf-dev \
    protobuf-compiler \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . .

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -e .

# Train the model before running the application
RUN python pipeline/training_pipeline.py

# Expose the port that Flask will run on
EXPOSE 5000

# Command to run the app
CMD ["python", "app.py"]