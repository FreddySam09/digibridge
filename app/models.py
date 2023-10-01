from flask_login import UserMixin
from app import db
from app import app

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    last_booking_date = db.Column(db.Date)
    user_type = db.Column(db.String(10), default='user')

class Doubt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    replies = db.relationship('Reply', backref='doubt', lazy=True)

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    doubt_id = db.Column(db.Integer, db.ForeignKey('doubt.id'), nullable=False)

class ComputerBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    computer = db.Column(db.String(120), nullable=False)
    slot = db.Column(db.String(120), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    booked_by = db.Column(db.String(120))

    user = db.relationship('User', backref='bookings')

class Staff(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    user_type = db.Column(db.String(10), default='staff')
    courses = db.relationship('Course', back_populates='staff')
    profile_picture = db.Column(db.String(255))

class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    query_text = db.Column(db.String(500), nullable=False)
    response_text = db.Column(db.String(500))

    user = db.relationship('User', backref='queries')
    staff = db.relationship('Staff', backref='queries')

#haha

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
import os

class Course(db.Model):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=False)
    thumbnail_filename = Column(String(255), nullable=False)  # Store file name only
    video_filename = Column(String(255), nullable=False)  # Store file name only
    subject = Column(String(100), nullable=False)  # Add subject field
    staff_id = Column(Integer, ForeignKey('staff.id'), nullable=False)
    staff = db.relationship('Staff', back_populates='courses')

    @property
    def thumbnail_path(self):
        """Generate the full path to the thumbnail image."""
        return os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', self.thumbnail_filename)

    @property
    def video_path(self):
        """Generate the full path to the course video."""
        return os.path.join(app.config['UPLOAD_FOLDER'], 'videos', self.video_filename)
    