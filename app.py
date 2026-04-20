from flask import Flask
from flask_cors import CORS
from config import Config
from database.db import init_db
from routes.auth import register_routes
from routes.admin import register_admin_routes
from routes.dealer import register_dealer_routes
from routes.authorizer import register_authorizer_routes
from routes.approver import register_approver_routes
import cloudinary
import cloudinary.uploader
import os

app = Flask(__name__)
app.config.from_object(Config)

# Validate configuration before starting
try:
    Config.validate()
    print("✅ Configuration validated successfully!")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    print("Please check your .env file")
    exit(1)

# Initialize Cloudinary
cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET
)
print("✅ Cloudinary configured!")

# CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": Config.CORS_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize database
init_db()
print("✅ Database initialized!")

# Register all routes
register_routes(app)
register_admin_routes(app)
register_dealer_routes(app)
register_authorizer_routes(app)
register_approver_routes(app)
print("✅ All routes registered!")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])