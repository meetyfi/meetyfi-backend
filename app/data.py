from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create the database engine with updated connection pool parameters
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,        # Increase from default 5
    max_overflow=20,     # Increase from default 10
    pool_timeout=60,     # Increase timeout if needed
    pool_recycle=3600    # Recycle connections after 1 hour
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Function to create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Function to get a database session
def get_db_session():
    db = SessionLocal()  # Create a new session
    try:
        return db  # Return the session object
    finally:
        db.close()  # Close the session after use