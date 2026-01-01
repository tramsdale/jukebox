# Database Configuration Guide

## For Local Development (SQLite - simpler for testing)

If you want to test locally before setting up MySQL, you can use SQLite by setting this environment variable:

```bash
export DATABASE_URL="sqlite:///jukebox.db"
```

## For MySQL (Production/AWS Lambda)

1. Install MySQL locally or use a cloud MySQL service
2. Create a database called `jukebox_db`
3. Set the DATABASE_URL environment variable:

```bash
export DATABASE_URL="mysql+pymysql://username:password@localhost/jukebox_db"
```

Replace:
- `username` with your MySQL username
- `password` with your MySQL password  
- `localhost` with your MySQL server host (e.g., RDS endpoint for AWS)

## Database Setup Commands

After setting the DATABASE_URL, run:

```bash
# Install dependencies
uv install

# Initialize database tables
uv run python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Or start the app (it will create tables automatically)
uv run python app.py
```

## Environment Variables for AWS Lambda

For AWS Lambda deployment, set these environment variables:
- `DATABASE_URL`: Your RDS MySQL connection string
- `SECRET_KEY`: A secure secret key for Flask sessions

## Sample Data

You can add sample records through the web interface at `/database/add` or programmatically:

```python
from app import app, db
from models import JukeboxRecord, JukeboxStatus

with app.app_context():
    # Create sample records
    records = [
        JukeboxRecord(
            track_a_side="Hey Jude",
            track_b_side="Revolution", 
            artist_a_side="The Beatles",
            artist_b_side="The Beatles",
            status=JukeboxStatus.IN_JUKEBOX,
            jukebox_id="001"
        ),
        # Add more records...
    ]
    
    for record in records:
        db.session.add(record)
    
    db.session.commit()
```