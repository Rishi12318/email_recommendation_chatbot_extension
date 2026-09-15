pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.12'
        GROQ_API_KEY = credentials('groq-api-key')
        HF_TOKEN = credentials('hf-token')
        GOOGLE_CLIENT_ID = credentials('google-client-id')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    python --version
                    pip install --upgrade pip setuptools wheel
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                sh 'pip install flake8 && flake8 app/ --max-line-length=120 --ignore=E501,W503'
            }
        }

        stage('Unit Tests') {
            steps {
                sh 'pytest tests/ -v --junitxml=reports/test-results.xml'
            }
            post {
                always {
                    junit 'reports/test-results.xml'
                }
            }
        }

        stage('Build Model') {
            steps {
                sh 'python scripts/setup_model.py'
            }
        }

        stage('Deploy to Render') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    echo "Deploying to Render..."
                    curl -X POST "${RENDER_DEPLOY_HOOK}" || echo "Manual deploy required"
                '''
            }
        }
    }

    post {
        success {
            slackSend(
                color: 'good',
                message: "✅ Build SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            )
        }
        failure {
            slackSend(
                color: 'danger',
                message: "❌ Build FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}\n${env.BUILD_URL}"
            )
        }
        always {
            cleanWs()
        }
    }
}
