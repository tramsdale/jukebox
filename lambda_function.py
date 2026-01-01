"""
AWS Lambda handler for the jukebox Flask application
"""
import os
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db
import tempfile

# Configure for Lambda environment
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'sqlite:///tmp/jukebox.db'  # Use /tmp for Lambda writable storage
)

# Initialize database in Lambda context
with app.app_context():
    db.create_all()

def lambda_handler(event, context):
    """
    AWS Lambda handler function
    """
    try:
        # Import AWS Lambda WSGI adapter
        from awslambda_wsgi import response
        return response(app, event, context)
    except ImportError:
        # Fallback if awslambda_wsgi not available
        return {
            'statusCode': 500,
            'body': 'Missing awslambda_wsgi dependency'
        }

# For local testing
if __name__ == '__main__':
    app.run(debug=True)