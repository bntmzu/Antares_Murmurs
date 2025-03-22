from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import relationship, DeclarativeBase

class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models (with async support)."""
    pass

# Associative table "Star-Emotion" (many to many)
star_emotions_association = Table(
    "star_emotions_association", Base.metadata,
    Column("star_id", Integer, ForeignKey("filtered_stars.id")),
    Column("emotion_id", Integer, ForeignKey("star_emotions.id"))
)

class Emotion(Base):
    """Database model for storing star-related emotions."""
    __tablename__: str = "star_emotions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    # Many-to-many relationship with stars
    stars = relationship("Star", secondary=star_emotions_association, back_populates="emotions")
