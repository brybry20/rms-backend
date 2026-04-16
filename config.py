import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # SQLite Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'rma.db'))
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    
    # Cloudinary Configuration (from .env)
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    
    # App
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-this')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # CORS
    CORS_ORIGINS = ['http://localhost:5173', 'http://localhost:3000']
    
    # Validate required configs
    @classmethod
    def validate(cls):
        """Check if all required environment variables are set"""
        required = [
            ('CLOUDINARY_CLOUD_NAME', cls.CLOUDINARY_CLOUD_NAME),
            ('CLOUDINARY_API_KEY', cls.CLOUDINARY_API_KEY),
            ('CLOUDINARY_API_SECRET', cls.CLOUDINARY_API_SECRET)
        ]
        
        missing = [name for name, value in required if not value]
        
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
        
        return True