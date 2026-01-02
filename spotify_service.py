"""
Spotify integration service for finding track links
"""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class SpotifyService:
    """Service for interacting with Spotify Web API to find track links."""
    
    def __init__(self):
        """Initialize Spotify client with credentials from environment variables."""
        self.client_id = os.environ.get('SPOTIFY_CLIENT_ID')
        self.client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            logger.warning("Spotify credentials not found. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.")
            self.spotify = None
            return
            
        try:
            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            logger.info("Spotify client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}")
            self.spotify = None
    
    def is_available(self) -> bool:
        """Check if Spotify service is available."""
        return self.spotify is not None
    
    def search_track(self, artist: str, track: str) -> Optional[Dict]:
        """
        Search for a track on Spotify and return the best match.
        
        Args:
            artist: Artist name
            track: Track/song name
            
        Returns:
            Dictionary with track info including Spotify URL, or None if not found
        """
        if not self.is_available():
            logger.warning("Spotify service not available")
            return None
            
        if not artist or not track:
            logger.warning("Artist and track name are required")
            return None
            
        try:
            # Clean up search terms
            artist_clean = self._clean_search_term(artist)
            track_clean = self._clean_search_term(track)
            
            # Search with artist and track
            query = f"artist:{artist_clean} track:{track_clean}"
            results = self.spotify.search(q=query, type='track', limit=10)
            
            if not results['tracks']['items']:
                # Try broader search without artist constraint
                query = f"{artist_clean} {track_clean}"
                results = self.spotify.search(q=query, type='track', limit=10)
            
            if not results['tracks']['items']:
                logger.info(f"No Spotify results found for: {artist} - {track}")
                return None
            
            # Find the best match (first result is usually the best)
            best_match = results['tracks']['items'][0]
            
            return {
                'spotify_id': best_match['id'],
                'spotify_url': best_match['external_urls']['spotify'],
                'name': best_match['name'],
                'artist': best_match['artists'][0]['name'] if best_match['artists'] else '',
                'album': best_match['album']['name'],
                'preview_url': best_match.get('preview_url'),
                'popularity': best_match.get('popularity', 0),
                'duration_ms': best_match.get('duration_ms', 0)
            }
            
        except Exception as e:
            logger.error(f"Error searching Spotify for {artist} - {track}: {e}")
            return None
    
    def search_tracks_batch(self, tracks: List[Dict[str, str]]) -> Dict[str, Dict]:
        """
        Search for multiple tracks in batch.
        
        Args:
            tracks: List of dictionaries with 'artist' and 'track' keys
            
        Returns:
            Dictionary mapping track keys to Spotify info
        """
        results = {}
        
        for track_info in tracks:
            artist = track_info.get('artist', '')
            track = track_info.get('track', '')
            key = f"{artist}||{track}"  # Use || as separator to avoid conflicts
            
            spotify_info = self.search_track(artist, track)
            if spotify_info:
                results[key] = spotify_info
                
        return results
    
    def _clean_search_term(self, term: str) -> str:
        """Clean search terms for better Spotify matching."""
        if not term:
            return ""
            
        # Remove common suffixes and prefixes that might interfere
        term = term.strip()
        
        # Remove featuring, ft., etc. - these can sometimes hurt search results
        # We'll keep them for now but could add more cleaning if needed
        
        # Remove extra whitespace
        term = ' '.join(term.split())
        
        return term

# Global instance
spotify_service = SpotifyService()

def get_spotify_link(artist: str, track: str) -> Optional[str]:
    """
    Convenience function to get Spotify link for a track.
    
    Args:
        artist: Artist name
        track: Track name
        
    Returns:
        Spotify URL if found, None otherwise
    """
    result = spotify_service.search_track(artist, track)
    return result['spotify_url'] if result else None