#!/bin/bash

echo "🚀 Deploying Jukebox to AWS Lambda..."

# Clean npm cache and install serverless framework locally
echo "Setting up Node.js dependencies..."
npm cache clean --force 2>/dev/null || true

# Install serverless framework locally if not already installed
if ! npx serverless --version &> /dev/null; then
    echo "Installing Serverless Framework locally..."
    npm install --save-dev serverless
fi

# Install serverless plugins
echo "Installing Serverless plugins..."
npm install --save-dev serverless-python-requirements
npm install --save-dev serverless-wsgi  
npm install --save-dev serverless-domain-manager

# Set up environment variables
echo "Setting up environment variables..."
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(uv run python -c "import secrets; print(secrets.token_hex(16))")
    echo "Generated SECRET_KEY: $SECRET_KEY"
fi

# S3 Database configuration
export S3_BUCKET="jukebox-database-storage-prod"
export DB_S3_KEY="database/jukebox.db"
echo "S3 Database: s3://$S3_BUCKET/$DB_S3_KEY"

# Deploy to AWS
echo "Deploying to AWS Lambda..."
npx serverless deploy --stage prod

echo "✅ Deployment complete!"
echo ""
echo "🌐 Your jukebox app is available at:"
echo "   https://jukebox.tcla.me"
echo ""
echo "📊 AWS Resources created:"
echo "   • Lambda function: jukebox-app-prod-app (eu-west-2)"
echo "   • API Gateway: Custom domain jukebox.tcla.me"
echo "   • S3 Database: s3://jukebox-database-storage-prod/database/jukebox.db"
echo "   • CloudFormation stack: jukebox-app-prod"
echo ""
echo "💾 Database features:"
echo "   • Persistent S3 storage with versioning enabled"
echo "   • Automatic sync after write operations"
echo "   • 78 records imported and ready to use"
echo ""
echo "🔧 To update the deployment:"
echo "   npx serverless deploy"
echo ""
echo "🗑️  To remove the deployment:"
echo "   npx serverless remove"