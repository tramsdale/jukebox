"""
Flask Web App for Juke Box Label Generator with Database Management
"""

from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import os
import json
import secrets
import uuid
from werkzeug.utils import secure_filename
from jukebox_generator import LabelGenerator, DataLoader, JukeBoxLabel
from dynamodb_models import JukeboxRecord, JukeboxStatus
from pathlib import Path
import tempfile

app = Flask(__name__)
# Use SECRET_KEY from environment if available, otherwise generate random key
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure session for Lambda environment
if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
    # For API Gateway, configure session cookies properly
    app.config['SESSION_COOKIE_SECURE'] = False  
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # Remove explicit path setting - let Flask handle it automatically

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Configure Flask-Login for Lambda
if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
    login_manager.session_protection = "basic"  # Reduce session protection for Lambda

# User class for authentication
class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username
    
    @property 
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return self.id

# Load users from hashed password file
try:
    from hashed_passwords import USERS
    if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
        import logging
        logging.info(f"Loaded {len(USERS)} users from hashed_passwords.py")
except ImportError as e:
    USERS = {}
    if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
        import logging
        logging.error(f"Failed to import hashed_passwords: {e}")
except Exception as e:
    USERS = {}
    if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
        import logging
        logging.error(f"Error loading users: {e}")

@login_manager.user_loader
def load_user(user_id):
    if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
        import logging
        logging.error(f"=== USER LOADER CALLED ===")
        logging.error(f"load_user called with user_id: {user_id}")
        logging.error(f"Users available: {list(USERS.keys())}")
        logging.error(f"User exists: {user_id in USERS}")
    
    if user_id in USERS:
        user = User(user_id)
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            logging.error(f"User {user_id} loaded successfully")
        return user
    
    if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
        logging.error(f"User {user_id} not found, returning None")
    return None

# DynamoDB configuration
if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
    # Lambda environment - configure for API Gateway stage
    app.config['APPLICATION_ROOT'] = '/prod'

# Configure URL generation for Lambda environment
if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
    from werkzeug.middleware.proxy_fix import ProxyFix
    # Configure proxy fix to handle API Gateway properly
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_proto=1,
        x_host=1,
        x_prefix=1,
        x_for=1,
        x_port=1
    )

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

@app.route('/debug-session')
def debug_session():
    """Debug route to check session state - only works in Lambda environment"""
    if 'AWS_LAMBDA_FUNCTION_NAME' not in os.environ:
        return "Debug route only available in Lambda environment"
    
    import logging
    logging.info("=== SESSION DEBUG ===")
    logging.info(f"Session data: {dict(session)}")
    logging.info(f"Current user: {current_user}")
    logging.info(f"Is authenticated: {current_user.is_authenticated if current_user else 'No current_user'}")
    logging.info(f"User ID: {current_user.id if current_user and hasattr(current_user, 'id') else 'No ID'}")
    logging.info(f"Request cookies: {dict(request.cookies)}")
    logging.info(f"Request path: {request.path}")
    logging.info(f"Request method: {request.method}")
    
    return jsonify({
        'session': dict(session),
        'authenticated': current_user.is_authenticated if current_user else False,
        'user_id': current_user.id if current_user and hasattr(current_user, 'id') else None,
        'cookies': dict(request.cookies),
        'path': request.path
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
        import logging
        logging.info(f"Login route accessed with method: {request.method}")
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Add debugging for Lambda environment
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            logging.info(f"Login attempt for user: {username}")
            logging.info(f"Users available: {list(USERS.keys())}")
            logging.info(f"Password hash exists: {username in USERS}")
            logging.info(f"SECRET_KEY configured: {bool(app.secret_key)}")
        
        if username in USERS and check_password_hash(USERS[username], password):
            user = User(username)
            login_result = login_user(user, remember=True)  # Add remember=True
            if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
                logging.info(f"Login successful for {username}: {login_result}")
                logging.info(f"User authenticated: {user.is_authenticated}")
                logging.info(f"Session data after login_user: {dict(session)}")
                # Test if we can load the user immediately
                test_user = load_user(username)
                logging.info(f"Test load_user result: {test_user}")
            
            next_page = request.args.get('next')
            redirect_url = next_page if next_page else url_for('index')
            if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
                logging.info(f"Redirecting to: {redirect_url}")
            return redirect(redirect_url)
        else:
            if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
                logging.info(f"Login failed for {username}")
                if username in USERS:
                    logging.info("Username exists but password check failed")
                else:
                    logging.info("Username not found in USERS")
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
    if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
        import logging
        logging.info(f"Index route accessed")
        logging.info(f"Current user authenticated: {current_user.is_authenticated if current_user else 'No current_user'}")
        logging.info(f"Current user ID: {current_user.id if current_user and hasattr(current_user, 'id') else 'No ID'}")
        logging.info(f"Session data: {dict(session)}")
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
            'width': float(request.form.get('width', 76.0)),
            'height': float(request.form.get('height', 26.0)),
            'genre_box_width_pct': float(request.form.get('genre_box_width_pct', 15.0)),
            'genre_box_height_pct': float(request.form.get('genre_box_height_pct', 12.0)),
            'artist_box_height_pct': float(request.form.get('artist_box_height_pct', 28.0)),
            'a_side_y_offset': float(request.form.get('a_side_y_offset', 0.0)),
            'artist_y_offset': float(request.form.get('artist_y_offset', 0.0)),
            'b_side_y_offset': float(request.form.get('b_side_y_offset', 0.0)),
            'genre_y_offset': float(request.form.get('genre_y_offset', 0.0)),
            'gap_x_mm': float(request.form.get('gap_x_mm', 2.0)),
            'gap_y_mm': float(request.form.get('gap_y_mm', 2.0)),
            'main_font_size': float(request.form.get('main_font_size', 12.0)),
            'genre_font_size': float(request.form.get('genre_font_size', 6.0))
        }
        flash('Settings saved successfully!')
        return redirect(url_for('settings'))
    
    # Get current settings from session or use defaults
    current_settings = get_label_settings()
    
    return render_template('settings.html', **current_settings, message=request.args.get('message'))

def get_label_settings():
    """Helper function to get current label settings from session or defaults."""
    defaults = {
        'width': 76.0,
        'height': 26.0,
        'genre_box_width_pct': 15.0,
        'genre_box_height_pct': 12.0,
        'artist_box_height_pct': 28.0,
        'a_side_y_offset': 0.0,
        'artist_y_offset': 0.0,
        'b_side_y_offset': 0.0,
        'genre_y_offset': 0.0,
        'gap_x_mm': 2.0,
        'gap_y_mm': 2.0,
        'main_font_size': 12.0,
        'genre_font_size': 6.0
    }
    
    current_settings = session.get('label_settings', {})
    
    # Migrate old sessions to new defaults
    needs_update = False
    for key, new_default in defaults.items():
        if key not in current_settings:
            current_settings[key] = new_default
            needs_update = True
        elif key in ['main_font_size'] and current_settings[key] == 14.0:
            # Migrate old font size default
            current_settings[key] = 12.0
            needs_update = True
        elif key.endswith('_offset') and current_settings[key] == 2.0:
            # Migrate old offset defaults
            current_settings[key] = 0.0
            needs_update = True
    
    if needs_update:
        session['label_settings'] = current_settings
    
    return current_settings

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
        main_font_size = float(request.form.get('main_font_size', settings['main_font_size']))
        genre_font_size = float(request.form.get('genre_font_size', settings['genre_font_size']))
        
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
            gap_y_mm=gap_y_mm,
            main_font_size=main_font_size,
            genre_font_size=genre_font_size
        )
        
        # Create temporary file for PDF with explicit directory
        import uuid
        temp_filename = f'jukebox_labels_{uuid.uuid4().hex[:8]}.pdf'
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            temp_path = f'/tmp/{temp_filename}'
        else:
            temp_path = os.path.join(OUTPUT_FOLDER, temp_filename)
        
        try:
            output_path = generator.generate_pdf(labels, temp_path)
            
            return send_file(
                output_path,
                as_attachment=True,
                download_name='jukebox_labels.pdf',
                mimetype='application/pdf'
            )
        except Exception as e:
            # Clean up on error
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
            raise
    
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}')
        return redirect(url_for('index'))

@app.route('/test-logging')
def test_logging():
    """Test route to verify logging works"""
    if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
        import logging
        logging.error("=== TEST LOGGING ROUTE CALLED ===")
        logging.error("This is a test error message")
        return "Test logging complete - check logs"
    else:
        return "Test route - only works in Lambda"

@app.route('/sample')
@login_required
def generate_sample():
    # Force error logging to make sure we see this
    import logging
    logging.error("=== SAMPLE PDF ROUTE CALLED ===")
    logging.error(f"Request method: {request.method}")
    logging.error(f"Request path: {request.path}")
    logging.error(f"Full URL: {request.url}")
    logging.error(f"Current user authenticated: {current_user.is_authenticated}")
    logging.error(f"Current user: {current_user}")
    logging.error(f"Session data: {dict(session)}")
    logging.error(f"Session _user_id: {session.get('_user_id')}")
    
    try:
        # Add logging to track route access
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            logging.error("Lambda environment detected in sample route")
            logging.error("Getting label settings...")
        
        # Get settings from session or query params
        settings = get_label_settings()
        
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            logging.error(f"Settings retrieved: {settings}")
        
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
        main_font_size = float(request.args.get('main_font_size', settings['main_font_size']))
        genre_font_size = float(request.args.get('genre_font_size', settings['genre_font_size']))
        
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            logging.error("Creating sample data...")
        
        # Create sample data
        sample_labels = [
            JukeBoxLabel("The Beatles", "Hey Jude", "Revolution", "Rock"),
            JukeBoxLabel("Miles Davis", "So What", "Kind of Blue", "Jazz"),
            JukeBoxLabel("Madonna", "Like a Virgin", "Material Girl", "Pop"),
            JukeBoxLabel("Johnny Cash", "Ring of Fire", "I Walk the Line", "Country"),
            JukeBoxLabel("B.B. King", "The Thrill Is Gone", "Sweet Little Angel", "Blues"),
            JukeBoxLabel("Daft Punk", "Around the World", "Da Funk", "Electronic"),
        ]
        
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            logging.error(f"Created {len(sample_labels)} sample labels")
            logging.error("Initializing LabelGenerator...")
        
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
            gap_y_mm=gap_y_mm,
            main_font_size=main_font_size,
            genre_font_size=genre_font_size
        )
        
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            logging.error("LabelGenerator initialized successfully")
            logging.error(f"Output folder: {OUTPUT_FOLDER}")
        
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            logging.error("Creating temporary filename...")
        
        # Create temporary file for PDF with explicit directory
        import uuid
        temp_filename = f'sample_jukebox_labels_{uuid.uuid4().hex[:8]}.pdf'
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            temp_path = f'/tmp/{temp_filename}'
            import logging
            logging.error(f"Lambda environment: Creating PDF at {temp_path}")
        else:
            temp_path = os.path.join(OUTPUT_FOLDER, temp_filename)
        
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            logging.error("Starting PDF generation try block...")
        
        try:
            if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
                logging.error(f"Generating PDF with {len(sample_labels)} labels")
                logging.error(f"Generator output dir: {OUTPUT_FOLDER}")
                logging.error(f"Temp path: {temp_path}")
                logging.error("About to call generator.generate_pdf()...")
                
            output_path = generator.generate_pdf(sample_labels, temp_path)
            
            if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
                logging.error("generator.generate_pdf() completed successfully!")
                logging.error(f"PDF generated successfully at {output_path}")
                logging.error(f"File exists: {os.path.exists(output_path)}")
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logging.error(f"File size: {file_size} bytes")
                    
                    # Check if it's actually a PDF by reading first few bytes
                    try:
                        with open(output_path, 'rb') as f:
                            first_bytes = f.read(20)
                            logging.error(f"First 20 bytes: {first_bytes}")
                            is_pdf = first_bytes.startswith(b'%PDF')
                            logging.error(f"Starts with PDF header: {is_pdf}")
                    except Exception as read_error:
                        logging.error(f"Error reading generated file: {read_error}")
                else:
                    logging.error("Generated file does not exist!")
                    
            logging.error("About to serve file...")
            
            # Try using send_file directly - let serverless-wsgi handle everything
            return send_file(
                output_path,
                as_attachment=True,
                download_name='sample_jukebox_labels.pdf',
                mimetype='application/pdf'
            )
        except Exception as pdf_error:
            if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
                logging.error(f"PDF generation error: {pdf_error}")
                import traceback
                logging.error(f"PDF generation traceback: {traceback.format_exc()}")
            # Clean up on error
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
            raise
    
    except Exception as e:
        flash(f'Error generating sample PDF: {str(e)}')
        return redirect(url_for('index'))

@app.route('/database')
@login_required
def database():
    """Show database records with filtering and sorting."""
    try:
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            import logging
            logging.info("Database route accessed in Lambda environment")
        
        # Get filter and sort parameters
        status_filter = request.args.get('status', '')
        search_query = request.args.get('search', '')
        sort_by = request.args.get('sort', 'id')
        sort_order = request.args.get('order', 'asc')
        
        # Get records from DynamoDB
        records = JukeboxRecord.scan_all(
            status_filter=status_filter if status_filter else None,
            search_query=search_query if search_query else None
        )
        
        # Sort records (DynamoDB doesn't support all sorting options)
        if sort_by == 'id':
            records.sort(key=lambda x: x.id, reverse=(sort_order == 'desc'))
        elif sort_by == 'track_a_side':
            records.sort(key=lambda x: x.track_a_side.lower(), reverse=(sort_order == 'desc'))
        elif sort_by == 'artist_a_side':
            records.sort(key=lambda x: x.artist_a_side.lower(), reverse=(sort_order == 'desc'))
        elif sort_by == 'status':
            records.sort(key=lambda x: x.status.value, reverse=(sort_order == 'desc'))
        elif sort_by == 'jukebox_id':
            records.sort(key=lambda x: x.jukebox_id or '', reverse=(sort_order == 'desc'))
        
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            logging.info(f"Retrieved {len(records)} records from DynamoDB")
        
        return render_template('database.html', 
                             records=records,
                             statuses=JukeboxStatus,
                             current_status=status_filter,
                             current_search=search_query,
                             current_sort=sort_by,
                             current_order=sort_order)
                             
    except Exception as e:
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            import logging
            logging.error(f"Database route error: {e}")
            logging.error(f"Error type: {type(e)}")
            import traceback
            logging.error(f"Full traceback: {traceback.format_exc()}")
        
        # Return JSON error for debugging in Lambda
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            return jsonify({'error': str(e), 'type': str(type(e))})
        else:
            flash(f'Error accessing database: {str(e)}')
            return redirect(url_for('index'))

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
            record.save()
            flash('Record added successfully!')
            return redirect(url_for('database'))
        except Exception as e:
            flash(f'Error adding record: {str(e)}')
    
    return render_template('add_record.html', statuses=JukeboxStatus)

@app.route('/database/edit/<record_id>', methods=['GET', 'POST'])
@login_required
def edit_record(record_id):
    """Edit an existing jukebox record."""
    record = JukeboxRecord.get_by_id(record_id)
    if not record:
        flash('Record not found')
        return redirect(url_for('database'))
    
    if request.method == 'POST':
        try:
            record.track_a_side = request.form['track_a_side']
            record.track_b_side = request.form['track_b_side']
            record.artist_a_side = request.form['artist_a_side']
            record.artist_b_side = request.form['artist_b_side']
            record.genre = request.form.get('genre') or None
            record.status = JukeboxStatus(request.form['status'])
            record.jukebox_id = request.form['jukebox_id'] if request.form['jukebox_id'] else None
            
            record.save()
            flash('Record updated successfully!')
            return redirect(url_for('database'))
        except Exception as e:
            flash(f'Error updating record: {str(e)}')
    
    return render_template('edit_record.html', record=record, statuses=JukeboxStatus)

@app.route('/database/delete/<record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    """Delete a jukebox record."""
    try:
        record = JukeboxRecord.get_by_id(record_id)
        if record:
            record.delete()
            flash('Record deleted successfully!')
        else:
            flash('Record not found')
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
        records = JukeboxRecord.get_by_ids(record_ids)
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
            gap_y_mm=settings['gap_y_mm'],
            main_font_size=settings['main_font_size'],
            genre_font_size=settings['genre_font_size']
        )
        
        # Create temporary file for PDF with explicit directory
        import uuid
        temp_filename = f'selected_jukebox_labels_{uuid.uuid4().hex[:8]}.pdf'
        if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
            temp_path = f'/tmp/{temp_filename}'
        else:
            temp_path = os.path.join(OUTPUT_FOLDER, temp_filename)
        
        try:
            output_path = generator.generate_pdf(labels, temp_path)
            
            return send_file(
                output_path,
                as_attachment=True,
                download_name='selected_jukebox_labels.pdf',
                mimetype='application/pdf'
            )
        except Exception as e:
            # Clean up on error
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
            raise
    
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}')
        return redirect(url_for('database'))

@app.route('/api/records')
@login_required
def api_records():
    """API endpoint for getting records as JSON."""
    records = JukeboxRecord.scan_all()
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
                    artist_a = row['Artist A side'].strip()
                    track_a = row['Track A side'].strip()
                    
                    # Simple duplicate check - scan existing records
                    existing_records = JukeboxRecord.scan_all()
                    existing = any(
                        r.artist_a_side == artist_a and r.track_a_side == track_a
                        for r in existing_records
                    )
                    
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Create new record
                    record = JukeboxRecord(
                        track_a_side=track_a,
                        track_b_side=row.get('Track B side', '').strip() or 'Unknown',
                        artist_a_side=artist_a,
                        artist_b_side=row.get('Artist B side', '').strip() or artist_a,
                        genre=row.get('Genre', '').strip() or None,
                        status=status,
                        jukebox_id=jukebox_id
                    )
                    
                    record.save()
                    imported_count += 1
                flash(f'Successfully imported {imported_count} records. {skipped_count} records were skipped.')
                return redirect(url_for('database'))
                
            except Exception as e:
                flash(f'Error importing CSV: {str(e)}')
        else:
            flash('Please upload a CSV file')
    
    return render_template('import_csv.html')

if __name__ == '__main__':
    app.run(debug=True)