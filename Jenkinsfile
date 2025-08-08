pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "ticket_book"
        DOCKER_TAG = "latest"
        // This must match the ID you create in Jenkins Credentials Manager for Docker Hub username/password
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')  
        REGISTRY = "kosalaperera780"  // Docker Hub username (without domain)
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/your-username/your-repo.git'  // <-- Replace with your repo URL
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    // Runs pytest tests inside a container (make sure tests folder and pytest are setup correctly)
                    sh "docker run --rm ${DOCKER_IMAGE}:${DOCKER_TAG} pytest tests/"
                }
            }
        }

        stage('Push Image') {
            steps {
                script {
                    sh """
                    echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin
                    docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}
                    docker push ${REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}
                    """
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    sh """
                    docker stop ticket_book || true
                    docker rm ticket_book || true
                    docker run -d --name ticket_book -p 5000:5000 ${REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}
                    """
                }
            }
        }
    }
}
