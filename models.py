"""
AL MUBARACK Service - Modèles de base de données
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Admin(db.Model, UserMixin):
    """Un seul compte admin pour gérer la boutique (Oustage)."""
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    doit_changer_mdp = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self):
        return True


class Produit(db.Model):
    __tablename__ = "produits"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    categorie = db.Column(db.String(30), nullable=False)
    badge = db.Column(db.String(50), default="Disponible")
    details = db.Column(db.Text)  # une ligne de specs par ligne de texte
    date_ajout = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship(
        "ProduitImage", backref="produit", order_by="ProduitImage.ordre",
        cascade="all, delete-orphan"
    )

    @property
    def liste_details(self):
        if not self.details:
            return []
        return [ligne.strip() for ligne in self.details.split("\n") if ligne.strip()]

    @property
    def liste_images(self):
        return [img.chemin for img in self.images]


class ProduitImage(db.Model):
    __tablename__ = "produit_images"

    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, db.ForeignKey("produits.id"), nullable=False)
    chemin = db.Column(db.String(300), nullable=False)
    ordre = db.Column(db.Integer, default=0)
