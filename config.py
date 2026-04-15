import os

class Config:
    DATABASE_URL = os.environ.get('DATABASE_URL')  # kukunin sa Render

    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', 'djlthe2df')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '543835262257818')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', 'CSIlELP-PRQfWZiMk9wq3izKlTk')

    SECRET_KEY = os.environ.get('SECRET_KEY', 'rma-secret-key-2024')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('FLASK_ENV') != 'production'

    # CORS origins – dapat dynamic
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')