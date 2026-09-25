from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Crop, UserCrop

crops_bp = Blueprint("crops", __name__)

@crops_bp.route("/")
def list_crops():
    crops = db.session.scalars(db.select(Crop).order_by(Crop.id)).all()
    return render_template("crops.html", crops=crops)

@crops_bp.route("/<int:crop_id>")
def detail(crop_id):
    crop = db.get_or_404(Crop, crop_id)
    saved = False
    if current_user.is_authenticated:
        saved = db.session.scalar(
            db.select(UserCrop).where(
                UserCrop.user_id == current_user.id,
                UserCrop.crop_id == crop.id
            )
        ) is not None
    return render_template("crop_detail.html", crop=crop, saved=saved)

@crops_bp.route("/<int:crop_id>/save", methods=["POST"])
@login_required
def save(crop_id):
    crop = db.get_or_404(Crop, crop_id)
    existing = db.session.scalar(
        db.select(UserCrop).where(
            UserCrop.user_id == current_user.id,
            UserCrop.crop_id == crop.id
        )
    )
    if not existing:
        uc = UserCrop(
            user_id=current_user.id,
            crop_id=crop.id,
            start_date=date.today(),
            current_stage="Planning"
        )
        db.session.add(uc)
        db.session.commit()
        flash(f"{crop.name} was added to your crops.", "success")
    else:
        flash(f"{crop.name} is already in your crops.", "info")
    return redirect(url_for("crops.detail", crop_id=crop.id))

@crops_bp.route("/<int:crop_id>/remove", methods=["POST"])
@login_required
def remove(crop_id):
    uc = db.session.scalar(
        db.select(UserCrop).where(
            UserCrop.user_id == current_user.id,
            UserCrop.crop_id == crop_id
        )
    )
    if uc:
        db.session.delete(uc)
        db.session.commit()
        flash("Crop removed from your saved crops.", "success")
    return redirect(url_for("dashboard.index"))

@crops_bp.route("/mine")
@login_required
def mine():
    return render_template("my_crops.html", user_crops=current_user.crops)
