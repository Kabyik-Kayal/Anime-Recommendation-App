pipeline {
    agent any
    environment{
        VENV_DIR = 'venv'
        GCP_PROJECT = 'carbide-datum-457415-j1'
        GCLOUD_PATH = "/var/jenkins_home/google-cloud-sdk/bin"
        KUBECTL_AUTH_PLUGIN = "/usr/lib/google-cloud-sdk/bin"
    }
    stages{
        stage("Cloning from GitHub") {
            steps {
                script {
                    echo "Cloning from GitHub"
                    checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-anime-system', url: 'https://github.com/Kabyik-Kayal/Anime-Recommendation-App']])
                }
            }
        }

        stage("Making a virtual environment") {
            steps {
                script {
                    echo "Making a virtual environment"
                    sh """
                        python -m venv ${VENV_DIR}
                        . ${VENV_DIR}/bin/activate
                        pip install --upgrade pip
                        pip install -e .
                    """
                }
            }
        }

        stage('Pulling DVC'){
            steps{
                withCredentials([file(credentialsId:'gcp-anime-key', variable:'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    script {
                        echo "Pulling DVC"
                        sh """
                            . ${VENV_DIR}/bin/activate
                            dvc pull
                        """
                    }
                }
            }
        }

        stage('Build and Deploy Docker Image') {
            steps{
                withCredentials([file(credentialsId:'gcp-anime-key', variable:'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    script {
                        echo "Building and Deploying Docker Image to GCR"
                        sh """
                        export PATH=$PATH:${GCLOUD_PATH}
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud config set project ${GCP_PROJECT}
                        gcloud auth configure-docker --quiet
                        docker build -t gcr.io/${GCP_PROJECT}/anime-recommendation-app:latest .
                        docker push gcr.io/${GCP_PROJECT}/anime-recommendation-app:latest
                        """
                    }
                }
            }
        }

        stage('Deploying to Kubernetes') {
            steps{
                withCredentials([file(credentialsId:'gcp-anime-key', variable:'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    script {
                        echo "Deploying Docker Image to Kubernetes"
                        sh """
                        export PATH=$PATH:${GCLOUD_PATH}:${KUBECTL_AUTH_PLUGIN}
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud config set project ${GCP_PROJECT}
                        gcloud container clusters get-credentials anime-app-cluster --region us-central1
                        kubectl apply -f deployment.yaml
                        """
                    }
                }
            }
        }
    }
}