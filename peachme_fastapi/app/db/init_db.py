from app.db.database import Base, engine
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database by creating all tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise e

if __name__ == "__main__":
    logger.info("Creating database tables...")
    init_db()
    logger.info("Database initialization completed") 