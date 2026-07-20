"""
AL MUBARACK Service - Gestion des produits (admin)
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash

from flask_login import login_required

from models import db, Produit, ProduitImage
from config import Config
from stockage import extension_valide as _extension_valide, televerser_image as _sauvegarder_image, supprimer_image as _supprimer_fichier_stockage

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
            flash("Le nom et la catégorie sont obligatoires.", "danger")
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
                flash(f"Format non autorisé pour {f.filename} (PNG, JPG ou WEBP seulement).", "danger")
                return render_template("admin/form.html", produit=None, categories=Config.CATEGORIES)

        produit = Produit(nom=nom, categorie=categorie, badge=badge, details=details)
        db.session.add(produit)
        db.session.flush()

        for i, f in enumerate(fichiers_valides):
            chemin = _sauvegarder_image(f)
            db.session.add(ProduitImage(produit_id=produit.id, chemin=chemin, ordre=i))

        db.session.commit()
        flash(f"Produit « {nom} » ajouté avec succès.", "success")
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
            flash("Le nom et la catégorie sont obligatoires.", "danger")
            return render_template("admin/form.html", produit=produit, categories=Config.CATEGORIES)

        # Nouvelles photos (optionnelles) : s'ajoutent à celles déjà présentes, dans la limite de 3
        fichiers = request.files.getlist("images")
        fichiers_valides = [f for f in fichiers if f and f.filename]

        if len(produit.images) + len(fichiers_valides) > 3:
            flash("Maximum 3 photos par produit. Supprime une ancienne photo avant d'en ajouter une nouvelle.", "danger")
            return render_template("admin/form.html", produit=produit, categories=Config.CATEGORIES)

        for f in fichiers_valides:
            if not _extension_valide(f.filename):
                flash(f"Format non autorisé pour {f.filename}.", "danger")
                return render_template("admin/form.html", produit=produit, categories=Config.CATEGORIES)

        ordre_depart = len(produit.images)
        for i, f in enumerate(fichiers_valides):
            chemin = _sauvegarder_image(f)
            db.session.add(ProduitImage(produit_id=produit.id, chemin=chemin, ordre=ordre_depart + i))

        db.session.commit()
        flash(f"Produit « {produit.nom} » mis à jour.", "success")
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
    flash(f"Produit « {nom} » supprimé.", "info")
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
    flash("Photo supprimée.", "info")
    return redirect(url_for("produits_admin.modifier", produit_id=produit_id))
