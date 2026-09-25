from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location_name = db.Column(db.String(255))
    state = db.Column(db.String(80))
    preferred_language = db.Column(db.String(2), nullable=False, default="en", server_default="en")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    crops = db.relationship("UserCrop", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Crop(db.Model):
    __tablename__ = "crops"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    scientific_name = db.Column(db.String(160))
    emoji = db.Column(db.String(10))
    description = db.Column(db.Text)
    soil = db.Column(db.Text)
    climate = db.Column(db.Text)
    sowing_period = db.Column(db.String(255))
    harvest_period = db.Column(db.String(255))

    steps = db.relationship("CultivationStep", back_populates="crop",
                            cascade="all, delete-orphan", order_by="CultivationStep.sequence")
    irrigations = db.relationship("Irrigation", back_populates="crop",
                                  cascade="all, delete-orphan")
    advices = db.relationship("CropAdvice", back_populates="crop",
                              cascade="all, delete-orphan")
    users = db.relationship("UserCrop", back_populates="crop", cascade="all, delete-orphan")

class CultivationStep(db.Model):
    __tablename__ = "cultivation_steps"
    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey("crops.id"), nullable=False)
    stage = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    duration_days = db.Column(db.Integer)
    sequence = db.Column(db.Integer, nullable=False)

    crop = db.relationship("Crop", back_populates="steps")

class Irrigation(db.Model):
    __tablename__ = "irrigation"
    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey("crops.id"), nullable=False)
    growth_stage = db.Column(db.String(120), nullable=False)
    frequency = db.Column(db.String(180))
    water_requirement = db.Column(db.String(255))
    description = db.Column(db.Text)

    crop = db.relationship("Crop", back_populates="irrigations")

class CropAdvice(db.Model):
    __tablename__ = "crop_advice"
    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey("crops.id"), nullable=False)
    condition = db.Column(db.String(100), nullable=False)
    advice = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(30), default="info")

    crop = db.relationship("Crop", back_populates="advices")

class UserCrop(db.Model):
    __tablename__ = "user_crops"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    crop_id = db.Column(db.Integer, db.ForeignKey("crops.id"), nullable=False)
    start_date = db.Column(db.Date)
    current_stage = db.Column(db.String(120), default="Planning")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="crops")
    crop = db.relationship("Crop", back_populates="users")

    __table_args__ = (
        db.UniqueConstraint("user_id", "crop_id", name="uq_user_crop"),
    )

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
