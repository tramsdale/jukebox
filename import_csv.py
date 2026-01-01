#!/usr/bin/env python3
"""
Script to import CSV jukebox records into the database.
"""

import csv
from app import app, db
from models import JukeboxRecord, JukeboxStatus

def import_csv_file(filename):
    with app.app_context():
        # Clear existing records first (optional)
        # JukeboxRecord.query.delete()
        # db.session.commit()
        # print('Cleared existing records')
        
        # Read the CSV file
        with open(filename, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            imported_count = 0
            skipped_count = 0
            
            for row in csv_reader:
                # Skip rows with missing essential data
                if not row.get('Artist A side') or not row.get('Track A side'):
                    print(f"Skipping row - missing artist or track: {row}")
                    skipped_count += 1
                    continue
                
                # Map the status from CSV to our enum
                in_jukebox_value = row.get('In Jukebox', '').strip()
                if in_jukebox_value in ['Y', '`']:
                    status = JukeboxStatus.IN_JUKEBOX
                elif in_jukebox_value == 'New':
                    status = JukeboxStatus.NEW
                else:
                    status = JukeboxStatus.IN_STORAGE
                
                # Get jukebox ID (format as 3-digit string)
                jukebox_id_raw = row.get('Jukebox ID', '').strip()
                jukebox_id = None
                if jukebox_id_raw and jukebox_id_raw.isdigit():
                    jukebox_id = str(int(jukebox_id_raw)).zfill(3)
                
                # Check if record already exists
                existing = JukeboxRecord.query.filter(
                    JukeboxRecord.artist_a_side == row['Artist A side'].strip(),
                    JukeboxRecord.track_a_side == row['Track A side'].strip()
                ).first()
                
                if existing:
                    print(f"Skipping duplicate: {row['Artist A side']} - {row['Track A side']}")
                    skipped_count += 1
                    continue
                
                # Create new record
                record = JukeboxRecord(
                    track_a_side=row['Track A side'].strip(),
                    track_b_side=row.get('Track B side', '').strip() or 'Unknown',
                    artist_a_side=row['Artist A side'].strip(),
                    artist_b_side=row.get('Artist B side', '').strip() or row['Artist A side'].strip(),
                    genre=row.get('Genre', '').strip() or None,
                    status=status,
                    jukebox_id=jukebox_id
                )
                
                db.session.add(record)
                imported_count += 1
                
                if imported_count % 10 == 0:
                    print(f"Processed {imported_count} records...")
            
            db.session.commit()
            print(f'Successfully imported {imported_count} records!')
            print(f'Skipped {skipped_count} records')
            
            # Show some statistics
            total = JukeboxRecord.query.count()
            in_jukebox = JukeboxRecord.query.filter_by(status=JukeboxStatus.IN_JUKEBOX).count()
            new_records = JukeboxRecord.query.filter_by(status=JukeboxStatus.NEW).count()
            in_storage = JukeboxRecord.query.filter_by(status=JukeboxStatus.IN_STORAGE).count()
            wishlist = JukeboxRecord.query.filter_by(status=JukeboxStatus.WISHLIST).count()
            
            print(f'\nDatabase Statistics:')
            print(f'Total records: {total}')
            print(f'In Jukebox: {in_jukebox}')
            print(f'New: {new_records}')
            print(f'In Storage: {in_storage}')
            print(f'Wishlist: {wishlist}')

if __name__ == '__main__':
    import_csv_file('jukebox_records.csv')