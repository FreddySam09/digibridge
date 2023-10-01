from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'icsct23'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SESSION_COOKIE_SECURE'] = False


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)

import os
from werkzeug.utils import secure_filename

# Define a folder where uploaded thumbnails and videos will be stored
UPLOAD_FOLDER = 'uploads'
THUMBNAIL_FOLDER = os.path.join(UPLOAD_FOLDER, 'thumbnails')
VIDEO_FOLDER = os.path.join(UPLOAD_FOLDER, 'videos')

# Ensure the upload folders exist
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)

# Function to save a thumbnail image
def save_thumbnail(thumbnail_file):
    if thumbnail_file:
        # Generate a secure filename
        filename = secure_filename(thumbnail_file.filename)
        # Save the thumbnail to the thumbnails folder
        thumbnail_path = os.path.join(THUMBNAIL_FOLDER, filename)
        thumbnail_file.save(thumbnail_path)
        return thumbnail_path
    return None

# Function to save a video
def save_video(video_file):
    if video_file:
        # Generate a secure filename
        filename = secure_filename(video_file.filename)
        # Save the video to the videos folder
        video_path = os.path.join(VIDEO_FOLDER, filename)
        video_file.save(video_path)
        return video_path
    return None

app.config['UPLOAD_FOLDER'] = 'uploads'

from app import routes, models, forms
