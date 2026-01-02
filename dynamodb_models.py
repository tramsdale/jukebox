"""
DynamoDB models for the jukebox application
"""
import boto3
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import os

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_DEFAULT_REGION', 'eu-west-2'))
table_name = os.environ.get('DYNAMODB_TABLE', 'jukebox-records-dev')

class JukeboxStatus(Enum):
    NEW = "New"
    IN_JUKEBOX = "In Jukebox"
    IN_STORAGE = "In Storage"

class JukeboxRecord:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.track_a_side = kwargs.get('track_a_side', '')
        self.track_b_side = kwargs.get('track_b_side', '')
        self.artist_a_side = kwargs.get('artist_a_side', '')
        self.artist_b_side = kwargs.get('artist_b_side', '')
        self.genre = kwargs.get('genre')
        self.status = kwargs.get('status', JukeboxStatus.NEW)
        self.jukebox_id = kwargs.get('jukebox_id')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())
        
        # Spotify integration fields
        self.spotify_a_side_url = kwargs.get('spotify_a_side_url')
        self.spotify_b_side_url = kwargs.get('spotify_b_side_url')
        self.spotify_a_side_id = kwargs.get('spotify_a_side_id')
        self.spotify_b_side_id = kwargs.get('spotify_b_side_id')
        
        # Convert status to enum if it's a string
        if isinstance(self.status, str):
            self.status = JukeboxStatus(self.status)
    
    @property 
    def table(self):
        return dynamodb.Table(table_name)
    
    def save(self):
        """Save record to DynamoDB"""
        self.updated_at = datetime.utcnow().isoformat()
        
        item = {
            'id': self.id,
            'track_a_side': self.track_a_side,
            'track_b_side': self.track_b_side,
            'artist_a_side': self.artist_a_side,
            'artist_b_side': self.artist_b_side,
            'status': self.status.value,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        # Only include optional fields if they have values
        if self.genre:
            item['genre'] = self.genre
        if self.jukebox_id:
            item['jukebox_id'] = self.jukebox_id
        if self.spotify_a_side_url:
            item['spotify_a_side_url'] = self.spotify_a_side_url
        if self.spotify_b_side_url:
            item['spotify_b_side_url'] = self.spotify_b_side_url
        if self.spotify_a_side_id:
            item['spotify_a_side_id'] = self.spotify_a_side_id
        if self.spotify_b_side_id:
            item['spotify_b_side_id'] = self.spotify_b_side_id
            
        self.table.put_item(Item=item)
        return self
    
    def delete(self):
        """Delete record from DynamoDB"""
        self.table.delete_item(Key={'id': self.id})
    
    def to_dict(self):
        """Convert record to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'track_a_side': self.track_a_side,
            'track_b_side': self.track_b_side,
            'artist_a_side': self.artist_a_side,
            'artist_b_side': self.artist_b_side,
            'genre': self.genre,
            'status': self.status.value,
            'jukebox_id': self.jukebox_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'spotify_a_side_url': self.spotify_a_side_url,
            'spotify_b_side_url': self.spotify_b_side_url,
            'spotify_a_side_id': self.spotify_a_side_id,
            'spotify_b_side_id': self.spotify_b_side_id
        }
    
    def to_jukebox_label(self, use_a_side=True):
        """Convert to JukeBoxLabel for PDF generation"""
        from jukebox_generator import JukeBoxLabel
        
        if use_a_side:
            return JukeBoxLabel(
                artist=self.artist_a_side,  # Fallback for compatibility
                artist_a=self.artist_a_side,
                artist_b=self.artist_b_side,
                a_side=self.track_a_side,
                b_side=self.track_b_side,
                genre=self.genre or "Unknown"
            )
        else:
            return JukeBoxLabel(
                artist=self.artist_b_side or self.artist_a_side,  # Fallback for compatibility
                artist_a=self.artist_b_side or self.artist_a_side,
                artist_b=self.artist_a_side,
                a_side=self.track_b_side,
                b_side=self.track_a_side,
                genre=self.genre or "Unknown"
            )

    def fetch_spotify_links(self, force_refresh=False):
        """
        Fetch Spotify links for A-side and B-side tracks.
        
        Args:
            force_refresh: If True, fetch new links even if they already exist
            
        Returns:
            Dictionary with success status and any errors
        """
        from spotify_service import spotify_service
        
        if not spotify_service.is_available():
            return {
                'success': False,
                'error': 'Spotify service not available. Check API credentials.'
            }
        
        results = {'success': True, 'errors': []}
        
        # Fetch A-side Spotify link
        if (not self.spotify_a_side_url or force_refresh) and self.track_a_side and self.artist_a_side:
            try:
                spotify_info = spotify_service.search_track(self.artist_a_side, self.track_a_side)
                if spotify_info:
                    self.spotify_a_side_url = spotify_info['spotify_url']
                    self.spotify_a_side_id = spotify_info['spotify_id']
                else:
                    results['errors'].append(f"No Spotify match found for A-side: {self.artist_a_side} - {self.track_a_side}")
            except Exception as e:
                results['errors'].append(f"Error fetching A-side Spotify link: {str(e)}")
        
        # Fetch B-side Spotify link
        if (not self.spotify_b_side_url or force_refresh) and self.track_b_side:
            try:
                # Use B-side artist if available, otherwise use A-side artist
                b_artist = self.artist_b_side or self.artist_a_side
                spotify_info = spotify_service.search_track(b_artist, self.track_b_side)
                if spotify_info:
                    self.spotify_b_side_url = spotify_info['spotify_url']
                    self.spotify_b_side_id = spotify_info['spotify_id']
                else:
                    results['errors'].append(f"No Spotify match found for B-side: {b_artist} - {self.track_b_side}")
            except Exception as e:
                results['errors'].append(f"Error fetching B-side Spotify link: {str(e)}")
        
        # Save if we found any links
        if self.spotify_a_side_url or self.spotify_b_side_url:
            self.save()
        
        return results
    

    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]):
        """Create JukeboxRecord from DynamoDB item"""
        return cls(
            id=item['id'],
            track_a_side=item['track_a_side'],
            track_b_side=item['track_b_side'],
            artist_a_side=item['artist_a_side'],
            artist_b_side=item['artist_b_side'],
            genre=item.get('genre'),
            status=item['status'],
            jukebox_id=item.get('jukebox_id'),
            created_at=item.get('created_at'),
            updated_at=item.get('updated_at'),
            spotify_a_side_url=item.get('spotify_a_side_url'),
            spotify_b_side_url=item.get('spotify_b_side_url'),
            spotify_a_side_id=item.get('spotify_a_side_id'),
            spotify_b_side_id=item.get('spotify_b_side_id')
        )
    
    @classmethod
    def get_by_id(cls, record_id: str):
        """Get record by ID"""
        table = dynamodb.Table(table_name)
        try:
            response = table.get_item(Key={'id': record_id})
            if 'Item' in response:
                return cls.from_dynamodb_item(response['Item'])
            return None
        except Exception as e:
            print(f"Error getting record by ID: {e}")
            return None
    
    @classmethod
    def scan_all(cls, status_filter: Optional[str] = None, search_query: Optional[str] = None) -> List['JukeboxRecord']:
        """Get all records with optional filtering"""
        table = dynamodb.Table(table_name)
        
        try:
            if status_filter:
                # Use GSI for status filtering
                response = table.query(
                    IndexName='StatusIndex',
                    KeyConditionExpression='#status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': status_filter}
                )
            else:
                # Full table scan
                response = table.scan()
            
            records = []
            for item in response.get('Items', []):
                record = cls.from_dynamodb_item(item)
                
                # Apply search filter if specified
                if search_query:
                    search_term = search_query.lower()
                    if (search_term in record.track_a_side.lower() or
                        search_term in record.track_b_side.lower() or
                        search_term in record.artist_a_side.lower() or
                        search_term in record.artist_b_side.lower() or
                        (record.jukebox_id and search_term in record.jukebox_id.lower())):
                        records.append(record)
                else:
                    records.append(record)
            
            return records
            
        except Exception as e:
            print(f"Error scanning records: {e}")
            return []
    
    @classmethod
    def get_by_ids(cls, record_ids: List[str]) -> List['JukeboxRecord']:
        """Get multiple records by IDs"""
        table = dynamodb.Table(table_name)
        records = []
        
        # DynamoDB batch_get_item has a limit of 100 items
        for i in range(0, len(record_ids), 100):
            batch_ids = record_ids[i:i+100]
            
            try:
                response = dynamodb.batch_get_item(
                    RequestItems={
                        table_name: {
                            'Keys': [{'id': record_id} for record_id in batch_ids]
                        }
                    }
                )
                
                for item in response['Responses'][table_name]:
                    records.append(cls.from_dynamodb_item(item))
                    
            except Exception as e:
                print(f"Error batch getting records: {e}")
                
        return records

# Initialize table connection (for testing)
def get_table():
    return dynamodb.Table(table_name)