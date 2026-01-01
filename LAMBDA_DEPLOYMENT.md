# AWS Lambda Deployment Guide

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Node.js** installed for Serverless Framework
3. **Domain certificate** for `*.tcla.me` in AWS Certificate Manager
4. **Route53 hosted zone** for `tcla.me` domain

## Quick Deploy

```bash
# Run the deployment script
./deploy.sh
```

## Manual Deployment Steps

### 1. Install Dependencies
```bash
npm install
```

### 2. Set Environment Variables
```bash
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(16))")
export DATABASE_URL="sqlite:///tmp/jukebox.db"  # Or your RDS URL
```

### 3. Deploy to AWS
```bash
serverless deploy --stage prod
```

## Database Considerations

### Option 1: SQLite (Current - Limited)
- Uses `/tmp` directory in Lambda
- **Limitation**: Data is lost between cold starts
- Good for: Testing, temporary storage

### Option 2: RDS (Recommended for Production)
```bash
export DATABASE_URL="mysql://username:password@rds-endpoint:3306/jukebox"
```

### Option 3: DynamoDB (Serverless Native)
- Would require code changes to use DynamoDB instead of SQLAlchemy
- Fully serverless and scales automatically

## Static Files

The app currently serves files locally. For production:

1. **Upload static files to S3**:
```bash
aws s3 sync output/ s3://jukebox-static-files/output/
```

2. **Update code to use S3 URLs** for generated PDFs

## Environment Configuration

Key environment variables:
- `SECRET_KEY`: Flask session secret
- `DATABASE_URL`: Database connection string
- `S3_BUCKET`: For static file storage (optional)

## Monitoring and Logs

```bash
# View logs
serverless logs -f app

# Monitor function
aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Invocations --dimensions Name=FunctionName,Value=jukebox-app-prod-app --start-time 2024-01-01T00:00:00Z --end-time 2024-01-02T00:00:00Z --period 3600 --statistics Sum
```

## Custom Domain

The deployment automatically sets up `jukebox.tcla.me` with:
- SSL certificate from ACM
- Route53 DNS record
- API Gateway custom domain

## Scaling and Performance

- **Memory**: 512MB (adjustable in serverless.yml)
- **Timeout**: 30 seconds (adjustable)
- **Cold starts**: ~2-3 seconds for first request
- **Concurrent executions**: 1000 (default AWS limit)

## Cost Optimization

- Lambda pricing: Pay per request and execution time
- API Gateway: Pay per API call
- Consider reserved capacity for high traffic

## Troubleshooting

### Common Issues:
1. **Import errors**: Ensure all dependencies are in requirements.txt
2. **Database connection**: Check DATABASE_URL and VPC configuration
3. **Static files**: Consider S3 for file storage
4. **Memory issues**: Increase memorySize in serverless.yml

### Debug locally:
```bash
python lambda_function.py
```

## Cleanup

To remove all AWS resources:
```bash
serverless remove
```