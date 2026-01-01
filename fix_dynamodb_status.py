#!/usr/bin/env python3
"""
Fix existing DynamoDB records that have old status enum values
"""
import os
import sys
import boto3

# Set up DynamoDB environment
os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'fix'
os.environ['DYNAMODB_TABLE'] = 'jukebox-records-prod'

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def fix_status_values():
    """Fix old status enum values in DynamoDB"""
    
    # Direct DynamoDB access
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
    table = dynamodb.Table('jukebox-records-prod')
    
    # Mapping from old values to new values
    status_mapping = {
        'in_jukebox': 'In Jukebox',
        'new': 'New', 
        'in_storage': 'In Storage'
    }
    
    print("Scanning DynamoDB for records with old status values...")
    
    try:
        # Scan all items
        response = table.scan()
        items = response['Items']
        
        print(f"Found {len(items)} total records")
        
        updated_count = 0
        
        for item in items:
            old_status = item.get('status')
            if old_status in status_mapping:
                new_status = status_mapping[old_status]
                
                print(f"Updating record {item['id']}: '{old_status}' -> '{new_status}'")
                
                # Update the item
                table.update_item(
                    Key={'id': item['id']},
                    UpdateExpression='SET #status = :new_status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':new_status': new_status}
                )
                
                updated_count += 1
        
        print(f"\\nFixed {updated_count} records with old status values")
        
        # Verify the fix
        print("\\nVerifying fix by scanning again...")
        response = table.scan()
        items = response['Items']
        
        status_counts = {}
        for item in items:
            status = item.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("Current status distribution:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    fix_status_values()