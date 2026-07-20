"""
AL MUBARACK Service - Initialisation
Crée le compte admin (Oustage) pour pouvoir se connecter.
Usage : python init_db.py
"""
from app import create_app
from models import db, Admin

app = create_app()

with app.app_context():
    db.create_all()

    if Admin.query.first():
        print("Un compte admin existe déjà. Rien à faire.")
    else:
        admin = Admin(username="oustage")
        admin.set_password("almubarack2026")
        db.session.add(admin)
        db.session.commit()

        print("Compte admin créé avec succès.")
        print("Connexion -> identifiant: oustage / mot de passe: almubarack2026")
        print("(à changer dès la première connexion, dans 'Mon compte')")
