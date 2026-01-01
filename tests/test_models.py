"""
Unit tests for database models
"""

import pytest
from models import JukeboxRecord, JukeboxStatus, db
from jukebox_generator import JukeBoxLabel


class TestJukeboxRecord:
    """Test cases for JukeboxRecord model."""

    def test_jukebox_record_creation(self, app):
        """Test creating a JukeboxRecord."""
        with app.app_context():
            record = JukeboxRecord(
                track_a_side="Hey Jude",
                track_b_side="Revolution",
                artist_a_side="The Beatles",
                artist_b_side="The Beatles",
                genre="Rock",
                status=JukeboxStatus.IN_JUKEBOX,
                jukebox_id="A01"
            )
            
            assert record.track_a_side == "Hey Jude"
            assert record.track_b_side == "Revolution"
            assert record.artist_a_side == "The Beatles"
            assert record.artist_b_side == "The Beatles"
            assert record.genre == "Rock"
            assert record.status == JukeboxStatus.IN_JUKEBOX
            assert record.jukebox_id == "A01"

    def test_jukebox_record_default_status(self, app):
        """Test JukeboxRecord default status is NEW."""
        with app.app_context():
            record = JukeboxRecord(
                track_a_side="Test Track A",
                track_b_side="Test Track B",
                artist_a_side="Test Artist A",
                artist_b_side="Test Artist B"
            )
            
            assert record.status == JukeboxStatus.NEW

    def test_jukebox_record_optional_fields(self, app):
        """Test JukeboxRecord with optional fields as None."""
        with app.app_context():
            record = JukeboxRecord(
                track_a_side="Test Track A",
                track_b_side="Test Track B",
                artist_a_side="Test Artist A",
                artist_b_side="Test Artist B",
                genre=None,
                jukebox_id=None
            )
            
            assert record.genre is None
            assert record.jukebox_id is None

    def test_jukebox_record_repr(self, app):
        """Test JukeboxRecord string representation."""
        with app.app_context():
            record = JukeboxRecord(
                track_a_side="Hey Jude",
                track_b_side="Revolution",
                artist_a_side="The Beatles",
                artist_b_side="The Beatles"
            )
            
            assert "The Beatles" in repr(record)
            assert "Hey Jude" in repr(record)

    def test_to_dict(self, app, sample_record):
        """Test converting JukeboxRecord to dictionary."""
        with app.app_context():
            db.session.add(sample_record)
            db.session.commit()
            
            record_dict = sample_record.to_dict()
            
            assert record_dict["track_a_side"] == "Hey Jude"
            assert record_dict["track_b_side"] == "Revolution" 
            assert record_dict["artist_a_side"] == "The Beatles"
            assert record_dict["artist_b_side"] == "The Beatles"
            assert record_dict["genre"] == "Rock"
            assert record_dict["status"] == "In Jukebox"
            assert record_dict["jukebox_id"] == "A01"
            assert "id" in record_dict

    def test_to_jukebox_label_a_side(self, app, sample_record):
        """Test converting to JukeBoxLabel using A side."""
        with app.app_context():
            label = sample_record.to_jukebox_label(use_a_side=True)
            
            assert isinstance(label, JukeBoxLabel)
            assert label.artist == "The Beatles"
            assert label.a_side == "Hey Jude"
            assert label.b_side == "Revolution"
            assert label.genre == "Rock"
            assert label.artist_a == "The Beatles"
            assert label.artist_b == "The Beatles"

    def test_to_jukebox_label_b_side(self, app, sample_record):
        """Test converting to JukeBoxLabel using B side."""
        with app.app_context():
            label = sample_record.to_jukebox_label(use_a_side=False)
            
            assert isinstance(label, JukeBoxLabel)
            assert label.artist == "The Beatles"  # B side artist
            assert label.a_side == "Revolution"  # B side track becomes A
            assert label.b_side == "Hey Jude"    # A side track becomes B
            assert label.genre == "Rock"
            assert label.artist_a == "The Beatles"  # B side artist becomes A
            assert label.artist_b == "The Beatles"  # A side artist becomes B

    def test_to_jukebox_label_different_artists(self, app, sample_record_different_artists):
        """Test converting to JukeBoxLabel with different artists."""
        with app.app_context():
            label = sample_record_different_artists.to_jukebox_label(use_a_side=True)
            
            assert label.artist == "John Lennon"
            assert label.artist_a == "John Lennon"
            assert label.artist_b == "Plastic Ono Band"
            assert label.get_display_artist() == "John Lennon // Plastic Ono Band"

    def test_to_jukebox_label_none_genre(self, app):
        """Test converting to JukeBoxLabel with None genre."""
        with app.app_context():
            record = JukeboxRecord(
                track_a_side="Test Track",
                track_b_side="Test B Side",
                artist_a_side="Test Artist",
                artist_b_side="Test Artist",
                genre=None
            )
            
            label = record.to_jukebox_label()
            assert label.genre == "Various"

    def test_database_persistence(self, app, sample_record):
        """Test saving and retrieving JukeboxRecord from database."""
        with app.app_context():
            # Save record
            db.session.add(sample_record)
            db.session.commit()
            
            record_id = sample_record.id
            
            # Retrieve record
            retrieved_record = db.session.get(JukeboxRecord, record_id)
            
            assert retrieved_record is not None
            assert retrieved_record.track_a_side == "Hey Jude"
            assert retrieved_record.artist_a_side == "The Beatles"

    def test_database_query_by_artist(self, app, populated_db):
        """Test querying records by artist."""
        with app.app_context():
            beatles_records = JukeboxRecord.query.filter_by(artist_a_side="The Beatles").all()
            
            assert len(beatles_records) == 1
            assert beatles_records[0].track_a_side == "Hey Jude"

    def test_database_query_by_genre(self, app, populated_db):
        """Test querying records by genre."""
        with app.app_context():
            rock_records = JukeboxRecord.query.filter_by(genre="Rock").all()
            jazz_records = JukeboxRecord.query.filter_by(genre="Jazz").all()
            
            assert len(rock_records) == 2
            assert len(jazz_records) == 1

    def test_database_query_by_status(self, app, populated_db):
        """Test querying records by status."""
        with app.app_context():
            in_jukebox = JukeboxRecord.query.filter_by(status=JukeboxStatus.IN_JUKEBOX).all()
            new_records = JukeboxRecord.query.filter_by(status=JukeboxStatus.NEW).all()
            
            assert len(in_jukebox) == 1
            assert len(new_records) == 1


class TestJukeboxStatus:
    """Test cases for JukeboxStatus enum."""

    def test_jukebox_status_values(self):
        """Test JukeboxStatus enum values."""
        assert JukeboxStatus.IN_JUKEBOX.value == "In Jukebox"
        assert JukeboxStatus.NEW.value == "New"
        assert JukeboxStatus.IN_STORAGE.value == "In Storage"
        assert JukeboxStatus.WISHLIST.value == "Wishlist"

    def test_jukebox_status_enum_members(self):
        """Test that all expected JukeboxStatus members exist."""
        expected_members = {"IN_JUKEBOX", "NEW", "IN_STORAGE", "WISHLIST"}
        actual_members = {status.name for status in JukeboxStatus}
        
        assert expected_members == actual_members