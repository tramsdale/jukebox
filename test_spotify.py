#!/usr/bin/env python3
"""
Test script for Spotify integration.

Before running:
1. Install spotipy: uv add spotipy
2. Get Spotify API credentials:
   - Go to https://developer.spotify.com/dashboard
   - Create an app
   - Copy Client ID and Client Secret
3. Set environment variables:
   export SPOTIFY_CLIENT_ID="your_client_id_here"
   export SPOTIFY_CLIENT_SECRET="your_client_secret_here"

Usage:
    python test_spotify.py
"""

import os
import sys
from spotify_service import spotify_service

def test_spotify_service():
    """Test Spotify service with some sample tracks."""
    
    print("🎵 Testing Spotify Integration")
    print("=" * 50)
    
    # Check if Spotify service is available
    if not spotify_service.is_available():
        print("❌ Spotify service not available")
        print("\n📝 Setup Instructions:")
        print("1. Go to https://developer.spotify.com/dashboard")
        print("2. Create a new app (any name/description)")
        print("3. Copy the Client ID and Client Secret")
        print("4. Set environment variables:")
        print("   export SPOTIFY_CLIENT_ID='your_client_id'")
        print("   export SPOTIFY_CLIENT_SECRET='your_client_secret'")
        print("5. Install spotipy: uv add spotipy")
        return
    
    print("✅ Spotify service initialized successfully")
    print()
    
    # Test tracks from our sample data
    test_tracks = [
        {"artist": "The Beatles", "track": "Hey Jude"},
        {"artist": "Miles Davis", "track": "So What"},
        {"artist": "Madonna", "track": "Like a Virgin"},
        {"artist": "Johnny Cash", "track": "Ring of Fire"},
        {"artist": "B.B. King", "track": "The Thrill Is Gone"},
        {"artist": "Daft Punk", "track": "Around the World"},
        {"artist": "NonExistentArtist", "track": "Fake Song Title"}  # This should fail
    ]
    
    successful_matches = 0
    total_searches = len(test_tracks)
    
    for i, track_info in enumerate(test_tracks, 1):
        artist = track_info["artist"]
        track = track_info["track"]
        
        print(f"🔍 [{i}/{total_searches}] Searching: {artist} - {track}")
        
        result = spotify_service.search_track(artist, track)
        
        if result:
            print(f"   ✅ Found: {result['artist']} - {result['name']}")
            print(f"   🔗 URL: {result['spotify_url']}")
            print(f"   📀 Album: {result['album']}")
            print(f"   📊 Popularity: {result['popularity']}/100")
            if result['preview_url']:
                print(f"   🎵 Preview: Available")
            successful_matches += 1
        else:
            print("   ❌ No match found")
        
        print()
    
    # Summary
    print("=" * 50)
    print(f"📊 Results: {successful_matches}/{total_searches} successful matches")
    success_rate = (successful_matches / total_searches) * 100
    print(f"🎯 Success rate: {success_rate:.1f}%")
    
    if successful_matches > 0:
        print("\n✅ Spotify integration is working!")
        print("💡 You can now use this in your jukebox application to automatically")
        print("   find Spotify links for your vinyl records.")
    else:
        print("\n⚠️  No matches found. This could indicate:")
        print("   - API credentials issue")
        print("   - Network connectivity problem")
        print("   - All test tracks were genuinely not found on Spotify")

def test_batch_search():
    """Test batch searching functionality."""
    
    if not spotify_service.is_available():
        return
        
    print("\n🔄 Testing Batch Search")
    print("=" * 30)
    
    tracks = [
        {"artist": "Elvis Presley", "track": "Can't Help Falling in Love"},
        {"artist": "Queen", "track": "Bohemian Rhapsody"},
        {"artist": "Bob Dylan", "track": "Like a Rolling Stone"}
    ]
    
    results = spotify_service.search_tracks_batch(tracks)
    
    print(f"Found {len(results)} matches from {len(tracks)} searches:")
    for key, info in results.items():
        artist, track = key.split('||')
        print(f"  ✅ {artist} - {track} → {info['spotify_url']}")

if __name__ == "__main__":
    # Check if credentials are set
    if not os.environ.get('SPOTIFY_CLIENT_ID') or not os.environ.get('SPOTIFY_CLIENT_SECRET'):
        print("⚠️  Spotify credentials not found in environment variables")
        print("\n📝 To set them:")
        print("export SPOTIFY_CLIENT_ID='your_client_id'")
        print("export SPOTIFY_CLIENT_SECRET='your_client_secret'")
        print("\n🔗 Get credentials from: https://developer.spotify.com/dashboard")
        sys.exit(1)
    
    test_spotify_service()
    test_batch_search()
    
    print("\n🚀 Next steps:")
    print("1. Add Spotify links to your database records using fetch_spotify_links()")
    print("2. Display Spotify links in your web interface")
    print("3. Consider adding bulk Spotify link generation for existing records")