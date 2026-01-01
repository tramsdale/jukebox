"""
Performance and integration tests for jukebox label generator
"""

import pytest
import time
from pathlib import Path
import tempfile
from jukebox_generator import LabelGenerator, JukeBoxLabel


class TestPerformance:
    """Performance tests for label generation."""

    def test_large_batch_label_generation(self, temp_output_dir):
        """Test generating a large batch of labels."""
        generator = LabelGenerator(output_dir=temp_output_dir)
        
        # Generate 100 labels
        labels = []
        for i in range(100):
            labels.append(JukeBoxLabel(
                artist=f"Artist {i}",
                a_side=f"Track A {i}",
                b_side=f"Track B {i}",
                genre="Rock",
                artist_a=f"Artist A {i}",
                artist_b=f"Artist B {i}" if i % 2 == 0 else f"Artist A {i}"
            ))
        
        start_time = time.time()
        output_file_path = generator.generate_pdf(labels, "test_large_batch.pdf")
        output_file = Path(output_file_path)
        end_time = time.time()
        
        assert output_file.exists()
        # Should complete within reasonable time (adjust as needed)
        assert (end_time - start_time) < 30.0  # 30 seconds max
        
        # Check file size is reasonable
        file_size = output_file.stat().st_size
        assert file_size > 1000  # At least 1KB
        assert file_size < 10 * 1024 * 1024  # Less than 10MB

    def test_memory_usage_large_dataset(self, temp_output_dir):
        """Test memory usage with large dataset."""
        generator = LabelGenerator(output_dir=temp_output_dir)
        
        # Generate many labels with long text
        labels = []
        long_text = "A" * 150  # Close to field limit
        
        for i in range(50):
            labels.append(JukeBoxLabel(
                artist=f"{long_text} {i}",
                a_side=f"{long_text} A {i}",
                b_side=f"{long_text} B {i}",
                genre="Rock",
                artist_a=f"{long_text} A {i}",
                artist_b=f"{long_text} B {i}"
            ))
        
        # This should complete without memory errors
        output_file = generator.generate_pdf(labels, "test_memory_usage.pdf")
        assert output_file.exists()


class TestGenreHandling:
    """Test comprehensive genre handling."""

    def test_all_supported_genres(self, label_generator):
        """Test label generation with all supported genres."""
        genres = [
            "Rock", "Pop", "Jazz", "Classical", "Blues", "Country", 
            "Folk", "R&B", "Hip Hop", "Electronic", "Reggae", "Punk",
            "Metal", "Alternative", "Indie", "Soul", "Funk", "Gospel"
        ]
        
        labels = []
        for i, genre in enumerate(genres):
            labels.append(JukeBoxLabel(
                artist=f"Artist {i}",
                a_side=f"Track A {i}",
                b_side=f"Track B {i}",
                genre=genre
            ))
        
        output_file = label_generator.generate_pdf(labels, "test_all_genres.pdf")
        assert output_file.exists()

    def test_genre_case_insensitive_handling(self, label_generator):
        """Test that genre handling is case insensitive."""
        labels = [
            JukeBoxLabel(
                artist="Test Artist 1",
                a_side="Track A1",
                b_side="Track B1", 
                genre="rock"
            ),
            JukeBoxLabel(
                artist="Test Artist 2", 
                a_side="Track A2",
                b_side="Track B2",
                genre="ROCK"
            ),
            JukeBoxLabel(
                artist="Test Artist 3",
                a_side="Track A3", 
                b_side="Track B3",
                genre="Rock"
            )
        ]
        
        output_file = label_generator.generate_pdf(labels, "test_case_insensitive.pdf")
        assert output_file.exists()

    def test_unknown_genre_handling(self, label_generator):
        """Test handling of unknown/unsupported genres."""
        labels = [
            JukeBoxLabel(
                artist="Test Artist",
                a_side="Track A", 
                b_side="Track B",
                genre="Unknown Genre Type"
            ),
            JukeBoxLabel(
                artist="Test Artist 2",
                a_side="Track A2",
                b_side="Track B2",
                genre=""  # Empty genre
            ),
            JukeBoxLabel(
                artist="Test Artist 3",
                a_side="Track A3",
                b_side="Track B3",
                genre=None  # None genre
            )
        ]
        
        output_file = label_generator.generate_pdf(labels, "test_unknown_genres.pdf")
        assert output_file.exists()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_characters_in_labels(self, label_generator):
        """Test handling of unicode characters in label text."""
        labels = [
            JukeBoxLabel(
                artist="Björk",
                a_side="Jóga", 
                b_side="Bachelorette",
                genre="Electronic"
            ),
            JukeBoxLabel(
                artist="Café Tacvba",
                a_side="La Ingrata",
                b_side="El Ciclón",
                genre="Rock"
            ),
            JukeBoxLabel(
                artist="松本伊代", # Japanese characters
                a_side="センチメンタル・ジャーニー",
                b_side="青春",
                genre="Pop"
            )
        ]
        
        output_file = label_generator.generate_pdf(labels, "test_unicode.pdf")
        assert output_file.exists()

    def test_special_characters_in_filenames(self, label_generator):
        """Test handling of special characters in output filenames."""
        labels = [JukeBoxLabel(
            artist="Test Artist",
            a_side="Track A",
            b_side="Track B", 
            genre="Rock"
        )]
        
        # Test various special characters
        special_filenames = [
            "test file with spaces.pdf",
            "test-file-with-dashes.pdf",
            "test_file_with_underscores.pdf",
            "test.file.with.dots.pdf"
        ]
        
        for filename in special_filenames:
            output_file = label_generator.generate_pdf(labels, filename)
            assert output_file.exists()

    def test_very_long_text_handling(self, label_generator):
        """Test handling of very long text in label fields."""
        long_artist = "A" * 100
        long_track = "T" * 100
        
        labels = [JukeBoxLabel(
            artist=long_artist,
            a_side=long_track,
            b_side=long_track,
            genre="Rock",
            artist_a=long_artist,
            artist_b=long_artist + " Extended"
        )]
        
        output_file = label_generator.generate_pdf(labels, "test_long_text.pdf")
        assert output_file.exists()

    def test_empty_or_none_values(self, label_generator):
        """Test handling of empty or None values in label fields."""
        labels = [
            JukeBoxLabel(
                artist="",
                a_side="Track A",
                b_side="Track B",
                genre="Rock"
            ),
            JukeBoxLabel(
                artist="Test Artist",
                a_side="", 
                b_side="Track B",
                genre="Rock"
            ),
            JukeBoxLabel(
                artist="Test Artist",
                a_side="Track A",
                b_side="",
                genre="Rock"
            )
        ]
        
        output_file = label_generator.generate_pdf(labels, "test_empty_values.pdf")
        assert output_file.exists()


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_mixed_artist_scenarios(self, label_generator):
        """Test various artist display scenarios in one batch."""
        labels = [
            # Same artists
            JukeBoxLabel(
                artist="The Beatles",
                a_side="Hey Jude", 
                b_side="Revolution",
                genre="Rock",
                artist_a="The Beatles",
                artist_b="The Beatles"
            ),
            # Different artists
            JukeBoxLabel(
                artist="John Lennon",
                a_side="Imagine",
                b_side="Give Peace a Chance",
                genre="Rock", 
                artist_a="John Lennon",
                artist_b="Plastic Ono Band"
            ),
            # Legacy format
            JukeBoxLabel(
                artist="Miles Davis",
                a_side="So What",
                b_side="Kind of Blue",
                genre="Jazz"
            ),
            # Only artist_a
            JukeBoxLabel(
                artist="Bob Dylan",
                a_side="Blowin' in the Wind", 
                b_side="The Times They Are a-Changin'",
                genre="Folk",
                artist_a="Bob Dylan",
                artist_b=None
            )
        ]
        
        output_file = label_generator.generate_pdf(labels, "test_mixed_artists.pdf")
        assert output_file.exists()
        
        # Verify display artist logic
        assert labels[0].get_display_artist() == "The Beatles"
        assert labels[1].get_display_artist() == "John Lennon // Plastic Ono Band"
        assert labels[2].get_display_artist() == "Miles Davis"
        assert labels[3].get_display_artist() == "Bob Dylan"

    def test_real_world_data_simulation(self, label_generator):
        """Test with data that simulates real-world usage."""
        # Simulate importing data from various sources
        labels = [
            # Classic rock with same artist
            JukeBoxLabel(
                artist="Led Zeppelin",
                a_side="Stairway to Heaven",
                b_side="Black Dog",
                genre="Rock", 
                artist_a="Led Zeppelin",
                artist_b="Led Zeppelin"
            ),
            # Collaboration with different artists
            JukeBoxLabel(
                artist="Queen",
                a_side="Under Pressure",
                b_side="Bohemian Rhapsody", 
                genre="Rock",
                artist_a="Queen & David Bowie",
                artist_b="Queen"
            ),
            # Single with B-side by different artist/band lineup
            JukeBoxLabel(
                artist="The Beatles",
                a_side="While My Guitar Gently Weeps",
                b_side="Something",
                genre="Rock",
                artist_a="The Beatles (George Harrison)",
                artist_b="The Beatles (George Harrison)"
            )
        ]
        
        output_file = label_generator.generate_pdf(labels, "test_real_world.pdf")
        assert output_file.exists()
        
        # Test that collaboration displays correctly
        assert "//" in labels[1].get_display_artist()  # Queen & David Bowie // Queen