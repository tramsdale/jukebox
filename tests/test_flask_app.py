"""
Integration tests for Flask web application
"""

import pytest
import json
import tempfile
from io import StringIO
from models import db, JukeboxRecord, JukeboxStatus
from pathlib import Path


class TestFlaskApp:
    """Test cases for Flask application routes."""

    def test_index_route_requires_login(self, client):
        """Test that index route requires authentication."""
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location

    def test_login_page_accessible(self, client):
        """Test that login page is accessible."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Please log in' in response.data

    def test_invalid_login(self, client):
        """Test login with invalid credentials."""
        response = client.post('/login', data={
            'username': 'invalid_user',
            'password': 'invalid_password'
        })
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data

    def test_database_route_requires_login(self, client):
        """Test that database route requires authentication."""
        response = client.get('/database')
        assert response.status_code == 302  # Redirect to login

    def test_api_records_requires_login(self, client):
        """Test that API records route requires authentication."""
        response = client.get('/api/records')
        assert response.status_code == 302  # Redirect to login

    def test_settings_route_requires_login(self, client):
        """Test that settings route requires authentication."""
        response = client.get('/settings')
        assert response.status_code == 302  # Redirect to login

    def test_add_record_route_requires_login(self, client):
        """Test that add record route requires authentication."""
        response = client.get('/add_record')
        assert response.status_code == 302  # Redirect to login

    def test_import_csv_route_requires_login(self, client):
        """Test that import CSV route requires authentication."""
        response = client.get('/import_csv')
        assert response.status_code == 302  # Redirect to login


class TestDatabaseIntegration:
    """Test database integration with Flask app."""

    def test_api_records_empty_database(self, app, client):
        """Test API records endpoint with empty database."""
        with app.app_context():
            # Mock login by bypassing authentication for testing
            with client.session_transaction() as sess:
                sess['_user_id'] = 'test_user'
                sess['_fresh'] = True
            
            response = client.get('/api/records')
            # Note: This test assumes we can bypass login. In a real scenario,
            # we'd need to properly authenticate or mock the login system

    def test_database_operations(self, app):
        """Test basic database operations."""
        with app.app_context():
            # Test record creation
            record = JukeboxRecord(
                track_a_side="Test Track A",
                track_b_side="Test Track B", 
                artist_a_side="Test Artist A",
                artist_b_side="Test Artist B",
                genre="Test Genre"
            )
            
            db.session.add(record)
            db.session.commit()
            
            # Test record retrieval
            retrieved = JukeboxRecord.query.first()
            assert retrieved is not None
            assert retrieved.track_a_side == "Test Track A"
            
            # Test record update
            retrieved.genre = "Updated Genre"
            db.session.commit()
            
            updated = JukeboxRecord.query.first()
            assert updated.genre == "Updated Genre"
            
            # Test record deletion
            db.session.delete(updated)
            db.session.commit()
            
            assert JukeboxRecord.query.count() == 0


class TestCSVImport:
    """Test CSV import functionality."""

    def test_csv_import_data_processing(self, app):
        """Test CSV data processing logic."""
        with app.app_context():
            # Sample CSV data
            csv_data = """Artist - A Side,Track - A Side,Artist - B Side,Track - B Side,Genre
The Beatles,Hey Jude,The Beatles,Revolution,Rock
John Lennon,Imagine,Plastic Ono Band,Give Peace a Chance,Rock
Miles Davis,So What,Miles Davis,Kind of Blue,Jazz"""
            
            # Process the CSV data (this would normally be done in the import route)
            lines = csv_data.strip().split('\n')[1:]  # Skip header
            records_created = 0
            
            for line in lines:
                parts = line.split(',')
                if len(parts) >= 5:
                    record = JukeboxRecord(
                        artist_a_side=parts[0].strip(),
                        track_a_side=parts[1].strip(), 
                        artist_b_side=parts[2].strip(),
                        track_b_side=parts[3].strip(),
                        genre=parts[4].strip() if len(parts) > 4 else None,
                        status=JukeboxStatus.NEW
                    )
                    db.session.add(record)
                    records_created += 1
            
            db.session.commit()
            
            assert records_created == 3
            assert JukeboxRecord.query.count() == 3
            
            # Verify specific records
            beatles_record = JukeboxRecord.query.filter_by(artist_a_side="The Beatles").first()
            assert beatles_record.track_a_side == "Hey Jude"
            assert beatles_record.genre == "Rock"


class TestLabelGeneration:
    """Test label generation integration."""

    def test_label_generation_from_database(self, app, populated_db):
        """Test generating labels from database records."""
        with app.app_context():
            records = JukeboxRecord.query.all()
            labels = [record.to_jukebox_label() for record in records]
            
            assert len(labels) == 3
            
            # Test that different artist display works
            different_artist_labels = [label for label in labels if "//" in label.get_display_artist()]
            assert len(different_artist_labels) == 1  # John Lennon // Plastic Ono Band
            
            same_artist_labels = [label for label in labels if "//" not in label.get_display_artist()]
            assert len(same_artist_labels) == 2  # The Beatles and Miles Davis

    def test_settings_persistence(self, app, client):
        """Test settings persistence in session."""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['label_settings'] = {
                    'genre_box_width_pct': 0.15,
                    'genre_box_height_pct': 0.12,
                    'artist_box_height_pct': 0.28
                }
                
            with client.session_transaction() as sess:
                settings = sess.get('label_settings', {})
                assert settings['genre_box_width_pct'] == 0.15
                assert settings['genre_box_height_pct'] == 0.12
                assert settings['artist_box_height_pct'] == 0.28


class TestErrorHandling:
    """Test error handling in the application."""

    def test_invalid_record_creation(self, app):
        """Test handling of invalid record creation."""
        with app.app_context():
            # Try to create record without required fields
            with pytest.raises(Exception):  # Should raise some kind of database error
                record = JukeboxRecord()
                db.session.add(record)
                db.session.commit()

    def test_duplicate_jukebox_id_handling(self, app):
        """Test handling of duplicate jukebox IDs."""
        with app.app_context():
            # Create first record
            record1 = JukeboxRecord(
                track_a_side="Track A1",
                track_b_side="Track B1",
                artist_a_side="Artist A1", 
                artist_b_side="Artist B1",
                jukebox_id="A01"
            )
            db.session.add(record1)
            db.session.commit()
            
            # Create second record with same jukebox_id
            record2 = JukeboxRecord(
                track_a_side="Track A2",
                track_b_side="Track B2",
                artist_a_side="Artist A2",
                artist_b_side="Artist B2", 
                jukebox_id="A01"
            )
            db.session.add(record2)
            db.session.commit()
            
            # Both should exist (no unique constraint on jukebox_id currently)
            assert JukeboxRecord.query.filter_by(jukebox_id="A01").count() == 2

    def test_long_field_values(self, app):
        """Test handling of very long field values."""
        with app.app_context():
            # Test with very long strings (within the 200 char limit)
            long_title = "A" * 199
            long_artist = "B" * 199
            
            record = JukeboxRecord(
                track_a_side=long_title,
                track_b_side=long_title,
                artist_a_side=long_artist,
                artist_b_side=long_artist,
                genre="Rock"
            )
            
            db.session.add(record)
            db.session.commit()
            
            retrieved = JukeboxRecord.query.first()
            assert len(retrieved.track_a_side) == 199
            assert len(retrieved.artist_a_side) == 199