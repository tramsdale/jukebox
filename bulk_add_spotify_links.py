#!/usr/bin/env python3
"""
Bulk add Spotify links to existing records in DynamoDB.

This script will:
1. Scan all records in the database
2. For each record, try to find Spotify links for A-side and B-side tracks
3. Update the records with found Spotify URLs

Before running:
1. Set up Spotify API credentials (see test_spotify.py for instructions)
2. Make sure your AWS credentials are configured for DynamoDB access

Usage:
    python bulk_add_spotify_links.py [--force-refresh] [--limit N]
    
Options:
    --force-refresh  Refresh Spotify links even if they already exist
    --limit N        Only process N records (useful for testing)
"""

import argparse
import os
import sys
from dynamodb_models import JukeboxRecord
from spotify_service import spotify_service
import time

def bulk_add_spotify_links(force_refresh=False, limit=None):
    """
    Add Spotify links to all records in the database.
    
    Args:
        force_refresh: If True, refresh existing Spotify links
        limit: Maximum number of records to process (None for all)
    """
    
    print("🎵 Bulk Adding Spotify Links")
    print("=" * 50)
    
    # Check Spotify service
    if not spotify_service.is_available():
        print("❌ Spotify service not available")
        print("Please check your SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")
        return
    
    print("✅ Spotify service available")
    
    # Get all records
    print("📥 Fetching records from database...")
    records = JukeboxRecord.scan_all()
    
    if not records:
        print("📭 No records found in database")
        return
    
    total_records = len(records)
    if limit:
        records = records[:limit]
        print(f"🔢 Processing {len(records)} of {total_records} records (limited)")
    else:
        print(f"🔢 Processing all {total_records} records")
    
    # Process records
    successful_updates = 0
    errors = []
    
    for i, record in enumerate(records, 1):
        print(f"\n[{i}/{len(records)}] Processing: {record.artist_a_side} - {record.track_a_side}")
        
        try:
            # Skip if already has links and not forcing refresh
            if not force_refresh and record.spotify_a_side_url and record.spotify_b_side_url:
                print("   ⏭️  Already has Spotify links, skipping")
                continue
            
            # Fetch Spotify links
            result = record.fetch_spotify_links(force_refresh=force_refresh)
            
            if result['success']:
                found_links = []
                if record.spotify_a_side_url:
                    found_links.append(f"A-side: {record.spotify_a_side_url}")
                if record.spotify_b_side_url:
                    found_links.append(f"B-side: {record.spotify_b_side_url}")
                
                if found_links:
                    print("   ✅ Found Spotify links:")
                    for link in found_links:
                        print(f"      {link}")
                    successful_updates += 1
                else:
                    print("   ⚠️  No Spotify links found")
                
                if result.get('errors'):
                    for error in result['errors']:
                        print(f"   ⚠️  {error}")
            else:
                error_msg = f"Record {record.id}: {result.get('error', 'Unknown error')}"
                errors.append(error_msg)
                print(f"   ❌ {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            error_msg = f"Record {record.id}: {str(e)}"
            errors.append(error_msg)
            print(f"   ❌ Error: {str(e)}")
        
        # Small delay to be nice to Spotify API
        time.sleep(0.1)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Summary")
    print(f"✅ Successfully updated: {successful_updates} records")
    print(f"❌ Errors: {len(errors)}")
    
    if errors:
        print("\n🔴 Errors encountered:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"   • {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more errors")
    
    success_rate = (successful_updates / len(records)) * 100 if records else 0
    print(f"\n🎯 Success rate: {success_rate:.1f}%")
    
    if successful_updates > 0:
        print("\n✅ Spotify links have been added to your records!")
        print("💡 You can now display these links in your web interface.")

def main():
    parser = argparse.ArgumentParser(description='Bulk add Spotify links to jukebox records')
    parser.add_argument('--force-refresh', action='store_true',
                       help='Refresh Spotify links even if they already exist')
    parser.add_argument('--limit', type=int, metavar='N',
                       help='Only process N records (useful for testing)')
    
    args = parser.parse_args()
    
    # Check credentials
    if not os.environ.get('SPOTIFY_CLIENT_ID') or not os.environ.get('SPOTIFY_CLIENT_SECRET'):
        print("❌ Spotify credentials not found in environment variables")
        print("\n📝 To set them:")
        print("export SPOTIFY_CLIENT_ID='your_client_id'")
        print("export SPOTIFY_CLIENT_SECRET='your_client_secret'")
        print("\n🔗 Get credentials from: https://developer.spotify.com/dashboard")
        sys.exit(1)
    
    # Confirmation for force refresh
    if args.force_refresh:
        response = input("⚠️  Force refresh will update all existing Spotify links. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
    
    bulk_add_spotify_links(force_refresh=args.force_refresh, limit=args.limit)

if __name__ == "__main__":
    main()