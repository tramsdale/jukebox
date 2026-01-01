"""
AWS Lambda handler for the jukebox Flask application with S3 database persistence
"""
import os
import sys
import boto3
import logging
import json
from pathlib import Path
from botocore.exceptions import ClientError
import serverless_wsgi

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

# S3 configuration
S3_BUCKET = os.environ.get('S3_BUCKET', 'jukebox-database-storage')
DB_S3_KEY = os.environ.get('DB_S3_KEY', 'database/jukebox.db')
LOCAL_DB_PATH = '/tmp/jukebox.db'

# Set Lambda environment detection
os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'jukebox-app-prod-app'

from app import app
from models import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize S3 client
s3_client = boto3.client('s3')

def download_database_from_s3():
    """Download SQLite database from S3 to local storage"""
    try:
        # Ensure the tmp directory exists (but don't try to change its permissions)
        os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)
        
        logger.info(f"Downloading database from s3://{S3_BUCKET}/{DB_S3_KEY}")
        s3_client.download_file(S3_BUCKET, DB_S3_KEY, LOCAL_DB_PATH)
        logger.info("Database downloaded successfully")
        
        # Ensure the database file has proper permissions
        os.chmod(LOCAL_DB_PATH, 0o644)
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            logger.info("Database not found in S3, will create new one")
            return False
        else:
            logger.error(f"Error downloading database: {e}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error downloading database: {e}")
        return False

def upload_database_to_s3():
    """Upload SQLite database from local storage to S3"""
    try:
        if os.path.exists(LOCAL_DB_PATH):
            logger.info(f"Uploading database to s3://{S3_BUCKET}/{DB_S3_KEY}")
            s3_client.upload_file(LOCAL_DB_PATH, S3_BUCKET, DB_S3_KEY)
            logger.info("Database uploaded successfully")
            return True
        else:
            logger.warning("No local database file to upload")
            return False
    except Exception as e:
        logger.error(f"Error uploading database: {e}")
        return False

def initialize_database():
    """Initialize database - download from S3 or create new"""
    logger.info("Starting database initialization")
    
    # Ensure /tmp directory exists
    os.makedirs('/tmp', exist_ok=True)
    logger.info(f"Ensured /tmp directory exists")
    
    # Configure Flask app for S3-backed database first
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{LOCAL_DB_PATH}'
    logger.info(f"Set database URI to: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Try to download existing database from S3
    logger.info("Attempting to download database from S3")
    db_exists = download_database_from_s3()
    logger.info(f"Database download result: {db_exists}")
    
    # Initialize database tables if needed
    with app.app_context():
        try:
            if not db_exists:
                # Ensure directory exists and create empty database file
                os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)
                if not os.path.exists(LOCAL_DB_PATH):
                    logger.info("Creating empty database file")
                    try:
                        # Create the file with proper permissions
                        Path(LOCAL_DB_PATH).touch()
                        os.chmod(LOCAL_DB_PATH, 0o644)
                        logger.info(f"Created database file: {LOCAL_DB_PATH}")
                    except Exception as create_error:
                        logger.error(f"Failed to create database file: {create_error}")
                        raise
                
                logger.info("Creating new database tables")
                db.create_all()
                # Upload the newly created database to S3
                upload_database_to_s3()
            else:
                # Verify file exists and has proper permissions
                if os.path.exists(LOCAL_DB_PATH):
                    os.chmod(LOCAL_DB_PATH, 0o644)
                    logger.info(f"Database file verified: {LOCAL_DB_PATH} (size: {os.path.getsize(LOCAL_DB_PATH)} bytes)")
                else:
                    logger.error(f"Database file missing after download: {LOCAL_DB_PATH}")
                    raise Exception("Database file missing after S3 download")
                
                # Ensure all tables exist (for schema migrations)
                logger.info("Verifying existing database tables")
                db.create_all()
                
            logger.info("Database initialization completed successfully")
        except Exception as e:
            logger.error(f"Error during database initialization: {e}")
            # Log additional debugging info
            logger.error(f"Current directory: {os.getcwd()}")
            logger.error(f"/tmp directory exists: {os.path.exists('/tmp')}")
            logger.error(f"/tmp directory permissions: {oct(os.stat('/tmp').st_mode) if os.path.exists('/tmp') else 'N/A'}")
            logger.error(f"Database path: {LOCAL_DB_PATH}")
            logger.error(f"Database path parent exists: {os.path.exists(os.path.dirname(LOCAL_DB_PATH))}")
            raise

# Don't initialize database at import time - do it on first request

class DatabaseSyncMiddleware:
    """Middleware to sync database changes back to S3"""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
        self.write_operations = {'POST', 'PUT', 'DELETE', 'PATCH'}
    
    def __call__(self, environ, start_response):
        # Check if this is a write operation
        method = environ.get('REQUEST_METHOD', 'GET')
        is_write = method in self.write_operations
        
        def custom_start_response(status, headers, exc_info=None):
            # Sync database to S3 after successful write operations
            if is_write and status.startswith('2'):  # 2xx status codes
                try:
                    upload_database_to_s3()
                except Exception as e:
                    logger.error(f"Failed to sync database to S3: {e}")
            return start_response(status, headers, exc_info)
        
        return self.wsgi_app(environ, custom_start_response)

# Apply middleware to sync database changes
app.wsgi_app = DatabaseSyncMiddleware(app.wsgi_app)

def lambda_handler(event, context):
    """
    AWS Lambda handler function
    """
    try:
        # Ensure database is downloaded and initialized before handling request
        if not os.path.exists(LOCAL_DB_PATH):
            logger.info("Database not found locally, initializing...")
            initialize_database()
        else:
            # Database exists, but make sure tables are created (for schema migrations)
            with app.app_context():
                try:
                    # Test database connection first
                    with db.engine.connect() as conn:
                        conn.execute(db.text('SELECT 1'))
                    db.create_all()
                    logger.info("Database tables verified/created")
                except Exception as e:
                    logger.error(f"Error verifying database tables: {e}")
                    # Re-initialize if there's an issue
                    logger.info("Re-initializing database due to verification error")
                    initialize_database()
        
        # Use serverless-wsgi to handle the WSGI application
        return serverless_wsgi.handle_request(app, event, context)
        
    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Return a proper error response
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }

# For local testing
if __name__ == '__main__':
    app.run(debug=True)