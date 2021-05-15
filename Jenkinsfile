pipeline { 
    agent any 
    stages {
        // stage('Checkout from SCM') { 
        //     steps {
        //       git branch: 'main', url: 'https://github.com/vibhuthasak/cisco-qos-viewer.git'
        //     }
        // }
        stage('Docker image build'){
            steps {
                sh 'docker build -t cisco-ios-qos:1.0.2 .'
            }
        }
        // stage('Deploy') {
        //     steps {
        //         sh 'make publish'
        //     }
        // }
    }
}