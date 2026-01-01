#!/usr/bin/env python3
"""
Migration script to transfer data from SQLite to DynamoDB
Run this locally to migrate existing data before deploying DynamoDB version
"""

import os
import sys
import json
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

def migrate_sqlite_to_dynamodb():
    """Migrate data from local SQLite database to DynamoDB"""
    
    # Set up environment for local SQLite access
    os.environ.pop('AWS_LAMBDA_FUNCTION_NAME', None)
    
    # Import SQLite models
    from models import db, JukeboxRecord as SQLiteRecord, JukeboxStatus
    from app import app as sqlite_app
    
    # Set up DynamoDB environment
    os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'migration'  # Enable DynamoDB mode
    os.environ['DYNAMODB_TABLE'] = 'jukebox-records-prod'  # Target table
    
    # Import DynamoDB models
    from dynamodb_models import JukeboxRecord as DynamoRecord
    
    print("Starting migration from SQLite to DynamoDB...")
    
    with sqlite_app.app_context():
        # Get all records from SQLite
        sqlite_records = SQLiteRecord.query.all()
        print(f"Found {len(sqlite_records)} records in SQLite database")
        
        if not sqlite_records:
            print("No records found to migrate")
            return
        
        # Migrate each record to DynamoDB
        migrated_count = 0
        failed_count = 0
        
        for sqlite_record in sqlite_records:
            try:
                # Convert SQLite record to DynamoDB record
                dynamo_record = DynamoRecord(
                    track_a_side=sqlite_record.track_a_side,
                    track_b_side=sqlite_record.track_b_side,
                    artist_a_side=sqlite_record.artist_a_side,
                    artist_b_side=sqlite_record.artist_b_side,
                    genre=sqlite_record.genre,
                    status=sqlite_record.status,  # Enum should convert properly
                    jukebox_id=sqlite_record.jukebox_id
                )
                
                # Save to DynamoDB
                dynamo_record.save()
                migrated_count += 1
                print(f"Migrated: {sqlite_record.artist_a_side} - {sqlite_record.track_a_side}")
                
            except Exception as e:
                print(f"Failed to migrate record {sqlite_record.id}: {e}")
                failed_count += 1
        
        print("\nMigration complete!")
        print(f"Successfully migrated: {migrated_count} records")
        print(f"Failed to migrate: {failed_count} records")
        
        if failed_count == 0:
            print("\n✅ All records migrated successfully!")
            print("You can now deploy the DynamoDB version.")
        else:
            print(f"\n⚠️  {failed_count} records failed to migrate. Check the errors above.")

def verify_migration():
    """Verify the migration by comparing record counts"""
    
    # Check SQLite count
    os.environ.pop('AWS_LAMBDA_FUNCTION_NAME', None)
    from models import db, JukeboxRecord as SQLiteRecord
    from app import app as sqlite_app
    
    with sqlite_app.app_context():
        sqlite_count = SQLiteRecord.query.count()
    
    # Check DynamoDB count
    os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'migration'
    os.environ['DYNAMODB_TABLE'] = 'jukebox-records-prod'
    
    from dynamodb_models import JukeboxRecord as DynamoRecord
    dynamo_records = DynamoRecord.scan_all()
    dynamo_count = len(dynamo_records)
    
    print(f"SQLite records: {sqlite_count}")
    print(f"DynamoDB records: {dynamo_count}")
    
    if sqlite_count == dynamo_count:
        print("✅ Record counts match!")
        return True
    else:
        print("❌ Record counts don't match!")
        return False

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Migrate jukebox records from SQLite to DynamoDB')
    parser.add_argument('--verify', action='store_true', help='Only verify migration, don\'t migrate')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without actually doing it')
    
    args = parser.parse_args()
    
    if args.verify:
        verify_migration()
    else:
        # Make sure DynamoDB table exists first
        print("Make sure you've deployed the DynamoDB table first:")
        print("npx serverless deploy --region eu-west-2")
        print("")
        
        if input("Have you deployed the DynamoDB infrastructure? (y/N): ").lower() != 'y':
            print("Please deploy first, then run this migration script.")
            sys.exit(1)
        
        migrate_sqlite_to_dynamodb()
        print("\nVerifying migration...")
        verify_migration()