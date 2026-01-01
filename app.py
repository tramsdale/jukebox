"""
Flask Web App for Juke Box Label Generator
"""

from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
import json
from werkzeug.utils import secure_filename
from jukebox_generator import LabelGenerator, DataLoader, JukeBoxLabel
from pathlib import Path
import tempfile

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this in production
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'json', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manual')
def manual_entry():
    return render_template('manual.html')

@app.route('/generate', methods=['POST'])
def generate_pdf():
    try:
        # Get form data
        width = float(request.form.get('width', 74.0))
        height = float(request.form.get('height', 28.0))
        genre_box_width_pct = float(request.form.get('genre_box_width_pct', 10.0))
        genre_box_height_pct = float(request.form.get('genre_box_height_pct', 33.0))
        artist_box_height_pct = float(request.form.get('artist_box_height_pct', 33.0))
        a_side_y_offset = float(request.form.get('a_side_y_offset', 2.0))
        artist_y_offset = float(request.form.get('artist_y_offset', 2.0))
        b_side_y_offset = float(request.form.get('b_side_y_offset', 2.0))
        genre_y_offset = float(request.form.get('genre_y_offset', 2.0))
        gap_x_mm = float(request.form.get('gap_x_mm', 2.0))
        gap_y_mm = float(request.form.get('gap_y_mm', 2.0))
        
        labels = []
        
        # Check if file was uploaded
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Load labels from file
                if filename.lower().endswith('.json'):
                    labels = DataLoader.load_from_json(filepath)
                else:  # CSV
                    labels = DataLoader.load_from_csv(filepath)
                
                # Clean up uploaded file
                os.remove(filepath)
        
        # Check for manual entry
        elif request.form.get('artist'):
            # Single label from form
            labels = [JukeBoxLabel(
                artist=request.form['artist'],
                a_side=request.form['a_side'],
                b_side=request.form['b_side'],
                genre=request.form['genre']
            )]
        
        # Check for multiple manual entries (JSON format)
        elif request.form.get('labels_json'):
            try:
                labels_data = json.loads(request.form['labels_json'])
                labels = [JukeBoxLabel(
                    artist=item['artist'],
                    a_side=item['a_side'],
                    b_side=item['b_side'],
                    genre=item['genre']
                ) for item in labels_data]
            except json.JSONDecodeError:
                flash('Invalid JSON format in labels data')
                return redirect(url_for('manual_entry'))
        
        else:
            flash('Please provide label data via file upload or manual entry')
            return redirect(url_for('index'))
        
        if not labels:
            flash('No valid labels found')
            return redirect(url_for('index'))
        
        # Generate PDF
        generator = LabelGenerator(
            label_width_mm=width, 
            label_height_mm=height,
            genre_box_width_pct=genre_box_width_pct,
            genre_box_height_pct=genre_box_height_pct,
            artist_box_height_pct=artist_box_height_pct,
            a_side_y_offset=a_side_y_offset,
            artist_y_offset=artist_y_offset,
            b_side_y_offset=b_side_y_offset,
            genre_y_offset=genre_y_offset,
            gap_x_mm=gap_x_mm,
            gap_y_mm=gap_y_mm
        )
        
        # Create temporary file for PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            output_path = generator.generate_pdf(labels, tmp_file.name)
            
            return send_file(
                output_path,
                as_attachment=False,
                download_name='jukebox_labels.pdf',
                mimetype='application/pdf'
            )
    
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}')
        return redirect(url_for('index'))

@app.route('/sample')
def generate_sample():
    try:
        # Get dimensions and layout parameters from query params
        width = float(request.args.get('width', 74.0))
        height = float(request.args.get('height', 28.0))
        genre_box_width_pct = float(request.args.get('genre_box_width_pct', 10.0))
        genre_box_height_pct = float(request.args.get('genre_box_height_pct', 33.0))
        artist_box_height_pct = float(request.args.get('artist_box_height_pct', 33.0))
        a_side_y_offset = float(request.args.get('a_side_y_offset', 2.0))
        artist_y_offset = float(request.args.get('artist_y_offset', 2.0))
        b_side_y_offset = float(request.args.get('b_side_y_offset', 2.0))
        genre_y_offset = float(request.args.get('genre_y_offset', 2.0))
        gap_x_mm = float(request.args.get('gap_x_mm', 2.0))
        gap_y_mm = float(request.args.get('gap_y_mm', 2.0))
        
        # Create sample data
        sample_labels = [
            JukeBoxLabel("The Beatles", "Hey Jude", "Revolution", "Rock"),
            JukeBoxLabel("Miles Davis", "So What", "Kind of Blue", "Jazz"),
            JukeBoxLabel("Madonna", "Like a Virgin", "Material Girl", "Pop"),
            JukeBoxLabel("Johnny Cash", "Ring of Fire", "I Walk the Line", "Country"),
            JukeBoxLabel("B.B. King", "The Thrill Is Gone", "Sweet Little Angel", "Blues"),
            JukeBoxLabel("Daft Punk", "Around the World", "Da Funk", "Electronic"),
        ]
        
        # Generate PDF
        generator = LabelGenerator(
            label_width_mm=width, 
            label_height_mm=height,
            genre_box_width_pct=genre_box_width_pct,
            genre_box_height_pct=genre_box_height_pct,
            artist_box_height_pct=artist_box_height_pct,
            a_side_y_offset=a_side_y_offset,
            artist_y_offset=artist_y_offset,
            b_side_y_offset=b_side_y_offset,
            genre_y_offset=genre_y_offset,
            gap_x_mm=gap_x_mm,
            gap_y_mm=gap_y_mm
        )
        
        # Create temporary file for PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            output_path = generator.generate_pdf(sample_labels, tmp_file.name)
            
            return send_file(
                output_path,
                as_attachment=False,
                download_name='sample_jukebox_labels.pdf',
                mimetype='application/pdf'
            )
    
    except Exception as e:
        flash(f'Error generating sample PDF: {str(e)}')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)