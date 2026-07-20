"""
AL MUBARACK Service - Application principale
"""
from flask import Flask
from flask_login import LoginManager

from config import Config
from models import db, Admin

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Veuillez vous connecter pour acceder a cette page."
login_manager.login_message_category = "warning"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from auth import auth_bp
    from produits_admin import produits_admin_bp
    from catalogue import catalogue_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(produits_admin_bp)
    app.register_blueprint(catalogue_bp)

    from stockage import url_affichage
    app.jinja_env.globals["url_affichage"] = url_affichage

    with app.app_context():
        db.create_all()

    return app


@login_manager.user_loader
def load_user(admin_id):
    return Admin.query.get(int(admin_id))


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
