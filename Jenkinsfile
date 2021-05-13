// node {
//     stage("Github checkout") {
//         git branch: 'main', url: 'https://github.com/vibhuthasak/cisco-qos-viewer.git'
//     }
// }

pipeline {
  agent { dockerfile true }
  stages {
    stage('Test') {
      steps {
          sh 'node --version'
          sh 'svn --version'
      }
    }
  }
}