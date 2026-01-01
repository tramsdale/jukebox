"""
Flask Web App for Juke Box Label Generator with Database Management
"""

from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import os
import json
import secrets
from werkzeug.utils import secure_filename
from jukebox_generator import LabelGenerator, DataLoader, JukeBoxLabel
from models import db, JukeboxRecord, JukeboxStatus
from flask_migrate import Migrate
from pathlib import Path
import tempfile
from sqlalchemy import or_, and_

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate random secret key
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# User class for authentication
class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username

# Load users from hashed password file
try:
    from hashed_passwords import USERS
except ImportError:
    USERS = {}

@login_manager.user_loader
def load_user(user_id):
    if user_id in USERS:
        return User(user_id)
    return None

# Database configuration
if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
    # Lambda environment - use environment variable or default to SQLite in /tmp
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///tmp/jukebox.db'
    )
    # Ensure /tmp directory exists and is writable
    os.makedirs('/tmp', exist_ok=True)
else:
    # Local development
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///jukebox.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
}

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Configure directories for Lambda/local environment
if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
    # Lambda environment
    UPLOAD_FOLDER = '/tmp/uploads'
    OUTPUT_FOLDER = '/tmp/output'
else:
    # Local development
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'output'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'json', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS and check_password_hash(USERS[username], password):
            user = User(username)
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/manual')
@login_required
def manual_entry():
    return render_template('manual.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Settings page for label layout configuration."""
    if request.method == 'POST':
        # Save settings to session
        session['label_settings'] = {
            'width': float(request.form.get('width', 74.0)),
            'height': float(request.form.get('height', 28.0)),
            'genre_box_width_pct': float(request.form.get('genre_box_width_pct', 15.0)),
            'genre_box_height_pct': float(request.form.get('genre_box_height_pct', 12.0)),
            'artist_box_height_pct': float(request.form.get('artist_box_height_pct', 28.0)),
            'a_side_y_offset': float(request.form.get('a_side_y_offset', 2.0)),
            'artist_y_offset': float(request.form.get('artist_y_offset', 2.0)),
            'b_side_y_offset': float(request.form.get('b_side_y_offset', 2.0)),
            'genre_y_offset': float(request.form.get('genre_y_offset', 2.0)),
            'gap_x_mm': float(request.form.get('gap_x_mm', 2.0)),
            'gap_y_mm': float(request.form.get('gap_y_mm', 2.0))
        }
        flash('Settings saved successfully!')
        return redirect(url_for('settings'))
    
    # Get current settings from session or use defaults
    current_settings = session.get('label_settings', {
        'width': 74.0,
        'height': 28.0,
        'genre_box_width_pct': 15.0,
        'genre_box_height_pct': 12.0,
        'artist_box_height_pct': 28.0,
        'a_side_y_offset': 2.0,
        'artist_y_offset': 2.0,
        'b_side_y_offset': 2.0,
        'genre_y_offset': 2.0,
        'gap_x_mm': 2.0,
        'gap_y_mm': 2.0
    })
    
    return render_template('settings.html', **current_settings, message=request.args.get('message'))

def get_label_settings():
    """Helper function to get current label settings from session or defaults."""
    return session.get('label_settings', {
        'width': 74.0,
        'height': 28.0,
        'genre_box_width_pct': 15.0,
        'genre_box_height_pct': 12.0,
        'artist_box_height_pct': 28.0,
        'a_side_y_offset': 2.0,
        'artist_y_offset': 2.0,
        'b_side_y_offset': 2.0,
        'genre_y_offset': 2.0,
        'gap_x_mm': 2.0,
        'gap_y_mm': 2.0
    })

@app.route('/generate', methods=['POST'])
@login_required
def generate_pdf():
    try:
        # Get settings from session or form data
        settings = get_label_settings()
        
        # Override with form data if provided
        width = float(request.form.get('width', settings['width']))
        height = float(request.form.get('height', settings['height']))
        genre_box_width_pct = float(request.form.get('genre_box_width_pct', settings['genre_box_width_pct']))
        genre_box_height_pct = float(request.form.get('genre_box_height_pct', settings['genre_box_height_pct']))
        artist_box_height_pct = float(request.form.get('artist_box_height_pct', settings['artist_box_height_pct']))
        a_side_y_offset = float(request.form.get('a_side_y_offset', settings['a_side_y_offset']))
        artist_y_offset = float(request.form.get('artist_y_offset', settings['artist_y_offset']))
        b_side_y_offset = float(request.form.get('b_side_y_offset', settings['b_side_y_offset']))
        genre_y_offset = float(request.form.get('genre_y_offset', settings['genre_y_offset']))
        gap_x_mm = float(request.form.get('gap_x_mm', settings['gap_x_mm']))
        gap_y_mm = float(request.form.get('gap_y_mm', settings['gap_y_mm']))
        
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
            output_dir=OUTPUT_FOLDER,
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
@login_required
def generate_sample():
    try:
        # Get settings from session or query params
        settings = get_label_settings()
        
        # Override with query params if provided
        width = float(request.args.get('width', settings['width']))
        height = float(request.args.get('height', settings['height']))
        genre_box_width_pct = float(request.args.get('genre_box_width_pct', settings['genre_box_width_pct']))
        genre_box_height_pct = float(request.args.get('genre_box_height_pct', settings['genre_box_height_pct']))
        artist_box_height_pct = float(request.args.get('artist_box_height_pct', settings['artist_box_height_pct']))
        a_side_y_offset = float(request.args.get('a_side_y_offset', settings['a_side_y_offset']))
        artist_y_offset = float(request.args.get('artist_y_offset', settings['artist_y_offset']))
        b_side_y_offset = float(request.args.get('b_side_y_offset', settings['b_side_y_offset']))
        genre_y_offset = float(request.args.get('genre_y_offset', settings['genre_y_offset']))
        gap_x_mm = float(request.args.get('gap_x_mm', settings['gap_x_mm']))
        gap_y_mm = float(request.args.get('gap_y_mm', settings['gap_y_mm']))
        
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
            output_dir=OUTPUT_FOLDER,
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

# Database management routes
@app.route('/database')
@login_required
def database():
    """Show database records with filtering and sorting."""
    # Get filter and sort parameters
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'id')
    sort_order = request.args.get('order', 'asc')
    
    # Build query
    query = JukeboxRecord.query
    
    # Apply status filter
    if status_filter:
        query = query.filter(JukeboxRecord.status == JukeboxStatus(status_filter))
    
    # Apply search filter
    if search_query:
        search_term = f'%{search_query}%'
        query = query.filter(or_(
            JukeboxRecord.track_a_side.ilike(search_term),
            JukeboxRecord.track_b_side.ilike(search_term),
            JukeboxRecord.artist_a_side.ilike(search_term),
            JukeboxRecord.artist_b_side.ilike(search_term),
            JukeboxRecord.jukebox_id.ilike(search_term)
        ))
    
    # Apply sorting
    if hasattr(JukeboxRecord, sort_by):
        column = getattr(JukeboxRecord, sort_by)
        if sort_order == 'desc':
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    
    records = query.all()
    
    return render_template('database.html', 
                         records=records,
                         statuses=JukeboxStatus,
                         current_status=status_filter,
                         current_search=search_query,
                         current_sort=sort_by,
                         current_order=sort_order)

@app.route('/database/add', methods=['GET', 'POST'])
@login_required
def add_record():
    """Add a new jukebox record."""
    if request.method == 'POST':
        try:
            record = JukeboxRecord(
                track_a_side=request.form['track_a_side'],
                track_b_side=request.form['track_b_side'],
                artist_a_side=request.form['artist_a_side'],
                artist_b_side=request.form['artist_b_side'],
                genre=request.form.get('genre') or None,
                status=JukeboxStatus(request.form['status']),
                jukebox_id=request.form['jukebox_id'] if request.form['jukebox_id'] else None
            )
            db.session.add(record)
            db.session.commit()
            flash('Record added successfully!')
            return redirect(url_for('database'))
        except Exception as e:
            flash(f'Error adding record: {str(e)}')
    
    return render_template('add_record.html', statuses=JukeboxStatus)

@app.route('/database/edit/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_record(record_id):
    """Edit an existing jukebox record."""
    record = JukeboxRecord.query.get_or_404(record_id)
    
    if request.method == 'POST':
        try:
            record.track_a_side = request.form['track_a_side']
            record.track_b_side = request.form['track_b_side']
            record.artist_a_side = request.form['artist_a_side']
            record.artist_b_side = request.form['artist_b_side']
            record.genre = request.form.get('genre') or None
            record.status = JukeboxStatus(request.form['status'])
            record.jukebox_id = request.form['jukebox_id'] if request.form['jukebox_id'] else None
            
            db.session.commit()
            flash('Record updated successfully!')
            return redirect(url_for('database'))
        except Exception as e:
            flash(f'Error updating record: {str(e)}')
    
    return render_template('edit_record.html', record=record, statuses=JukeboxStatus)

@app.route('/database/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    """Delete a jukebox record."""
    try:
        record = JukeboxRecord.query.get_or_404(record_id)
        db.session.delete(record)
        db.session.commit()
        flash('Record deleted successfully!')
    except Exception as e:
        flash(f'Error deleting record: {str(e)}')
    
    return redirect(url_for('database'))

@app.route('/database/print', methods=['POST'])
@login_required
def print_selected():
    """Generate PDF for selected database records."""
    try:
        record_ids = request.form.getlist('selected_records')
        if not record_ids:
            flash('No records selected for printing')
            return redirect(url_for('database'))
        
        # Get settings from session or defaults
        settings = get_label_settings()
        
        # Get selected records and convert to labels
        records = JukeboxRecord.query.filter(JukeboxRecord.id.in_(record_ids)).all()
        labels = []
        
        for record in records:
            # Generate label using A-side as primary
            labels.append(record.to_jukebox_label(use_a_side=True))
        
        # Generate PDF
        generator = LabelGenerator(
            output_dir=OUTPUT_FOLDER,
            label_width_mm=settings['width'],
            label_height_mm=settings['height'],
            genre_box_width_pct=settings['genre_box_width_pct'],
            genre_box_height_pct=settings['genre_box_height_pct'],
            artist_box_height_pct=settings['artist_box_height_pct'],
            a_side_y_offset=settings['a_side_y_offset'],
            artist_y_offset=settings['artist_y_offset'],
            b_side_y_offset=settings['b_side_y_offset'],
            genre_y_offset=settings['genre_y_offset'],
            gap_x_mm=settings['gap_x_mm'],
            gap_y_mm=settings['gap_y_mm']
        )
        
        # Create temporary file for PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            output_path = generator.generate_pdf(labels, tmp_file.name)
            
            return send_file(
                output_path,
                as_attachment=False,
                download_name='selected_jukebox_labels.pdf',
                mimetype='application/pdf'
            )
    
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}')
        return redirect(url_for('database'))

@app.route('/api/records')
@login_required
def api_records():
    """API endpoint for getting records as JSON."""
    records = JukeboxRecord.query.all()
    return jsonify([record.to_dict() for record in records])

@app.route('/database/import', methods=['GET', 'POST'])
@login_required
def import_csv():
    """Import jukebox records from CSV file."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file and file.filename.lower().endswith('.csv'):
            try:
                import csv
                import io
                
                # Read CSV content
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_input = csv.DictReader(stream)
                
                imported_count = 0
                skipped_count = 0
                
                for row in csv_input:
                    # Skip rows with missing essential data
                    if not row.get('Artist A side') or not row.get('Track A side'):
                        skipped_count += 1
                        continue
                    
                    # Map the status from CSV to our enum
                    in_jukebox_value = row.get('In Jukebox', '').strip()
                    if in_jukebox_value in ['Y', '`']:  # Handle both Y and backtick
                        status = JukeboxStatus.IN_JUKEBOX
                    elif in_jukebox_value == 'New':
                        status = JukeboxStatus.NEW
                    else:
                        status = JukeboxStatus.IN_STORAGE  # Default for empty/unknown
                    
                    # Get jukebox ID (format as 3-digit string)
                    jukebox_id_raw = row.get('Jukebox ID', '').strip()
                    jukebox_id = None
                    if jukebox_id_raw and jukebox_id_raw.isdigit():
                        jukebox_id = str(int(jukebox_id_raw)).zfill(3)
                    
                    # Check if record already exists (by artist A side and track A side)
                    existing = JukeboxRecord.query.filter(
                        JukeboxRecord.artist_a_side == row['Artist A side'].strip(),
                        JukeboxRecord.track_a_side == row['Track A side'].strip()
                    ).first()
                    
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Create new record
                    record = JukeboxRecord(
                        track_a_side=row['Track A side'].strip(),
                        track_b_side=row.get('Track B side', '').strip() or 'Unknown',
                        artist_a_side=row['Artist A side'].strip(),
                        artist_b_side=row.get('Artist B side', '').strip() or row['Artist A side'].strip(),
                        genre=row.get('Genre', '').strip() or None,
                        status=status,
                        jukebox_id=jukebox_id
                    )
                    
                    db.session.add(record)
                    imported_count += 1
                
                db.session.commit()
                flash(f'Successfully imported {imported_count} records. {skipped_count} records were skipped.')
                return redirect(url_for('database'))
                
            except Exception as e:
                flash(f'Error importing CSV: {str(e)}')
        else:
            flash('Please upload a CSV file')
    
    return render_template('import_csv.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)