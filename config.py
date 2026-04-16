import os

class Config:
    # SQLite Database
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'rma.db')
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME = 'djlthe2df'
    CLOUDINARY_API_KEY = '543835262257818'
    CLOUDINARY_API_SECRET = 'CSIlELP-PRQfWZiMk9wq3izKlTk'
    
    # App
    SECRET_KEY = 'rma-secret-key-2024'
    PORT = 5000
    DEBUG = True
    
    # CORS
    CORS_ORIGINS = ['http://localhost:5173', 'http://localhost:3000']