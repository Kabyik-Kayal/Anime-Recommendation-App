pipeline {
    agent any

    stages{
        stage("Cloning from GitHub") {
            steps {
                script {
                    echo "Cloning from GitHub"
                    checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-anime-system', url: 'https://github.com/Kabyik-Kayal/Anime-Recommendation-App']])
                }
            }
        }
    }
}