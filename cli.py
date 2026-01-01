#!/usr/bin/env python3
"""
Command-line interface for the Juke Box Label Generator
"""

import argparse
import sys
from pathlib import Path
from jukebox_generator import LabelGenerator, DataLoader, JukeBoxLabel


def main():
    parser = argparse.ArgumentParser(description='Generate PDF juke box labels')
    parser.add_argument('--input', '-i', type=str, help='Input file (JSON or CSV)')
    parser.add_argument('--output', '-o', type=str, default='jukebox_labels.pdf', 
                       help='Output PDF filename')
    parser.add_argument('--format', '-f', choices=['json', 'csv'], 
                       help='Input file format (auto-detected if not specified)')
    parser.add_argument('--sample', action='store_true', 
                       help='Generate PDF with sample data')
    parser.add_argument('--width', '-w', type=float, default=60.0,
                       help='Label width in millimeters (default: 60.0mm)')
    parser.add_argument('--height', type=float, default=25.0,
                       help='Label height in millimeters (default: 25.0mm)')
    
    args = parser.parse_args()
    
    generator = LabelGenerator(label_width_mm=args.width, label_height_mm=args.height)
    
    if args.sample:
        # Use built-in sample data
        sample_labels = [
            JukeBoxLabel("The Beatles", "Hey Jude", "Revolution", "Rock"),
            JukeBoxLabel("Miles Davis", "So What", "Kind of Blue", "Jazz"),
            JukeBoxLabel("Madonna", "Like a Virgin", "Material Girl", "Pop"),
            JukeBoxLabel("Johnny Cash", "Ring of Fire", "I Walk the Line", "Country"),
            JukeBoxLabel("B.B. King", "The Thrill Is Gone", "Sweet Little Angel", "Blues"),
            JukeBoxLabel("Daft Punk", "Around the World", "Da Funk", "Electronic"),
        ]
        labels = sample_labels
        print(f"Using sample data with labels {args.width}mm x {args.height}mm...")
        
    elif args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file '{args.input}' not found")
            sys.exit(1)
        
        # Auto-detect format if not specified
        file_format = args.format
        if not file_format:
            if input_path.suffix.lower() == '.json':
                file_format = 'json'
            elif input_path.suffix.lower() == '.csv':
                file_format = 'csv'
            else:
                print("Error: Cannot auto-detect file format. Please specify --format")
                sys.exit(1)
        
        # Load data
        try:
            if file_format == 'json':
                labels = DataLoader.load_from_json(args.input)
            else:  # csv
                labels = DataLoader.load_from_csv(args.input)
            print(f"Loaded {len(labels)} labels from {args.input}")
        except Exception as e:
            print(f"Error loading data: {e}")
            sys.exit(1)
    else:
        print("Error: Please specify --input file or --sample")
        parser.print_help()
        sys.exit(1)
    
    # Generate PDF
    try:
        output_path = generator.generate_pdf(labels, args.output)
        print(f"PDF generated successfully: {output_path}")
        print(f"Generated {len(labels)} labels")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()