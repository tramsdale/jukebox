# Juke Box Label Generator

A Python web application for generating PDF files containing juke box labels with configurable backgrounds based on music genre.

## Features

- **Web Interface**: Simple, user-friendly web interface
- Generate PDF files with multiple juke box labels per page
- Each label displays:
  - Artist name
  - A-side track name  
  - B-side track name
  - Genre
- Configurable background colors based on genre
- Customizable label dimensions in millimeters
- Support for JSON and CSV input formats
- Manual single or multiple label entry
- Sample data generation

## Installation

1. Install [uv](https://docs.astral.sh/uv/) if you haven't already
2. Install dependencies:
   ```bash
   uv sync
   ```

## Usage

### Web Application (Recommended)

1. Start the web server:
   ```bash
   uv run python app.py
   ```

2. Open your browser and go to `http://localhost:5000`

3. Use the web interface to:
   - **Generate sample labels** to test dimensions
   - **Upload JSON/CSV files** with your label data
   - **Manually enter** single or multiple labels

### Web Interface Features

- **Label Dimensions**: Adjust width and height in millimeters (default: 60mm × 25mm)
- **File Upload**: Support for JSON and CSV files
- **Manual Entry**: Create single labels or multiple labels via JSON input
- **Sample Generation**: Test the format with built-in sample data
- **Real-time Preview**: Download PDFs instantly

### Command Line Interface (Legacy)

Generate labels from sample data:
```bash
uv run python cli.py --sample
```

Generate labels from a JSON file:
```bash
uv run python cli.py --input data/sample_labels.json --output my_labels.pdf
```

Generate labels with custom dimensions:
```bash
uv run python cli.py --sample --width 50 --height 30
```

### Python API

```python
from jukebox_generator import LabelGenerator, JukeBoxLabel

# Create labels
labels = [
    JukeBoxLabel("The Beatles", "Hey Jude", "Revolution", "Rock"),
    JukeBoxLabel("Miles Davis", "So What", "Kind of Blue", "Jazz"),
]

# Generate PDF with custom dimensions (width=50mm, height=30mm)
generator = LabelGenerator(label_width_mm=50, label_height_mm=30)
output_file = generator.generate_pdf(labels, "my_labels.pdf")
```

## Configuration

### Label Dimensions

Default label size is 63.5mm x 38.1mm. You can specify custom dimensions:

- `--width` or `-w`: Label width in millimeters
- `--height`: Label height in millimeters

### Genre Colors

Edit [config/genre_config.yaml](config/genre_config.yaml) to customize background and text colors for different genres:

```yaml
genres:
  rock:
    background_color: '#FF6B6B'
    text_color: '#FFFFFF'
  jazz:
    background_color: '#45B7D1'
    text_color: '#FFFFFF'
  # ... more genres
```

### Input Data Format

#### JSON Format ([data/sample_labels.json](data/sample_labels.json)):
```json
[
  {
    "artist": "The Beatles",
    "a_side": "Hey Jude",
    "b_side": "Revolution",
    "genre": "Rock"
  }
]
```

#### CSV Format ([data/sample_labels.csv](data/sample_labels.csv)):
```csv
artist,a_side,b_side,genre
The Beatles,Hey Jude,Revolution,Rock
Miles Davis,So What,Kind of Blue,Jazz
```

## Project Structure

```
.
├── jukebox_generator.py    # Main label generation classes
├── cli.py                 # Command-line interface
├── pyproject.toml         # Project configuration and dependencies
├── config/
│   └── genre_config.yaml  # Genre color configuration
├── data/
│   ├── sample_labels.json # Sample data in JSON format
│   └── sample_labels.csv  # Sample data in CSV format
├── output/               # Generated PDF files (created automatically)
└── README.md            # This file
```

## Classes

- `JukeBoxLabel`: Data class representing a single label
- `GenreConfig`: Handles genre-based configuration (colors, etc.)
- `LabelGenerator`: Main class for generating PDF files
- `DataLoader`: Utility class for loading data from files

## CLI Arguments

- `--input`, `-i`: Input file (JSON or CSV)
- `--output`, `-o`: Output PDF filename (default: jukebox_labels.pdf)
- `--format`, `-f`: Input file format (auto-detected if not specified)
- `--sample`: Generate PDF with sample data
- `--width`, `-w`: Label width in millimeters (default: 63.5mm)
- `--height`: Label height in millimeters (default: 38.1mm)

## Dependencies

- `reportlab`: PDF generation
- `PyYAML`: YAML configuration files
- `Pillow`: Image processing support

## Development

Install development dependencies:
```bash
uv sync --dev
```

Run tests:
```bash
uv run pytest
```

Format code:
```bash
uv run black .
```

## License

This project is open source and available under the MIT License.