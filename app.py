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

# Initialize Cloudinary
cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET
)

CORS(app, origins=Config.CORS_ORIGINS)

init_db()

register_routes(app)
register_admin_routes(app)
register_dealer_routes(app)
register_authorizer_routes(app)
register_approver_routes(app)

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], port=app.config['PORT'])