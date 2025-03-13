import uvicorn
import logging
from app.main import app
from app.db.init_db import init_db

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Initialize the database
    logger.info("Initializing database...")
    init_db()
    
    # Run the application
    logger.info("Starting FastAPI application...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 