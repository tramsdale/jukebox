"""
AWS Lambda handler for the jukebox Flask application with DynamoDB
"""
import os
import sys
import logging
import json
import base64
import serverless_wsgi

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Set Lambda environment detection
os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'jukebox-app-prod-app'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Flask app after environment is set
from app import app

def lambda_handler(event, context):
    """AWS Lambda handler function with binary response handling"""
    try:
        logger.info("Lambda handler started")
        logger.error("=== LAMBDA HANDLER CALLED ===")  # Use ERROR level to ensure we see it
        
        # Use serverless_wsgi to handle the Flask app
        response = serverless_wsgi.handle_request(app, event, context)
        logger.error(f"Got response from serverless-wsgi: status={response.get('statusCode')}")
        
        # Check both headers and multiValueHeaders
        headers = response.get('headers', {})
        multi_headers = response.get('multiValueHeaders', {})
        logger.error(f"Headers: {headers}")
        logger.error(f"MultiValueHeaders: {multi_headers}")
        
        # Try to get Content-Type from either location
        content_type = headers.get('Content-Type', '') or headers.get('content-type', '')
        if not content_type and multi_headers:
            content_type_list = multi_headers.get('Content-Type', []) or multi_headers.get('content-type', [])
            if content_type_list:
                content_type = content_type_list[0]
        
        # Try to get Content-Disposition from either location  
        content_disposition = headers.get('Content-Disposition', '') or headers.get('content-disposition', '')
        if not content_disposition and multi_headers:
            content_disp_list = multi_headers.get('Content-Disposition', []) or multi_headers.get('content-disposition', [])
            if content_disp_list:
                content_disposition = content_disp_list[0]
                
        logger.error(f"Final Content-Type: '{content_type}'")
        logger.error(f"Final Content-Disposition: '{content_disposition}'")
        
        # Check if this looks like a PDF response
        is_pdf = ('application/pdf' in content_type.lower() or 
                 'pdf' in content_disposition.lower())
        
        if is_pdf:
            body = response.get('body', '')
            logger.error(f"PDF detected - body type: {type(body)}, length: {len(body) if body else 0}")
            
            if body:
                # serverless-wsgi already base64-encoded the binary PDF content
                # Decode it back to raw binary and let API Gateway handle it as binary
                try:
                    decoded_bytes = base64.b64decode(body, validate=True)
                    logger.error(f"Base64 decode successful - decoded length: {len(decoded_bytes)}")
                    logger.error(f"Decoded first 20 bytes: {decoded_bytes[:20]}")
                    
                    if decoded_bytes.startswith(b'%PDF'):
                        logger.error("Decoded content is valid PDF - returning as raw binary")
                        
                        # Combine all headers properly
                        final_headers = dict(headers)
                        final_headers['Content-Type'] = 'application/pdf'
                        if content_disposition:
                            final_headers['Content-Disposition'] = content_disposition
                        
                        # Return raw binary data (decode to latin-1 string for Lambda)
                        binary_body = decoded_bytes.decode('latin-1')
                        logger.error(f"Returning binary body length: {len(binary_body)}")
                        
                        return {
                            'statusCode': 200,
                            'headers': final_headers,
                            'body': binary_body,
                            'isBase64Encoded': False
                        }
                    else:
                        logger.error("Decoded content is not PDF - fallback")
                except Exception as e:
                    logger.error(f"Base64 decode failed ({e})")
                
                # Fallback 
                final_headers = dict(headers)
                final_headers['Content-Type'] = 'application/pdf'
                if content_disposition:
                    final_headers['Content-Disposition'] = content_disposition
                    
                return {
                    'statusCode': 200,
                    'headers': final_headers,
                    'body': body,
                    'isBase64Encoded': True
                }
        
        # Return the response as-is for non-PDF content
        return response
        
    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        logger.error(f"Error type: {type(e)}")
        
        # Import traceback for full error details
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Return error response
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }