"""
AL MUBARACK Service - Catalogue public
"""
import json

from flask import Blueprint, render_template

from models import Produit
from config import Config
from stockage import url_affichage

catalogue_bp = Blueprint("catalogue", __name__)


@catalogue_bp.route("/")
def public():
    produits = Produit.query.order_by(Produit.date_ajout.asc()).all()

    produits_json = json.dumps([
        {
            "nom": p.nom,
            "categorie": p.categorie,
            "badge": p.badge,
            "images": [url_affichage(img) for img in p.liste_images],
            "details": p.liste_details,
        }
        for p in produits
    ], ensure_ascii=False)

    return render_template(
        "catalogue.html",
        produits_json=produits_json,
        numero_whatsapp=Config.NUMERO_WHATSAPP,
        nom_boutique=Config.NOM_BOUTIQUE,
        nb_nouveautes=Config.NB_NOUVEAUTES,
        categories=Config.CATEGORIES,
    )
