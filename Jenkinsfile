pipeline {
    agent any
    stages {
        stage('Build on runner') {
            steps {
                echo '//////////////////Building the project.//////////////////////'
                sh 'whoami'
                sh 'pwd'
                sh 'docker ps'
                sh 'docker login -u ${USER_REGISTRY} -p ${USER_PASSWORD_REGISTRY}'
                sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .'
                sh 'docker push ${IMAGE_NAME}:${IMAGE_TAG}'
                }
            }
        stage('Test') {
            steps {
                echo 'Running fake tests.'
            }
        }
        stage('Deploy') {
            steps {
                sh 'echo Deploying the application to ${DEPLOYMENT_SERVER_HOST}'
                sh 'sshpass -p ${USER_PASSWORD_SERVER_HOST} scp ./docker-compose.yml ${USER_SERVER_HOST}@${DEPLOYMENT_SERVER_HOST}:/home/jenkins \
                && sshpass -p ${USER_PASSWORD_SERVER_HOST} ssh ${USER_SERVER_HOST}@${DEPLOYMENT_SERVER_HOST} \
                "docker login -u ${USER_REGISTRY} -p ${USER_PASSWORD_REGISTRY} \
                && docker pull ${IMAGE_NAME}:${IMAGE_TAG} \
                && export DC_TRIPADVISOR_API_KEY=${TRIPADVISOR_API_KEY} \
                && export DC_IMAGE_NAME=${IMAGE_NAME} \
                && export DC_IMAGE_TAG=${IMAGE_TAG} \
                && export DC_APP_PORT=8501 \
                && export DC_DASH_PORT=8050 \
                && export DC_BACKEND_PORT=8080 \
                && docker compose down && docker compose up -d"'
            }
        }
    }
}
