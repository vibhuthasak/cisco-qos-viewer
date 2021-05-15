pipeline { 
    agent any 
    stages {
        stage('Docker image build'){
            steps {
                sh "docker build -t cisco-ios-qos:1.0.${BUILD_NUMBER} ."
            }
        }
    }
}