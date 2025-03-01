from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create the database engine using the DATABASE_URL from the settings
engine = create_engine(settings.DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Function to create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Function to get a database session
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()