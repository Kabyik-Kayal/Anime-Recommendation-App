pipeline {
    agent any
    environment{
        VENV_DIR = 'venv'
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
                            source ${VENV_DIR}/bin/activate
                            dvc pull
                        """
                    }
                }
            }
        }

    }
}