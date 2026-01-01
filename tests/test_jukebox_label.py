"""
Unit tests for JukeBoxLabel class
"""

import pytest
from jukebox_generator import JukeBoxLabel


class TestJukeBoxLabel:
    """Test cases for JukeBoxLabel class."""

    def test_basic_label_creation(self):
        """Test creating a basic JukeBoxLabel."""
        label = JukeBoxLabel(
            artist="The Beatles",
            a_side="Hey Jude",
            b_side="Revolution", 
            genre="Rock"
        )
        
        assert label.artist == "The Beatles"
        assert label.a_side == "Hey Jude"
        assert label.b_side == "Revolution"
        assert label.genre == "Rock"
        assert label.background_color is None
        assert label.artist_a is None
        assert label.artist_b is None

    def test_label_with_separate_artists(self):
        """Test creating a JukeBoxLabel with separate artist fields."""
        label = JukeBoxLabel(
            artist="John Lennon",
            a_side="Imagine",
            b_side="Give Peace a Chance",
            genre="Rock",
            artist_a="John Lennon",
            artist_b="Plastic Ono Band"
        )
        
        assert label.artist == "John Lennon"
        assert label.artist_a == "John Lennon"
        assert label.artist_b == "Plastic Ono Band"

    def test_label_with_background_color(self):
        """Test creating a JukeBoxLabel with background color."""
        label = JukeBoxLabel(
            artist="Miles Davis",
            a_side="So What", 
            b_side="Kind of Blue",
            genre="Jazz",
            background_color="#0000FF"
        )
        
        assert label.background_color == "#0000FF"

    def test_get_display_artist_same_artists(self):
        """Test get_display_artist when both artists are the same."""
        label = JukeBoxLabel(
            artist="The Beatles",
            a_side="Hey Jude",
            b_side="Revolution",
            genre="Rock", 
            artist_a="The Beatles",
            artist_b="The Beatles"
        )
        
        assert label.get_display_artist() == "The Beatles"

    def test_get_display_artist_different_artists(self):
        """Test get_display_artist when artists are different."""
        label = JukeBoxLabel(
            artist="John Lennon",
            a_side="Imagine",
            b_side="Give Peace a Chance",
            genre="Rock",
            artist_a="John Lennon", 
            artist_b="Plastic Ono Band"
        )
        
        assert label.get_display_artist() == "John Lennon // Plastic Ono Band"

    def test_get_display_artist_only_artist_a(self):
        """Test get_display_artist with only artist_a specified."""
        label = JukeBoxLabel(
            artist="The Beatles",
            a_side="Hey Jude",
            b_side="Revolution",
            genre="Rock",
            artist_a="The Beatles",
            artist_b=None
        )
        
        assert label.get_display_artist() == "The Beatles"

    def test_get_display_artist_only_artist_b(self):
        """Test get_display_artist with only artist_b specified."""
        label = JukeBoxLabel(
            artist="The Beatles",
            a_side="Hey Jude", 
            b_side="Revolution",
            genre="Rock",
            artist_a=None,
            artist_b="The Beatles"
        )
        
        assert label.get_display_artist() == "The Beatles"

    def test_get_display_artist_fallback_to_main_artist(self):
        """Test get_display_artist falls back to main artist field."""
        label = JukeBoxLabel(
            artist="Miles Davis",
            a_side="So What",
            b_side="Kind of Blue", 
            genre="Jazz",
            artist_a=None,
            artist_b=None
        )
        
        assert label.get_display_artist() == "Miles Davis"

    def test_get_display_artist_legacy_compatibility(self):
        """Test get_display_artist with legacy labels (no artist_a/artist_b)."""
        label = JukeBoxLabel(
            artist="Led Zeppelin",
            a_side="Stairway to Heaven",
            b_side="Black Dog",
            genre="Rock"
        )
        
        assert label.get_display_artist() == "Led Zeppelin"

    def test_get_display_artist_empty_strings(self):
        """Test get_display_artist handles empty strings correctly."""
        label = JukeBoxLabel(
            artist="The Beatles",
            a_side="Hey Jude",
            b_side="Revolution",
            genre="Rock",
            artist_a="",
            artist_b=""
        )
        
        assert label.get_display_artist() == "The Beatles"

    def test_get_display_artist_whitespace_handling(self):
        """Test get_display_artist handles whitespace in artist names."""
        label = JukeBoxLabel(
            artist="Test Artist",
            a_side="Track A",
            b_side="Track B", 
            genre="Rock",
            artist_a="  John Lennon  ",
            artist_b="  Plastic Ono Band  "
        )
        
        # The method should handle whitespace properly
        result = label.get_display_artist()
        assert "//" in result
        assert "John Lennon" in result
        assert "Plastic Ono Band" in result