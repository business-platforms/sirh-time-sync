// pipeline {
//     agent any  // Will use your Linux Jenkins master
//
//     parameters {
//         booleanParam(
//             name: 'FORCE_BUILD',
//             defaultValue: false,
//             description: 'Force build even if version already exists'
//         )
//         text(
//             name: 'RELEASE_NOTES',
//             defaultValue: 'Bug fixes and improvements',
//             description: 'Release notes for this version'
//         )
//     }
//
//     environment {
//         // Update server details
//         UPDATE_SERVER_URL = 'http://timesync-dev.rh-partner.com:3010'
//         ADMIN_KEY = 'Vastness5-Ferocious1-Stooge7-Brewing9'
//
//         // Server connection details
//         SERVER_HOST = '157.173.97.199'
//         SERVER_USER = 'root'
//         SERVER_PATH = '/root/sirh/time-sync/downloads'
//     }
//
//     stages {
//         stage('Get Version from File') {
//             steps {
//                 script {
//                     if (!fileExists('version.txt')) {
//                         error("version.txt file not found in repository root")
//                     }
//
//                     def versionFromFile = readFile('version.txt').trim()
//
//                     if (!versionFromFile) {
//                         error("version.txt file is empty")
//                     }
//
//                     if (!versionFromFile.matches(/^\d+\.\d+\.\d+$/)) {
//                         error("Invalid version format in version.txt: '${versionFromFile}'. Use semantic versioning (e.g., 1.0.2)")
//                     }
//
//                     env.VERSION = versionFromFile
//                     env.INSTALLER_NAME = "timesync-setup-${env.VERSION}.exe"
//                     env.LOCAL_INSTALLER_PATH = "installer/${env.INSTALLER_NAME}"
//
//                     echo "📋 Version from file: ${env.VERSION}"
//                     echo "📦 Installer name: ${env.INSTALLER_NAME}"
//                     echo "📝 Release notes: ${params.RELEASE_NOTES}"
//                 }
//             }
//         }
//
//         stage('Check Existing Version') {
//             steps {
//                 script {
//                     echo "Checking if version ${env.VERSION} already exists on server..."
//
//                     def checkResult = sh(
//                         script: "ssh ${env.SERVER_USER}@${env.SERVER_HOST} 'test -f ${env.SERVER_PATH}/${env.INSTALLER_NAME} && echo EXISTS || echo NOT_EXISTS'",
//                         returnStdout: true
//                     ).trim()
//
//                     if (checkResult == 'EXISTS' && !params.FORCE_BUILD) {
//                         error("Version ${env.VERSION} already exists on server. Use FORCE_BUILD to overwrite.")
//                     } else if (checkResult == 'EXISTS') {
//                         echo "Version exists but FORCE_BUILD is enabled. Will overwrite."
//                     } else {
//                         echo "Version ${env.VERSION} does not exist. Proceeding with build."
//                     }
//                 }
//             }
//         }
//
//         stage('Build') {
//             steps {
//                 script {
//                     echo "Building installer for version ${env.VERSION}..."
//
//                     // Install Python and NSIS if not available
//                     sh """
//                         # Install Python3 if not available
//                         if ! command -v python3 &> /dev/null; then
//                             apt update
//                             apt install -y python3 python3-venv
//                         fi
//
//                         # Install NSIS if not available
//                         if ! command -v makensis &> /dev/null; then
//                             echo "Installing NSIS..."
//                             apt update
//                             apt install -y nsis
//                         else
//                             echo "NSIS already installed"
//                         fi
//
//                         # Set up Python virtual environment
//                         python3 -m venv .venv
//                         . .venv/bin/activate
//
//                         # Install Python dependencies
//                         pip install -r requirements.txt
//                     """
//
//
//                     // Clean previous builds
//                     sh "rm -rf dist/ build/ installer/"
//
//                     // Run the build script
//                     sh "python3 ci_build.py --version ${env.VERSION}"
//
//                     // Verify the installer was created
//                     if (!fileExists(env.LOCAL_INSTALLER_PATH)) {
//                         error("Build failed: ${env.LOCAL_INSTALLER_PATH} was not created")
//                     }
//
//                     // Get file size for logging
//                     def fileSize = sh(
//                         script: "stat -c%s '${env.LOCAL_INSTALLER_PATH}'",
//                         returnStdout: true
//                     ).trim()
//
//                     echo "Build successful: ${env.INSTALLER_NAME} (${fileSize} bytes)"
//
//                     // Archive the build artifact in Jenkins
//                     archiveArtifacts artifacts: "installer/*.exe", fingerprint: true
//                 }
//             }
//         }
//
//         stage('Deploy') {
//             steps {
//                 script {
//                     echo "Deploying installer to update server..."
//
//                     // Copy file to server using scp
//                     sh """
//                         scp '${env.LOCAL_INSTALLER_PATH}' ${env.SERVER_USER}@${env.SERVER_HOST}:${env.SERVER_PATH}/
//                     """
//
//                     // Set proper permissions
//                     sh """
//                         ssh ${env.SERVER_USER}@${env.SERVER_HOST} 'chmod 644 ${env.SERVER_PATH}/${env.INSTALLER_NAME}'
//                     """
//
//                     // Verify file was uploaded correctly
//                     def remoteSize = sh(
//                         script: "ssh ${env.SERVER_USER}@${env.SERVER_HOST} 'stat -c%s ${env.SERVER_PATH}/${env.INSTALLER_NAME}'",
//                         returnStdout: true
//                     ).trim()
//
//                     echo "Deployment successful: ${env.INSTALLER_NAME} uploaded (${remoteSize} bytes)"
//                 }
//             }
//         }
//
//         stage('Register Version') {
//             steps {
//                 script {
//                     echo "Registering version ${env.VERSION} with update server..."
//
//                     // Prepare API request payload
//                     def payload = groovy.json.JsonBuilder([
//                         version: env.VERSION,
//                         notes: params.RELEASE_NOTES
//                     ]).toString()
//
//                     // Make API call to register version
//                     def response = sh(
//                         script: """
//                             curl -X POST '${env.UPDATE_SERVER_URL}/api/admin/versions/add' \\
//                                  -H 'admin-key: ${env.ADMIN_KEY}' \\
//                                  -H 'Content-Type: application/json' \\
//                                  -d '${payload}' \\
//                                  -w '%{http_code}' \\
//                                  -s -o response.json
//                         """,
//                         returnStdout: true
//                     ).trim()
//
//                     // Check response
//                     if (response == '200' || response == '201') {
//                         echo "Version ${env.VERSION} registered successfully"
//
//                         // Log the response for debugging
//                         if (fileExists('response.json')) {
//                             def responseContent = readFile('response.json').trim()
//                             echo "API Response: ${responseContent}"
//                         }
//                     } else {
//                         def errorContent = fileExists('response.json') ? readFile('response.json') : 'No response content'
//                         error("Failed to register version. HTTP Status: ${response}. Response: ${errorContent}")
//                     }
//                 }
//             }
//         }
//     }
//
//     post {
//         success {
//             echo "✅ Successfully deployed version ${env.VERSION}"
//             echo "📦 Installer: ${env.INSTALLER_NAME}"
//             echo "🔗 Download will be available at: ${env.UPDATE_SERVER_URL}/api/updates/download"
//         }
//         failure {
//             echo "❌ Pipeline failed for version ${env.VERSION}"
//         }
//         always {
//             // Clean up temporary files
//             sh "rm -f response.json"
//             echo "Pipeline completed for version ${env.VERSION}"
//         }
//     }
// }