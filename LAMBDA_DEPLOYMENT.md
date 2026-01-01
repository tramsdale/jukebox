# AWS Lambda Deployment Guide - Production with S3 Database

## Overview

This production deployment uses S3-backed SQLite database storage, providing:
- ✅ **Persistent data storage** across Lambda cold starts
- ✅ **Automatic database synchronization** after write operations  
- ✅ **Database versioning** with S3 versioning enabled
- ✅ **Cost-effective storage** compared to RDS
- ✅ **Zero-maintenance** database infrastructure

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Node.js** installed for Serverless Framework
3. **Domain certificate** for `*.tcla.me` in AWS Certificate Manager
4. **Route53 hosted zone** for `tcla.me` domain
5. **S3 permissions** for database storage

## Quick Deploy

```bash
# 1. Set up production database in S3
./setup_production_db.py

# 2. Deploy to Lambda
./deploy.sh
```

## Manual Deployment Steps

### 1. Initialize Production Database
```bash
python setup_production_db.py
```

This script will:
- Create S3 bucket with versioning and security
- Import your existing CSV data (if available)
- Upload initial database to S3
- Configure proper permissions

### 2. Install Dependencies
```bash
npm install
```

### 3. Set Environment Variables
```bash
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(16))")
export S3_BUCKET="jukebox-database-storage-prod"
export DB_S3_KEY="database/jukebox.db"
```

### 4. Deploy to AWS
```bash
serverless deploy --stage prod
```

## Database Architecture

### S3-Backed SQLite
- **Storage**: SQLite database stored in S3
- **Sync Strategy**: 
  - Downloads database from S3 on Lambda startup
  - Uploads changes back to S3 after write operations
- **Concurrency**: Single-writer model (suitable for typical usage)
- **Backup**: S3 versioning provides automatic backups

### Database Flow
1. **Lambda Cold Start**: Downloads `jukebox.db` from S3 to `/tmp/`
2. **Read Operations**: Direct SQLite queries on local file
3. **Write Operations**: SQLite write + automatic S3 upload
4. **Lambda Termination**: Changes already saved to S3

## Production Features

### Automatic Database Sync
- Middleware monitors HTTP methods (POST, PUT, DELETE)
- Successful write operations trigger S3 upload
- Failed uploads are logged but don't break the app

### S3 Bucket Configuration
- **Versioning**: Enabled for data protection
- **Encryption**: AES-256 server-side encryption
- **Access**: Private with IAM role permissions only
- **Structure**: `s3://jukebox-database-storage-prod/database/jukebox.db`

### Error Handling
- Database download failures create new database
- Upload failures are logged but don't block requests  
- Connection pooling for reliability
- Graceful degradation

## Monitoring and Maintenance

### CloudWatch Logs
```bash
# View Lambda logs
serverless logs -f app --tail

# Check database sync operations
aws logs filter-log-events --log-group-name /aws/lambda/jukebox-app-prod-app --filter-pattern "database"
```

### Database Backup
S3 versioning provides automatic point-in-time backups:
```bash
# List database versions
aws s3api list-object-versions --bucket jukebox-database-storage-prod --prefix database/jukebox.db

# Restore specific version
aws s3api copy-object --copy-source "jukebox-database-storage-prod/database/jukebox.db?versionId=VERSION_ID" --bucket jukebox-database-storage-prod --key database/jukebox.db
```

### Manual Database Operations
```bash
# Download current database
aws s3 cp s3://jukebox-database-storage-prod/database/jukebox.db ./

# Upload updated database
aws s3 cp ./jukebox.db s3://jukebox-database-storage-prod/database/jukebox.db
```

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