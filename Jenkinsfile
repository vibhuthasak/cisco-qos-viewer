pipeline {
  agent any
  environment {
      TEST_VAR = "123TEST"
  }
  stages {
    stage('Docker image build'){
      steps {
        sh 'echo $TEST_VAR'
        sh "echo ${TEST_VAR}"
        script {
          docker.build("cisco-ios-qos:1.0.${BUILD_NUMBER}")
        }
        // sh "docker build -t cisco-ios-qos:1.0.${BUILD_NUMBER} ."
      }
    }
  }
}