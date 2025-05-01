# Anime-Recommendation-App

## Types of Recommendation System used : 
    1. Content Based
    2. User Based / Collaborative Filtering
    3. Hybrid System

## Target Audience - Anime Streaming Platforms eg. Crunchyroll

## Use Case :

- Increase User Retention Rate
- Increase Audience
- Increase Revenue

## Workflow

- Database setup in GCP buckets
- Data Ingestion
- Notebook Testing
- Data Processing
- Model Architecture
- Model Training
- Experiment Tracking
- Training Pipeline
- Data Versioning with DVC
- Prediction Helper
- User App with Prediction Pipeline
- CI/CD Deployment using Jenkins, Docker, GCR and Kubernetes

## Jenkins

These steps are for setting up Jenkins within a Docker container to run the pipeline.

1.  **Run Jenkins Docker-in-Docker Container:**
    ```bash
    # Ensure Docker is running on your host machine
    sudo docker run -d \
      --name jenkins-anime \
      --privileged \
      -p 8080:8080 -p 50000:50000 \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v jenkins_home:/var/jenkins_home \
      jenkins-anime
    ```
    *   `-v /var/run/docker.sock:/var/run/docker.sock`: Mounts the host's Docker socket to allow Jenkins to run Docker commands.
    *   `-v jenkins_home:/var/jenkins_home`: Persists Jenkins data.
    *   `--privileged`: Required for Docker-in-Docker (use with caution).

2.  **Get Initial Jenkins Admin Password:**
    ```bash
    sudo docker logs jenkins-anime
    ```
    Look for the password in the logs.

3.  **Access Jenkins:** Open `http://localhost:8080` in your browser and complete the setup using the password. Install suggested plugins.

4.  **Configure Jenkins Container (Install Python & Tools):**
    ```bash
    sudo docker exec -u root -it jenkins-anime bash

    # Inside the container:
    apt-get update && apt-get install -y python3 python3-pip python3-venv git curl gnupg
    ln -s /usr/bin/python3 /usr/bin/python # Create symlink if needed
    python --version

    # Install Google Cloud SDK (Example - adjust if needed)
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
    apt-get update && apt-get install -y google-cloud-sdk

    getent group docker #check if docker is accessible
    id jenkins #check docker asssociated or not

    chown root:docker /var/run/docker.sock #update socket ownership
    chmod 660 /var/run/docker.sock


    exit
    ```

5.  **Restart Jenkins Container:**
    ```bash
    sudo docker restart jenkins-dind
    ```
