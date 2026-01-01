"""
Juke Box Label Generator

A Python application for generating PDF files containing juke box labels
with configurable backgrounds based on music genre.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Flowable
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import json
import yaml
from pathlib import Path


class LabelFlowable(Flowable):
    """A custom flowable for drawing precise jukebox labels."""
    
    def __init__(self, label: 'JukeBoxLabel', width, height, genre_config, 
                 genre_box_width_pct=0.1, genre_box_height_pct=0.33, 
                 artist_box_height_pct=0.33, a_side_y_offset=0, artist_y_offset=0, 
                 b_side_y_offset=0, genre_y_offset=0, main_font_size=12, 
                 genre_font_size=6):
        self.label = label
        self.width = width
        self.height = height
        self.genre_config = genre_config
        self.genre_box_width_pct = genre_box_width_pct
        self.genre_box_height_pct = genre_box_height_pct
        self.artist_box_height_pct = artist_box_height_pct
        self.a_side_y_offset = a_side_y_offset
        self.artist_y_offset = artist_y_offset
        self.b_side_y_offset = b_side_y_offset
        self.genre_y_offset = genre_y_offset
        self.main_font_size = main_font_size
        self.genre_font_size = genre_font_size
    
    def _hex_to_color(self, hex_color: str):
        """Convert hex color string to ReportLab Color object."""
        if not hex_color or len(hex_color) < 6:
            return colors.Color(0.87, 0.87, 0.87)  # Light gray fallback
        
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            return colors.Color(0.87, 0.87, 0.87)  # Light gray fallback
        
        try:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return colors.Color(r, g, b)
        except ValueError:
            return colors.Color(0.87, 0.87, 0.87)  # Light gray fallback
    
    def _get_genre_bg_color(self, genre_color):
        """Create a lighter background version of the genre color."""
        # Make the genre color much lighter for background (blend with white)
        blend_factor = 0.15  # Use 15% of the genre color, 85% white
        r = genre_color.red * blend_factor + 0.98 * (1 - blend_factor)
        g = genre_color.green * blend_factor + 0.95 * (1 - blend_factor)
        b = genre_color.blue * blend_factor + 0.97 * (1 - blend_factor)
        return colors.Color(r, g, b)
    
    def _format_genre_text(self, genre: str) -> str:
        """Format genre text for display on labels with special abbreviations."""
        genre_lower = genre.lower()
        
        # Special cases
        if genre_lower == 'unknown':
            return ''  # Leave blank for unknown genres
        elif genre_lower == 'country':
            return 'CNTRY'
        elif genre_lower == 'electronic':
            return 'ELEC'
        elif genre_lower == 'classical':
            return 'CLASS'
        else:
            # Show up to 6 characters for other genres
            return genre.upper()[:6]
    
    def draw(self):
        """Draw a simple, clean jukebox label."""
        canvas = self.canv
        w, h = self.width, self.height
        
        # Get genre-specific colors
        genre_config = self.genre_config.get_genre_config(self.label.genre)
        genre_color = self._hex_to_color(genre_config['background_color'])
        bg_color = self._get_genre_bg_color(genre_color)
        
        # Draw background
        canvas.setFillColor(bg_color)
        canvas.setStrokeColor(genre_color)  # Set border color to match genre
        canvas.setLineWidth(1)
        canvas.rect(0, 0, w, h, fill=1, stroke=1)
        
        # Calculate sections using configurable parameters
        genre_box_height = h * self.genre_box_height_pct
        artist_box_height = h * self.artist_box_height_pct
        
        # Calculate remaining space for A-side and B-side
        remaining_height = h - artist_box_height
        a_side_height = remaining_height / 2
        b_side_height = remaining_height / 2
        
        # Position calculations
        a_side_y = h - a_side_height
        artist_box_y = h/2 - artist_box_height/2
        genre_box_y = h/2 - genre_box_height/2
        b_side_y = 0
        
        # Genre tab dimensions
        tab_width = w * self.genre_box_width_pct
        artist_banner_x = tab_width
        artist_banner_width = w - (2 * tab_width)
        
        # Draw white artist banner with genre color border
        canvas.setFillColor(colors.white)
        canvas.setStrokeColor(genre_color)  # Set border color to match genre
        canvas.rect(artist_banner_x, artist_box_y, artist_banner_width, artist_box_height, fill=1, stroke=1)
        
        # Draw genre tabs with genre-specific color and matching border
        canvas.setFillColor(genre_color)
        canvas.setStrokeColor(genre_color)  # Set border color to match genre
        canvas.rect(0, genre_box_y, tab_width, genre_box_height, fill=1, stroke=1)  # Left
        canvas.rect(w - tab_width, genre_box_y, tab_width, genre_box_height, fill=1, stroke=1)  # Right
        
        # Text - keep it simple and readable
        canvas.setFillColor(colors.black)
        
        # A-side (top section, centered)
        canvas.setFont("Helvetica-Bold", self.main_font_size)
        a_text = self.label.a_side
        a_width = canvas.stringWidth(a_text, "Helvetica-Bold", self.main_font_size)
        # Center vertically in the A-side section, with optional offset
        a_side_text_y = a_side_y + (a_side_height / 2) - (self.main_font_size/3) + self.a_side_y_offset
        canvas.drawString(w/2 - a_width/2, a_side_text_y, a_text)
        
        # Artist (middle banner, centered)
        canvas.setFont("Helvetica-Bold", self.main_font_size)
        artist_text = self.label.get_display_artist()
        artist_width = canvas.stringWidth(artist_text, "Helvetica-Bold", self.main_font_size)
        # Center vertically in the artist box, with optional offset
        artist_text_y = artist_box_y + (artist_box_height / 2) - (self.main_font_size/3) + self.artist_y_offset
        canvas.drawString(w/2 - artist_width/2, artist_text_y, artist_text)
        
        # B-side (bottom section, centered)
        canvas.setFont("Helvetica-Bold", self.main_font_size)
        b_text = self.label.b_side
        b_width = canvas.stringWidth(b_text, "Helvetica-Bold", self.main_font_size)
        # Center vertically in the B-side section, with optional offset
        b_side_text_y = b_side_y + (b_side_height / 2) - (self.main_font_size/3) + self.b_side_y_offset
        canvas.drawString(w/2 - b_width/2, b_side_text_y, b_text)
        
        # Genre in tabs with genre-specific text color
        genre_text_color = self._hex_to_color(genre_config['text_color'])
        canvas.setFillColor(genre_text_color)
        canvas.setFont("Helvetica-Bold", self.genre_font_size)
        genre = self._format_genre_text(self.label.genre)
        g_width = canvas.stringWidth(genre, "Helvetica-Bold", self.genre_font_size)
        
        # Center vertically in the genre tabs, with optional offset
        genre_text_y = genre_box_y + (genre_box_height / 2) - (self.genre_font_size/3) + self.genre_y_offset
        # Left tab
        canvas.drawString(tab_width/2 - g_width/2, genre_text_y, genre)
        # Right tab  
        canvas.drawString(w - tab_width/2 - g_width/2, genre_text_y, genre)
    
    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)


@dataclass
class JukeBoxLabel:
    """Represents a single juke box label with all required information."""
    artist: str
    a_side: str
    b_side: str
    genre: str
    background_color: Optional[str] = None
    artist_a: Optional[str] = None
    artist_b: Optional[str] = None
    
    def get_display_artist(self) -> str:
        """Get the artist display text, combining different artists with // if needed."""
        if self.artist_a and self.artist_b and self.artist_a != self.artist_b:
            return f"{self.artist_a} // {self.artist_b}"
        elif self.artist_a:
            return self.artist_a
        elif self.artist_b:
            return self.artist_b
        else:
            return self.artist  # Fallback to original artist field


class GenreConfig:
    """Handles genre-based configuration including background colors."""
    
    def __init__(self, config_file: str = "config/genre_config.yaml"):
        self.config_path = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load genre configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default configuration
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Return default genre configuration."""
        return {
            'genres': {
                'rock': {'background_color': '#FF6B6B', 'text_color': '#FFFFFF'},
                'pop': {'background_color': '#4ECDC4', 'text_color': '#FFFFFF'},
                'jazz': {'background_color': '#45B7D1', 'text_color': '#FFFFFF'},
                'classical': {'background_color': '#96CEB4', 'text_color': '#2C3E50'},
                'blues': {'background_color': '#6C5CE7', 'text_color': '#FFFFFF'},
                'country': {'background_color': '#FDCB6E', 'text_color': '#2D3436'},
                'electronic': {'background_color': '#A29BFE', 'text_color': '#FFFFFF'},
                'reggae': {'background_color': '#00B894', 'text_color': '#FFFFFF'},
                'soul': {'background_color': '#E17055', 'text_color': '#FFFFFF'},
                'hip-hop': {'background_color': '#2D3436', 'text_color': '#FFFFFF'},
                'funk': {'background_color': '#FD79A8', 'text_color': '#FFFFFF'},
                'oldy': {'background_color': '#B8860B', 'text_color': '#FFFFFF'},
                'disco': {'background_color': '#FF1493', 'text_color': '#FFFFFF'},
                'default': {'background_color': '#DDDDDD', 'text_color': '#333333'}
            }
        }
    
    def get_genre_config(self, genre: str) -> Dict:
        """Get configuration for a specific genre."""
        genre_lower = genre.lower()
        return self.config['genres'].get(genre_lower, self.config['genres']['default'])


class LabelGenerator:
    """Generates PDF files containing juke box labels."""
    
    def __init__(self, output_dir: str = "output", label_width_mm: float = 74.0, label_height_mm: float = 28.0,
                 genre_box_width_pct: float = 15.0, genre_box_height_pct: float = 12.0,
                 artist_box_height_pct: float = 28.0, a_side_y_offset: float = 0,
                 artist_y_offset: float = 0, b_side_y_offset: float = 0, 
                 genre_y_offset: float = 0, gap_x_mm: float = 2.0, gap_y_mm: float = 2.0,
                 main_font_size: float = 12.0, genre_font_size: float = 6.0):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.genre_config = GenreConfig()
        
        # Convert mm to points (1mm = 72/25.4 points)
        mm_to_points = 72.0 / 25.4
        self.label_width = label_width_mm * mm_to_points
        self.label_height = label_height_mm * mm_to_points
        self.margin = 2.5 * mm_to_points  # 2.5mm margin
        
        # Store layout parameters (convert percentages to decimals)
        self.genre_box_width_pct = genre_box_width_pct / 100.0
        self.genre_box_height_pct = genre_box_height_pct / 100.0
        self.artist_box_height_pct = artist_box_height_pct / 100.0
        self.a_side_y_offset = a_side_y_offset
        self.artist_y_offset = artist_y_offset
        self.b_side_y_offset = b_side_y_offset
        self.genre_y_offset = genre_y_offset
        self.gap_x_mm = gap_x_mm
        self.gap_y_mm = gap_y_mm
        self.main_font_size = main_font_size
        self.genre_font_size = genre_font_size
    
    def generate_pdf(self, labels: List[JukeBoxLabel], filename: str = "jukebox_labels.pdf") -> str:
        """Generate PDF file containing all labels.
        
        Args:
            labels: List of JukeBoxLabel objects
            filename: Output PDF filename
        """
        output_path = self.output_dir / filename
        
        # Convert gap from mm to points
        mm_to_points = 72.0 / 25.4
        gap_x_points = self.gap_x_mm * mm_to_points
        gap_y_points = self.gap_y_mm * mm_to_points
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Calculate labels per row and column (accounting for gaps)
        page_width, page_height = A4
        usable_width = page_width - inch  # minus margins
        usable_height = page_height - inch
        
        # Account for gaps when calculating how many labels fit
        # Add the gap to each label dimension for spacing calculation
        effective_label_width = self.label_width + gap_x_points
        effective_label_height = self.label_height + gap_y_points
        
        labels_per_row = int(usable_width // effective_label_width)
        labels_per_col = int(usable_height // effective_label_height)
        
        story = []
        
        # Process labels in batches to fit on pages
        for i in range(0, len(labels), labels_per_row * labels_per_col):
            batch = labels[i:i + labels_per_row * labels_per_col]
            table_data = self._create_label_table(batch, labels_per_row)
            
            if table_data:
                # Create table with actual spacing between columns and rows
                col_widths = []
                for j in range(labels_per_row):
                    col_widths.append(self.label_width)
                    if j < labels_per_row - 1:  # Add gap between columns except for last
                        col_widths.append(gap_x_points)
                
                # Calculate row structure with gaps
                row_count = len(table_data)
                table_with_gaps = []
                
                for row_idx, row in enumerate(table_data):
                    # Add the regular content row
                    new_row = []
                    for col_idx, cell in enumerate(row):
                        new_row.append(cell)
                        if col_idx < len(row) - 1:  # Add gap between columns except for last
                            new_row.append("")  # Empty gap cell
                    table_with_gaps.append(new_row)
                    
                    # Add gap row between rows except for last
                    if row_idx < row_count - 1:
                        gap_row = [""] * len(new_row)
                        table_with_gaps.append(gap_row)
                
                # Set row heights including gaps
                row_heights = []
                for row_idx in range(len(table_with_gaps)):
                    if row_idx % 2 == 0:  # Content rows
                        row_heights.append(self.label_height)
                    else:  # Gap rows
                        row_heights.append(gap_y_points)
                
                table = Table(table_with_gaps, colWidths=col_widths, rowHeights=row_heights,
                            hAlign='CENTER')
                table_style = self._get_simple_table_style()
                table.setStyle(table_style)
                story.append(table)
                
                if i + labels_per_row * labels_per_col < len(labels):
                    story.append(Spacer(1, 0.5*inch))
        
        doc.build(story)
        return str(output_path)
    
    def _create_label_table(self, labels: List[JukeBoxLabel], labels_per_row: int) -> List[List]:
        """Create table data for labels."""
        table_data = []
        
        for i in range(0, len(labels), labels_per_row):
            row = []
            for j in range(labels_per_row):
                if i + j < len(labels):
                    label = labels[i + j]
                    cell_content = self._create_label_content(label)
                    row.append(cell_content)
                else:
                    row.append("")  # Empty cell
            table_data.append(row)
        
        return table_data
    
    def _create_label_content(self, label: JukeBoxLabel) -> LabelFlowable:
        """Create precise jukebox label content using custom flowable."""
        return LabelFlowable(
            label, self.label_width, self.label_height, self.genre_config,
            genre_box_width_pct=self.genre_box_width_pct,
            genre_box_height_pct=self.genre_box_height_pct,
            artist_box_height_pct=self.artist_box_height_pct,
            a_side_y_offset=self.a_side_y_offset,
            artist_y_offset=self.artist_y_offset,
            b_side_y_offset=self.b_side_y_offset,
            genre_y_offset=self.genre_y_offset,
            main_font_size=self.main_font_size,
            genre_font_size=self.genre_font_size
        )
    
    def _get_table_style(self, labels: List[JukeBoxLabel], labels_per_row: int) -> TableStyle:
        """Create table style for drawing-based labels."""
        # Use gap values from instance variables, convert to points
        mm_to_points = 72.0 / 25.4
        gap_x_points = self.gap_x_mm * mm_to_points
        gap_y_points = self.gap_y_mm * mm_to_points
        
        style_commands = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Add actual spacing between cells using GRID
            ('GRID', (0, 0), (-1, -1), gap_x_points/4, colors.white),  # Thin white grid lines for spacing
            ('LEFTPADDING', (0, 0), (-1, -1), gap_x_points/2),
            ('RIGHTPADDING', (0, 0), (-1, -1), gap_x_points/2),
            ('TOPPADDING', (0, 0), (-1, -1), gap_y_points/2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), gap_y_points/2),
        ]
        
        return TableStyle(style_commands)
    
    def _get_simple_table_style(self) -> TableStyle:
        """Create simple table style without complex spacing."""
        style_commands = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]
        return TableStyle(style_commands)


class DataLoader:
    """Loads label data from various file formats."""
    
    @staticmethod
    def load_from_json(file_path: str) -> List[JukeBoxLabel]:
        """Load labels from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        labels = []
        for item in data:
            labels.append(JukeBoxLabel(
                artist=item['artist'],
                a_side=item['a_side'],
                b_side=item['b_side'],
                genre=item['genre']
            ))
        
        return labels
    
    @staticmethod
    def load_from_csv(file_path: str) -> List[JukeBoxLabel]:
        """Load labels from CSV file."""
        import csv
        
        labels = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                labels.append(JukeBoxLabel(
                    artist=row['artist'],
                    a_side=row['a_side'],
                    b_side=row['b_side'],
                    genre=row['genre']
                ))
        
        return labels


def main():
    """Main function to demonstrate label generation."""
    # Create sample data
    sample_labels = [
        JukeBoxLabel("The Beatles", "Hey Jude", "Revolution", "Rock"),
        JukeBoxLabel("Miles Davis", "So What", "Kind of Blue", "Jazz"),
        JukeBoxLabel("Madonna", "Like a Virgin", "Material Girl", "Pop"),
        JukeBoxLabel("Johnny Cash", "Ring of Fire", "I Walk the Line", "Country"),
        JukeBoxLabel("B.B. King", "The Thrill Is Gone", "Sweet Little Angel", "Blues"),
        JukeBoxLabel("Daft Punk", "Around the World", "Da Funk", "Electronic"),
    ]
    
    # Generate PDF with default dimensions (60.0mm x 25.0mm)
    generator = LabelGenerator()
    output_file = generator.generate_pdf(sample_labels)
    print(f"PDF generated: {output_file}")


if __name__ == "__main__":
    main()