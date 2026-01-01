#!/usr/bin/env python3
"""
Add sample records to DynamoDB for testing
"""
import os
import sys

# Set up DynamoDB environment
os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'test'
os.environ['DYNAMODB_TABLE'] = 'jukebox-records-prod'

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from dynamodb_models import JukeboxRecord, JukeboxStatus

def add_sample_records():
    """Add sample jukebox records to DynamoDB"""
    
    sample_records = [
        {
            'track_a_side': 'Hey Jude',
            'track_b_side': 'Revolution',
            'artist_a_side': 'The Beatles',
            'artist_b_side': 'The Beatles',
            'genre': 'Rock',
            'status': JukeboxStatus.IN_JUKEBOX,
            'jukebox_id': '001'
        },
        {
            'track_a_side': 'So What',
            'track_b_side': 'Kind of Blue',
            'artist_a_side': 'Miles Davis',
            'artist_b_side': 'Miles Davis',
            'genre': 'Jazz',
            'status': JukeboxStatus.IN_JUKEBOX,
            'jukebox_id': '002'
        },
        {
            'track_a_side': 'Like a Virgin',
            'track_b_side': 'Material Girl',
            'artist_a_side': 'Madonna',
            'artist_b_side': 'Madonna',
            'genre': 'Pop',
            'status': JukeboxStatus.IN_STORAGE,
            'jukebox_id': None
        },
        {
            'track_a_side': 'Ring of Fire',
            'track_b_side': 'I Walk the Line',
            'artist_a_side': 'Johnny Cash',
            'artist_b_side': 'Johnny Cash',
            'genre': 'Country',
            'status': JukeboxStatus.NEW,
            'jukebox_id': None
        },
        {
            'track_a_side': 'The Thrill Is Gone',
            'track_b_side': 'Sweet Little Angel',
            'artist_a_side': 'B.B. King',
            'artist_b_side': 'B.B. King',
            'genre': 'Blues',
            'status': JukeboxStatus.IN_JUKEBOX,
            'jukebox_id': '003'
        }
    ]
    
    print(f"Adding {len(sample_records)} sample records to DynamoDB...")
    
    for i, record_data in enumerate(sample_records):
        try:
            record = JukeboxRecord(**record_data)
            record.save()
            print(f"✅ Added: {record_data['artist_a_side']} - {record_data['track_a_side']}")
        except Exception as e:
            print(f"❌ Failed to add record {i+1}: {e}")
    
    print("\nSample records added successfully!")
    
    # Verify by listing all records
    print("\nVerifying records in DynamoDB:")
    all_records = JukeboxRecord.scan_all()
    print(f"Total records in database: {len(all_records)}")
    
    for record in all_records:
        print(f"- {record.artist_a_side} - {record.track_a_side} ({record.status.value})")

if __name__ == '__main__':
    add_sample_records()