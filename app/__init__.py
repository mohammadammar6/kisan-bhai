from flask import Flask, request, session, g
from flask_login import current_user
from config import Config
from .extensions import db, login_manager, csrf, init_redis

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    init_redis(app)

    @app.before_request
    def load_language():
        g.language = (current_user.preferred_language if current_user.is_authenticated
                      else session.get("language", "en"))

    @app.context_processor
    def inject_language():
        return {"language": getattr(g, "language", "en")}

    @app.after_request
    def translate_page(response):
        if g.get("language") == "hi" and response.mimetype == "text/html":
            from .translations import HI
            page = response.get_data(as_text=True)
            for english, hindi in sorted(HI.items(), key=lambda item: len(item[0]), reverse=True):
                page = page.replace(english, hindi)
            response.set_data(page)
        return response

    from .auth.routes import auth_bp
    from .dashboard.routes import dashboard_bp
    from .crops.routes import crops_bp
    from .weather.routes import weather_bp
    from .health import health_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(crops_bp, url_prefix='/crops')
    app.register_blueprint(weather_bp, url_prefix='/api')
    app.register_blueprint(health_bp)

    with app.app_context():
        db.create_all()
        # create_all does not add columns to existing installations.
        from sqlalchemy import inspect, text
        if "preferred_language" not in {column["name"] for column in inspect(db.engine).get_columns("users")}:
            with db.engine.begin() as connection:
                connection.execute(text("ALTER TABLE users ADD COLUMN preferred_language VARCHAR(2) NOT NULL DEFAULT 'en'"))
        if "state" not in {column["name"] for column in inspect(db.engine).get_columns("users")}:
            with db.engine.begin() as connection:
                connection.execute(text("ALTER TABLE users ADD COLUMN state VARCHAR(80)"))
    return app
