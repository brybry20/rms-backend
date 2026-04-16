import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database - Auto-detect kung production or local
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Kung walang DATABASE_URL, gumamit ng SQLite (local development)
    if not DATABASE_URL:
        # SQLite for local development
        DATABASE_PATH = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'rma.db'))
        USE_POSTGRES = False
    else:
        # PostgreSQL for production (Render)
        USE_POSTGRES = True
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    
    # App
    SECRET_KEY = os.getenv('SECRET_KEY', 'rma-secret-key-2024')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'  # Default to True for local
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
    
    @classmethod
    def validate(cls):
        """Check if all required environment variables are set"""
        # Only validate Cloudinary for now (required for both local and production)
        required = [
            ('CLOUDINARY_CLOUD_NAME', cls.CLOUDINARY_CLOUD_NAME),
            ('CLOUDINARY_API_KEY', cls.CLOUDINARY_API_KEY),
            ('CLOUDINARY_API_SECRET', cls.CLOUDINARY_API_SECRET)
        ]
        
        missing = [name for name, value in required if not value]
        
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
        
        # For production, also validate DATABASE_URL
        if cls.DATABASE_URL and not cls.DATABASE_URL.startswith('sqlite'):
            # This is production (PostgreSQL)
            if not cls.DATABASE_URL:
                raise ValueError("DATABASE_URL is required for production deployment")
        
        return True