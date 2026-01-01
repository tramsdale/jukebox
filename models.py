"""
Database models for jukebox inventory management.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional
import enum

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class JukeboxStatus(enum.Enum):
    """Enum for jukebox record status."""
    IN_JUKEBOX = "In Jukebox"
    NEW = "New"
    IN_STORAGE = "In Storage"
    WISHLIST = "Wishlist"

class JukeboxRecord(db.Model):
    """Model for jukebox inventory records."""
    __tablename__ = 'jukebox_records'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    track_a_side: Mapped[str] = mapped_column(String(200), nullable=False)
    track_b_side: Mapped[str] = mapped_column(String(200), nullable=False)
    artist_a_side: Mapped[str] = mapped_column(String(200), nullable=False)
    artist_b_side: Mapped[str] = mapped_column(String(200), nullable=False)
    genre: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[JukeboxStatus] = mapped_column(Enum(JukeboxStatus), nullable=False)
    jukebox_id: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    
    def __init__(self, **kwargs):
        if 'status' not in kwargs:
            kwargs['status'] = JukeboxStatus.NEW
        super().__init__(**kwargs)
    
    def __repr__(self) -> str:
        return f'<JukeboxRecord {self.artist_a_side} - {self.track_a_side}>'
    
    def to_dict(self) -> dict:
        """Convert record to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'track_a_side': self.track_a_side,
            'track_b_side': self.track_b_side,
            'artist_a_side': self.artist_a_side,
            'artist_b_side': self.artist_b_side,
            'genre': self.genre,
            'status': self.status.value,
            'jukebox_id': self.jukebox_id
        }
    
    def to_jukebox_label(self, use_a_side: bool = True):
        """Convert to JukeBoxLabel for PDF generation."""
        from jukebox_generator import JukeBoxLabel
        
        if use_a_side:
            return JukeBoxLabel(
                artist=self.artist_a_side,
                a_side=self.track_a_side,
                b_side=self.track_b_side,
                genre=self.genre or "Various",
                artist_a=self.artist_a_side,
                artist_b=self.artist_b_side
            )
        else:
            return JukeBoxLabel(
                artist=self.artist_b_side,
                a_side=self.track_b_side,
                b_side=self.track_a_side,
                genre=self.genre or "Various",
                artist_a=self.artist_b_side,
                artist_b=self.artist_a_side
            )