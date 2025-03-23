from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import relationship, DeclarativeBase
from src.backend.models.emotions import star_emotions_association
from sqlalchemy import DateTime

class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models (with async support)."""
    pass

class Star(Base):
    """Database model for storing filtered star data."""
    __tablename__ = "filtered_stars"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    spectral_type = Column(String)
    magnitude = Column(Float)
    color = Column(String)
    temperature = Column(Integer)
    distance = Column(Float)
    mythology = Column(String, nullable=True)  # Stores mythology description
    last_mythology_update = Column(DateTime, nullable=True)

    # Many-to-many relationship with emotions
    emotions = relationship("Emotions", secondary=star_emotions_association, back_populates="stars")

