from sqlalchemy import Column, Integer, String, Text, Float, TIMESTAMP
from sqlalchemy.sql import func
from extensions import db

class RawGoogleMap(db.Model):
    """New clean table for Google Map data from GDrive ingestion."""
    __tablename__ = "raw_google_map"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(Text)
    address = Column(Text)
    website = Column(Text)
    phone_number = Column(String(255))
    reviews_count = Column(Integer)
    reviews_average = Column(Float)
    category = Column(String(255))
    subcategory = Column(Text)
    city = Column(String(255))
    state = Column(String(255))
    
    # Source Metadata (from folder structure)
    source_city = Column(String(255), index=True)
    source_category = Column(String(255), index=True)
    drive_file_id = Column(String(255))
    drive_modified_at = Column(TIMESTAMP)
    drive_path = Column(Text)
    
    ingested_at = Column(TIMESTAMP, server_default=func.now())
