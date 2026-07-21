"""
AL MUBARACK Service - Gestion des produits (admin)
"""
import os
import json

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

from flask_login import login_required

from models import db, Produit, ProduitImage
from config import Config
from stockage import extension_valide as _extension_valide, televerser_image as _sauvegarder_image, supprimer_image as _supprimer_fichier_stockage, televerser_bytes

produits_admin_bp = Blueprint("produits_admin", __name__, url_prefix="/admin/produits")


@produits_admin_bp.route("/")
@login_required
def liste():
    produits = Produit.query.order_by(Produit.date_ajout.desc()).all()
    return render_template("admin/liste.html", produits=produits, categories=dict(Config.CATEGORIES))


@produits_admin_bp.route("/ajouter", methods=["GET", "POST"])
@login_required
def ajouter():
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        categorie = request.form.get("categorie", "")
        badge = request.form.get("badge", "").strip() or "Disponible"
        details = request.form.get("details", "").strip()

        if not nom or not categorie:
            flash("Le nom et la categorie sont obligatoires.", "danger")
            return render_template("admin/form.html", produit=None, categories=Config.CATEGORIES)

        fichiers = request.files.getlist("images")
        fichiers_valides = [f for f in fichiers if f and f.filename]

        if not fichiers_valides:
            flash("Ajoute au moins une photo.", "danger")
            return render_template("admin/form.html", produit=None, categories=Config.CATEGORIES)

        if len(fichiers_valides) > 3:
            flash("Maximum 3 photos par produit.", "danger")
            return render_template("admin/form.html", produit=None, categories=Config.CATEGORIES)

        for f in fichiers_valides:
            if not _extension_valide(f.filename):
                flash(f"Format non autorise pour {f.filename} (PNG, JPG ou WEBP seulement).", "danger")
                return render_template("admin/form.html", produit=None, categories=Config.CATEGORIES)

        produit = Produit(nom=nom, categorie=categorie, badge=badge, details=details)
        db.session.add(produit)
        db.session.flush()

        for i, f in enumerate(fichiers_valides):
            chemin = _sauvegarder_image(f)
            db.session.add(ProduitImage(produit_id=produit.id, chemin=chemin, ordre=i))

        db.session.commit()
        flash(f"Produit ajoute avec succes.", "success")
        return redirect(url_for("produits_admin.liste"))

    return render_template("admin/form.html", produit=None, categories=Config.CATEGORIES)


@produits_admin_bp.route("/<int:produit_id>/modifier", methods=["GET", "POST"])
@login_required
def modifier(produit_id):
    produit = Produit.query.get_or_404(produit_id)

    if request.method == "POST":
        produit.nom = request.form.get("nom", "").strip()
        produit.categorie = request.form.get("categorie", "")
        produit.badge = request.form.get("badge", "").strip() or "Disponible"
        produit.details = request.form.get("details", "").strip()

        if not produit.nom or not produit.categorie:
            flash("Le nom et la categorie sont obligatoires.", "danger")
            return render_template("admin/form.html", produit=produit, categories=Config.CATEGORIES)

        fichiers = request.files.getlist("images")
        fichiers_valides = [f for f in fichiers if f and f.filename]

        if len(produit.images) + len(fichiers_valides) > 3:
            flash("Maximum 3 photos par produit. Supprime une ancienne photo avant d'en ajouter une nouvelle.", "danger")
            return render_template("admin/form.html", produit=produit, categories=Config.CATEGORIES)

        for f in fichiers_valides:
            if not _extension_valide(f.filename):
                flash(f"Format non autorise pour {f.filename}.", "danger")
                return render_template("admin/form.html", produit=produit, categories=Config.CATEGORIES)

        ordre_depart = len(produit.images)
        for i, f in enumerate(fichiers_valides):
            chemin = _sauvegarder_image(f)
            db.session.add(ProduitImage(produit_id=produit.id, chemin=chemin, ordre=ordre_depart + i))

        db.session.commit()
        flash(f"Produit mis a jour.", "success")
        return redirect(url_for("produits_admin.liste"))

    return render_template("admin/form.html", produit=produit, categories=Config.CATEGORIES)


@produits_admin_bp.route("/<int:produit_id>/supprimer", methods=["POST"])
@login_required
def supprimer(produit_id):
    produit = Produit.query.get_or_404(produit_id)
    nom = produit.nom

    for img in produit.images:
        _supprimer_fichier_stockage(img.chemin)

    db.session.delete(produit)
    db.session.commit()
    flash(f"Produit supprime.", "info")
    return redirect(url_for("produits_admin.liste"))


@produits_admin_bp.route("/image/<int:image_id>/supprimer", methods=["POST"])
@login_required
def supprimer_image(image_id):
    image = ProduitImage.query.get_or_404(image_id)
    produit_id = image.produit_id

    if len(image.produit.images) <= 1:
        flash("Impossible : un produit doit garder au moins 1 photo.", "danger")
        return redirect(url_for("produits_admin.modifier", produit_id=produit_id))

    _supprimer_fichier_stockage(image.chemin)
    db.session.delete(image)
    db.session.commit()
    flash("Photo supprimee.", "info")
    return redirect(url_for("produits_admin.modifier", produit_id=produit_id))


@produits_admin_bp.route("/importer-existants")
def importer_existants():
    cle = request.args.get("cle", "")
    if cle != current_app.config["SECRET_KEY"]:
        return "Non autorise (cle manquante ou incorrecte).", 403

    if Produit.query.first():
        return "Des produits existent deja dans la base - import deja fait.", 200

    chemin_json = os.path.join(os.path.dirname(__file__), "produits_export.json")
    dossier_source = os.path.join(os.path.dirname(__file__), "images_a_importer")

    if not os.path.exists(chemin_json):
        return f"Fichier introuvable sur le serveur : {chemin_json}", 500

    with open(chemin_json, "r", encoding="utf-8") as f:
        produits_a_importer = json.load(f)

    nb_importes = 0
    nb_images_manquantes = 0
    messages = []

    for p in produits_a_importer:
        images = p.get("images") or ([p["image"]] if p.get("image") else [])

        produit = Produit(
            nom=p["nom"],
            categorie=p["categorie"],
            badge=p.get("badge", "Disponible"),
            details="\n".join(p["details"]) if p.get("details") else None,
        )
        db.session.add(produit)
        db.session.flush()

        for i, chemin_relatif in enumerate(images):
            nom_fichier = os.path.basename(chemin_relatif)
            source = os.path.join(dossier_source, nom_fichier)

            if not os.path.exists(source):
                messages.append(f"ATTENTION : image introuvable pour {p['nom']} -> {nom_fichier}")
                nb_images_manquantes += 1
                continue

            with open(source, "rb") as f_img:
                contenu = f_img.read()
            chemin_stocke = televerser_bytes(contenu, nom_fichier)
            db.session.add(ProduitImage(produit_id=produit.id, chemin=chemin_stocke, ordre=i))

        nb_importes += 1

    db.session.commit()

    reponse = f"{nb_importes} produits importes avec succes.<br>"
    if nb_images_manquantes:
        reponse += f"({nb_images_manquantes} image(s) introuvable(s))<br>" + "<br>".join(messages)
    reponse += "<br><br>Va sur /admin/produits pour les voir."
    return reponse, 200
