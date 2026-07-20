"""
AL MUBARACK Service - Authentification admin
"""
import re
from functools import wraps
from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from models import db, Admin

auth_bp = Blueprint("auth", __name__)

MAX_TENTATIVES = 5


def mot_de_passe_est_fort(mot_de_passe):
    if len(mot_de_passe) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
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
    flash("Vous avez été déconnecté.", "info")
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
        flash("Mot de passe modifié avec succès.", "success")
        return redirect(url_for("produits_admin.liste"))

    return render_template("mon_compte.html")
