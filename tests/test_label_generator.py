"""
Unit tests for LabelGenerator class
"""

import pytest
from pathlib import Path
import tempfile
from jukebox_generator import LabelGenerator, JukeBoxLabel, GenreConfig


class TestLabelGenerator:
    """Test cases for LabelGenerator class."""

    def test_label_generator_initialization(self, temp_output_dir):
        """Test LabelGenerator initialization with custom parameters."""
        generator = LabelGenerator(
            output_dir=temp_output_dir,
            label_width_mm=80.0,
            label_height_mm=30.0,
            genre_box_width_pct=20.0
        )
        
        assert generator.output_dir == Path(temp_output_dir)
        assert generator.label_width_mm == 80.0
        assert generator.label_height_mm == 30.0
        assert generator.genre_box_width_pct == 20.0

    def test_label_generator_default_initialization(self):
        """Test LabelGenerator initialization with default parameters."""
        generator = LabelGenerator()
        
        assert generator.output_dir == Path("output")
        assert generator.label_width_mm == 74.0
        assert generator.label_height_mm == 28.0

    def test_default_settings_match_requirements(self):
        """Test that default settings match the user's requirements."""
        generator = LabelGenerator()
        
        # Check the specific values user requested
        assert generator.genre_box_width_pct == 0.15  # 15%
        assert generator.genre_box_height_pct == 0.12  # 12%
        assert generator.artist_box_height_pct == 0.28  # 28%

    def test_generate_pdf_single_label(self, label_generator, temp_output_dir):
        """Test generating a PDF with a single label."""
        labels = [JukeBoxLabel(
            artist="Test Artist",
            a_side="Test A Side",
            b_side="Test B Side",
            genre="Rock"
        )]
        
        output_file_path = label_generator.generate_pdf(labels, "test_single.pdf")
        output_file = Path(output_file_path)
        
        assert output_file.exists()
        assert output_file.suffix == ".pdf"
        assert "test_single.pdf" in str(output_file)

    def test_generate_pdf_multiple_labels(self, label_generator, sample_labels):
        """Test generating a PDF with multiple labels."""
        output_file_path = label_generator.generate_pdf(sample_labels, "test_multiple.pdf")
        output_file = Path(output_file_path)
        
        assert output_file.exists()
        assert output_file.suffix == ".pdf"

    def test_generate_pdf_with_different_artists(self, label_generator):
        """Test PDF generation with labels having different artists."""
        labels = [JukeBoxLabel(
            artist="John Lennon",
            a_side="Imagine", 
            b_side="Give Peace a Chance",
            genre="Rock",
            artist_a="John Lennon",
            artist_b="Plastic Ono Band"
        )]
        
        output_file_path = label_generator.generate_pdf(labels, "test_different_artists.pdf")
        output_file = Path(output_file_path)
        
        assert output_file.exists()

    def test_generate_pdf_empty_labels_list(self, label_generator):
        """Test generating a PDF with empty labels list."""
        # Empty labels list should generate an empty PDF
        output_file_path = label_generator.generate_pdf([], "test_empty.pdf")
        output_file = Path(output_file_path)
        
        assert output_file.exists()

    def test_generate_pdf_invalid_filename(self, label_generator, sample_labels):
        """Test generating a PDF with invalid filename characters."""
        # This should sanitize the filename
        output_file_path = label_generator.generate_pdf(sample_labels, "test<>file?.pdf")
        output_file = Path(output_file_path)
        
        assert output_file.exists()
        # Should have sanitized the filename or created the file anyway
        assert output_file.suffix == ".pdf"

    def test_generate_pdf_creates_output_directory(self, temp_output_dir):
        """Test that PDF generation creates output directory if it doesn't exist."""
        non_existent_dir = Path(temp_output_dir) / "new_output"
        generator = LabelGenerator(output_dir=str(non_existent_dir))
        
        labels = [JukeBoxLabel(
            artist="Test Artist",
            a_side="Test A Side", 
            b_side="Test B Side",
            genre="Rock"
        )]
        
        output_file_path = generator.generate_pdf(labels, "test_create_dir.pdf")
        output_file = Path(output_file_path)
        
        assert non_existent_dir.exists()
        assert output_file.exists()

    def test_mm_to_points_conversion(self, label_generator):
        """Test millimeter to points conversion logic."""
        # Test that the conversion factor is reasonable
        # 1 mm = 2.834645669 points approximately
        mm_to_points = 72.0 / 25.4
        points_10mm = 10 * mm_to_points
        assert abs(points_10mm - 28.35) < 0.1

    def test_custom_label_dimensions(self, temp_output_dir):
        """Test LabelGenerator with custom label dimensions."""
        generator = LabelGenerator(
            output_dir=temp_output_dir,
            label_width_mm=100.0,
            label_height_mm=40.0
        )
        
        labels = [JukeBoxLabel(
            artist="Test Artist",
            a_side="Test A Side",
            b_side="Test B Side", 
            genre="Rock"
        )]
        
        output_file_path = generator.generate_pdf(labels, "test_custom_dimensions.pdf")
        output_file = Path(output_file_path)
        assert output_file.exists()

    def test_genre_config_integration(self, label_generator, temp_config_dir):
        """Test LabelGenerator integration with genre configuration."""
        temp_dir, config_file = temp_config_dir
        
        # Create generator with custom config
        generator = LabelGenerator(output_dir=temp_dir)
        generator.genre_config = GenreConfig(config_file)
        
        labels = [JukeBoxLabel(
            artist="Test Artist",
            a_side="Test A Side",
            b_side="Test B Side",
            genre="Rock"
        )]
        
        output_file_path = generator.generate_pdf(labels, "test_genre_config.pdf")
        output_file = Path(output_file_path)
        assert output_file.exists()


class TestGenreConfig:
    """Test cases for GenreConfig class."""

    def test_genre_config_initialization(self, temp_config_dir):
        """Test GenreConfig initialization with custom config file."""
        temp_dir, config_file = temp_config_dir
        config = GenreConfig(config_file)
        
        assert config.config is not None
        assert "Rock" in config.config
        assert "Jazz" in config.config

    def test_get_genre_config_existing_genre(self, temp_config_dir):
        """Test getting configuration for existing genre."""
        temp_dir, config_file = temp_config_dir
        config = GenreConfig(config_file)
        
        rock_config = config.get_genre_config("Rock")
        assert rock_config["color"] == "#FF0000"
        assert rock_config["text_color"] == "#FFFFFF"

    def test_get_genre_config_missing_genre(self, temp_config_dir):
        """Test getting configuration for missing genre returns default."""
        temp_dir, config_file = temp_config_dir
        config = GenreConfig(config_file)
        
        unknown_config = config.get_genre_config("Unknown Genre")
        # Should return default configuration
        assert "background_color" in unknown_config or "color" in unknown_config
        assert "text_color" in unknown_config

    def test_genre_config_case_insensitive(self, temp_config_dir):
        """Test that genre configuration lookup is case insensitive."""
        temp_dir, config_file = temp_config_dir
        config = GenreConfig(config_file)
        
        rock_lower = config.get_genre_config("rock")
        rock_upper = config.get_genre_config("ROCK")
        rock_mixed = config.get_genre_config("Rock")
        
        assert rock_lower == rock_upper == rock_mixed

    def test_default_config_fallback(self):
        """Test GenreConfig falls back to default config when file doesn't exist."""
        config = GenreConfig("nonexistent_config.yaml")
        
        assert config.config is not None
        # Should have some default genres
        assert len(config.config) > 0