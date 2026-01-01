"""
Pytest configuration and fixtures for jukebox label generator tests
"""

import pytest
import tempfile
import os
from pathlib import Path
from flask import Flask
from models import db, JukeboxRecord, JukeboxStatus
from jukebox_generator import JukeBoxLabel, LabelGenerator
import yaml

@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.init_app(app)
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test runner for the Flask application."""
    return app.test_cli_runner()

@pytest.fixture
def sample_record():
    """Create a sample JukeboxRecord for testing."""
    return JukeboxRecord(
        track_a_side="Hey Jude",
        track_b_side="Revolution",
        artist_a_side="The Beatles",
        artist_b_side="The Beatles", 
        genre="Rock",
        status=JukeboxStatus.IN_JUKEBOX,
        jukebox_id="A01"
    )

@pytest.fixture
def sample_record_different_artists():
    """Create a sample JukeboxRecord with different artists for testing."""
    return JukeboxRecord(
        track_a_side="Imagine",
        track_b_side="Give Peace a Chance",
        artist_a_side="John Lennon",
        artist_b_side="Plastic Ono Band",
        genre="Rock",
        status=JukeboxStatus.NEW
    )

@pytest.fixture
def sample_labels():
    """Create sample JukeBoxLabels for testing."""
    return [
        JukeBoxLabel(
            artist="The Beatles",
            a_side="Hey Jude", 
            b_side="Revolution",
            genre="Rock",
            artist_a="The Beatles",
            artist_b="The Beatles"
        ),
        JukeBoxLabel(
            artist="John Lennon",
            a_side="Imagine",
            b_side="Give Peace a Chance", 
            genre="Rock",
            artist_a="John Lennon",
            artist_b="Plastic Ono Band"
        ),
        JukeBoxLabel(
            artist="Miles Davis",
            a_side="So What",
            b_side="Kind of Blue",
            genre="Jazz"
        )
    ]

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test output files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory with test genre config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "genre_config.yaml"
        test_config = {
            'genres': {
                'rock': {
                    'color': '#FF0000',
                    'text_color': '#FFFFFF'
                },
                'jazz': {
                    'color': '#0000FF', 
                    'text_color': '#FFFFFF'
                },
                'classical': {
                    'color': '#800080',
                    'text_color': '#FFFFFF'
                },
                'default': {
                    'background_color': '#DDDDDD',
                    'text_color': '#333333'
                }
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)
        yield temp_dir, str(config_file)

@pytest.fixture
def label_generator(temp_output_dir):
    """Create a LabelGenerator instance for testing."""
    return LabelGenerator(output_dir=temp_output_dir)

@pytest.fixture
def populated_db(app):
    """Create a database with sample data for testing."""
    with app.app_context():
        # Add sample records
        records = [
            JukeboxRecord(
                track_a_side="Hey Jude",
                track_b_side="Revolution", 
                artist_a_side="The Beatles",
                artist_b_side="The Beatles",
                genre="Rock",
                status=JukeboxStatus.IN_JUKEBOX,
                jukebox_id="A01"
            ),
            JukeboxRecord(
                track_a_side="Imagine", 
                track_b_side="Give Peace a Chance",
                artist_a_side="John Lennon",
                artist_b_side="Plastic Ono Band",
                genre="Rock",
                status=JukeboxStatus.NEW
            ),
            JukeboxRecord(
                track_a_side="So What",
                track_b_side="Kind of Blue",
                artist_a_side="Miles Davis", 
                artist_b_side="Miles Davis",
                genre="Jazz",
                status=JukeboxStatus.IN_STORAGE
            )
        ]
        
        for record in records:
            db.session.add(record)
        db.session.commit()
        
        return records