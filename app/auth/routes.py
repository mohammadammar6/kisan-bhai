from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user
from sqlalchemy import func
from .forms import RegistrationForm, LoginForm
from ..extensions import db
from ..models import User
from ..state_data import STATES

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        if db.session.scalar(db.select(User).where(func.lower(User.email) == form.email.data.lower())):
            flash("An account with that email already exists.", "danger")
            return render_template("register.html", form=form)
        language = request.form.get("language", session.get("language", "en"))
        user = User(name=form.name.data.strip(), email=form.email.data.lower().strip(),
                    preferred_language=language if language in {"en", "hi"} else "en",
                    state=session.get("farmer_state") if session.get("farmer_state") in STATES else None)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        session["language"] = user.preferred_language
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).where(func.lower(User.email) == form.email.data.lower()))
        if user and user.check_password(form.password.data):
            if not user.state and session.get("farmer_state") in STATES:
                user.state = session["farmer_state"]
                db.session.commit()
            login_user(user, remember=form.remember.data)
            return redirect(request.args.get("next") or url_for("dashboard.index"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html", form=form)

@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))

@auth_bp.route("/language", methods=["POST"])
def set_language():
    language = request.form.get("language", "en")
    if language not in {"en", "hi"}:
        language = "en"
    if current_user.is_authenticated:
        current_user.preferred_language = language
        db.session.commit()
    else:
        session["language"] = language
    return redirect(request.referrer or url_for("dashboard.home"))
