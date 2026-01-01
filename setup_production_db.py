#!/usr/bin/env python3
"""
Script to initialize and populate S3-backed database for production deployment
"""
import os
import boto3
import sys
from pathlib import Path
from botocore.exceptions import ClientError

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def setup_production_database():
    """Set up and populate S3-backed database for production"""
    
    print("🗄️ Setting up S3-backed database for production...")
    
    # Configuration
    bucket_name = input("Enter S3 bucket name (default: jukebox-database-storage-prod): ").strip()
    if not bucket_name:
        bucket_name = "jukebox-database-storage-prod"
    
    db_key = "database/jukebox.db"
    local_db_path = os.path.abspath("instance/jukebox.db")
    
    # Initialize S3 client
    try:
        s3_client = boto3.client('s3', region_name='eu-west-2')
        print(f"✅ Connected to AWS S3")
    except Exception as e:
        print(f"❌ Failed to connect to AWS S3: {e}")
        print("Make sure your AWS credentials are configured (aws configure)")
        return False
    
    # Create S3 bucket if it doesn't exist
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket '{bucket_name}' exists")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"Creating S3 bucket '{bucket_name}'...")
            try:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': 'eu-west-2'}
                )
                
                # Enable versioning
                s3_client.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                
                # Block public access
                s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    }
                )
                
                print(f"✅ Created S3 bucket '{bucket_name}' with versioning and security")
            except Exception as e:
                print(f"❌ Failed to create S3 bucket: {e}")
                return False
        else:
            print(f"❌ Error checking S3 bucket: {e}")
            return False
    
    # Create local database with existing data
    print("🔧 Creating local database...")
    from app import app
    from models import db, JukeboxRecord, JukeboxStatus
    
    # Configure app for local database (use default instance location)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Ensure the instance directory doesn't interfere
    if hasattr(app, 'instance_path'):
        app.instance_path = os.path.dirname(local_db_path)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we should import existing data
        if os.path.exists('jukebox_records.csv'):
            print("📊 Found existing CSV data, importing...")
            import csv
            
            with open('jukebox_records.csv', 'r', encoding='utf-8') as csvfile:
                # Skip BOM if present
                csvfile.seek(0)
                first_bytes = csvfile.read(3)
                if first_bytes != '\ufeff':
                    csvfile.seek(0)
                
                # Read CSV
                csv_reader = csv.DictReader(csvfile)
                records_imported = 0
                
                for row in csv_reader:
                    try:
                        record = JukeboxRecord(
                            artist_a_side=row.get('Artist - A Side', '').strip(),
                            track_a_side=row.get('Track - A Side', '').strip(),
                            artist_b_side=row.get('Artist - B Side', '').strip(),
                            track_b_side=row.get('Track - B Side', '').strip(),
                            genre=row.get('Genre', '').strip() or None,
                            status=JukeboxStatus.IN_JUKEBOX  # Default for imported records
                        )
                        
                        if record.artist_a_side and record.track_a_side:
                            db.session.add(record)
                            records_imported += 1
                    except Exception as e:
                        print(f"⚠️ Error importing record: {e}")
                        continue
                
                db.session.commit()
                print(f"✅ Imported {records_imported} records from CSV")
        else:
            # Create some sample data
            print("📝 Creating sample data...")
            sample_records = [
                JukeboxRecord(
                    artist_a_side="The Beatles",
                    track_a_side="Hey Jude",
                    artist_b_side="The Beatles",
                    track_b_side="Revolution",
                    genre="Rock",
                    status=JukeboxStatus.IN_JUKEBOX,
                    jukebox_id="A01"
                ),
                JukeboxRecord(
                    artist_a_side="Miles Davis",
                    track_a_side="So What",
                    artist_b_side="Miles Davis", 
                    track_b_side="Kind of Blue",
                    genre="Jazz",
                    status=JukeboxStatus.IN_JUKEBOX,
                    jukebox_id="B02"
                )
            ]
            
            for record in sample_records:
                db.session.add(record)
            
            db.session.commit()
            print("✅ Created sample records")
        
        # Get record count
        total_records = JukeboxRecord.query.count()
        print(f"📊 Database contains {total_records} records")
        
        # Close database connections to ensure file is written
        db.session.close()
    
    # Verify database file exists
    if not os.path.exists(local_db_path):
        print(f"❌ Database file not found at {local_db_path}")
        print("Database creation may have failed")
        return False
    
    print(f"✅ Database file created at {local_db_path}")
    
    # Upload database to S3
    print(f"☁️ Uploading database to S3...")
    try:
        s3_client.upload_file(local_db_path, bucket_name, db_key)
        print(f"✅ Database uploaded to s3://{bucket_name}/{db_key}")
    except Exception as e:
        print(f"❌ Failed to upload database to S3: {e}")
        return False
    
    # Cleanup local file
    if os.path.exists(local_db_path):
        os.remove(local_db_path)
        print("🧹 Cleaned up local database file")
    
    print("\n" + "="*60)
    print("🎉 Production database setup complete!")
    print(f"📍 Database location: s3://{bucket_name}/{db_key}")
    print(f"📊 Total records: {total_records}")
    print("\n🚀 Your deployment will now use this S3-backed database")
    print("💡 Database changes will be automatically synced to S3")
    print("🔒 S3 bucket has versioning enabled for data protection")
    
    # Update environment for deployment
    print(f"\n🔧 Set these environment variables for deployment:")
    print(f"export S3_BUCKET={bucket_name}")
    print(f"export DB_S3_KEY={db_key}")
    
    return True

if __name__ == "__main__":
    success = setup_production_database()
    if not success:
        sys.exit(1)