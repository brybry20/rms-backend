import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database - PostgreSQL for production
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    
    # App
    SECRET_KEY = os.getenv('SECRET_KEY', 'rma-secret-key-2024')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
    
    @classmethod
    def validate(cls):
        required = ['DATABASE_URL', 'CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET']
        missing = [var for var in required if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing env vars: {', '.join(missing)}")
        return True