#!/bin/bash

echo "🚀 Deploying Jukebox to AWS Lambda..."

# Install serverless framework if not already installed
if ! command -v serverless &> /dev/null; then
    echo "Installing Serverless Framework..."
    npm install -g serverless
fi

# Install serverless plugins
echo "Installing Serverless plugins..."
npm install --save-dev serverless-python-requirements
npm install --save-dev serverless-wsgi  
npm install --save-dev serverless-domain-manager

# Set up environment variables
echo "Setting up environment variables..."
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(16))")
    echo "Generated SECRET_KEY: $SECRET_KEY"
fi

# Deploy to AWS
echo "Deploying to AWS Lambda..."
serverless deploy --stage prod

echo "✅ Deployment complete!"
echo ""
echo "🌐 Your jukebox app should be available at:"
echo "   https://jukebox.tcla.me"
echo ""
echo "📊 AWS Resources created:"
echo "   • Lambda function: jukebox-app-prod-app"
echo "   • API Gateway: Custom domain jukebox.tcla.me"
echo "   • CloudFormation stack: jukebox-app-prod"
echo ""
echo "🔧 To update the deployment:"
echo "   serverless deploy"
echo ""
echo "🗑️  To remove the deployment:"
echo "   serverless remove"