import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MongoDB Configuration
    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'rma_system')
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    
    # App
    SECRET_KEY = os.getenv('SECRET_KEY', 'rma-secret-key-2024')
    PORT = int(os.getenv('PORT', 10000))  # Change default to 10000
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
    
    # Environment detection
    IS_RENDER = os.getenv('RENDER', 'False').lower() == 'true'
    
    @classmethod
    def validate(cls):
        if not cls.MONGO_URI:
            raise ValueError("MONGO_URI is required! Please check your .env file")
        if not cls.CLOUDINARY_CLOUD_NAME:
            raise ValueError("Cloudinary credentials are required")
        return True