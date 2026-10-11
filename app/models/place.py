from sqlalchemy import Column, String, Float, Integer, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import datetime

from app.db.base import Base

class CanonicalPlace(Base):
    """Core source of truth for physical locations."""
    __tablename__ = 'canonical_places'

    id = Column(String, primary_key=True)  
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True) 
    
    # GeoAlchemy2 automatically creates the GiST index for this column behind the scenes.
    geom = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String, nullable=True)
    cuisines = Column(JSON, nullable=True)
    source_provider = Column(String, default="osm")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationship to scoring model
    ranking = relationship("PlaceRanking", back_populates="place", uselist=False, cascade="all, delete-orphan")


class PlaceRanking(Base):
    """Holds scoring metrics for both normal rating and LLM uniqueness pipelines."""
    __tablename__ = 'place_rankings'

    place_id = Column(String, ForeignKey('canonical_places.id', ondelete="CASCADE"), primary_key=True)
    
    # Pipeline 1: General Rating Metrics
    base_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    
    # Pipeline 2: LLM Curated Uniqueness Metrics
    is_curated_seed = Column(Boolean, default=False, index=True)
    uniqueness_score = Column(Integer, default=0, index=True)  
    ideal_meal = Column(String, nullable=True)                 
    unique_summary_lines = Column(JSON, nullable=True)        
    score_reasoning = Column(String, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    place = relationship("CanonicalPlace", back_populates="ranking")