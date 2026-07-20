"""
AL MUBARACK Service - Authentification admin
"""
import re
from functools import wraps
from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user

from models import db, Admin

auth_bp = Blueprint("auth", __name__)

MAX_TENTATIVES = 5


@auth_bp.route("/admin/initialiser-compte")
def initialiser_compte():
    if Admin.query.first():
        return "Un compte admin existe deja. Va sur /admin/connexion pour te connecter.", 200

    cle = request.args.get("cle", "")
    if cle != current_app.config["SECRET_KEY"]:
        return "Non autorise (cle manquante ou incorrecte).", 403

    admin = Admin(username="oustage")
    admin.set_password("almubarack2026")
    admin.doit_changer_mdp = True
    db.session.add(admin)
    db.session.commit()

    return (
        "Compte admin cree avec succes.<br>"
        "Identifiant : <b>oustage</b> - Mot de passe : <b>almubarack2026</b><br>"
        "Connecte-toi maintenant sur /admin/connexion, puis change ce mot de passe dans 'Mon compte'."
    ), 200


def mot_de_passe_est_fort(mot_de_passe):
    if len(mot_de_passe) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caracteres."
    if not re.search(r"[A-Za-z]", mot_de_passe):
        return False, "Le mot de passe doit contenir au moins une lettre."
    if not re.search(r"[0-9]", mot_de_passe):
        return False, "Le mot de passe doit contenir au moins un chiffre."
    return True, ""


@auth_bp.route("/admin/connexion", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("produits_admin.liste"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            login_user(admin)
            flash(f"Bienvenue !", "success")
            return redirect(url_for("produits_admin.liste"))

        flash("Identifiant ou mot de passe incorrect.", "danger")

    return render_template("login.html")


@auth_bp.route("/admin/deconnexion")
@login_required
def logout():
    logout_user()
    flash("Vous avez ete deconnecte.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/admin/mon-compte", methods=["GET", "POST"])
@login_required
def mon_compte():
    if request.method == "POST":
        ancien = request.form.get("ancien_mdp", "")
        nouveau = request.form.get("nouveau_mdp", "")
        confirmation = request.form.get("confirmation_mdp", "")

        if not current_user.check_password(ancien):
            flash("Mot de passe actuel incorrect.", "danger")
            return redirect(url_for("auth.mon_compte"))

        if nouveau != confirmation:
            flash("La confirmation ne correspond pas.", "danger")
            return redirect(url_for("auth.mon_compte"))

        est_fort, message = mot_de_passe_est_fort(nouveau)
        if not est_fort:
            flash(message, "danger")
            return redirect(url_for("auth.mon_compte"))

        current_user.set_password(nouveau)
        current_user.doit_changer_mdp = False
        db.session.commit()
        flash("Mot de passe modifie avec succes.", "success")
        return redirect(url_for("produits_admin.liste"))

    return render_template("mon_compte.html")
