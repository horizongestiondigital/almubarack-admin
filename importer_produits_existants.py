"""
AL MUBARACK Service - Import unique des produits déjà créés sur le site statique
Lit directement produits_export.json (généré à partir du vrai produits.js, sans
retranscription manuelle -> zéro risque d'erreur), copie les photos, crée les fiches.

Usage : python importer_produits_existants.py
(à lancer UNE SEULE FOIS, juste après avoir installé le nouveau panneau admin)
"""
import os
import json

from app import create_app
from models import db, Produit, ProduitImage
from stockage import televerser_bytes

CHEMIN_JSON = os.path.join(os.path.dirname(__file__), "produits_export.json")
DOSSIER_SOURCE = os.path.join(os.path.dirname(__file__), "images_a_importer")

app = create_app()

with app.app_context():
    if not os.path.exists(CHEMIN_JSON):
        print(f"Fichier introuvable : {CHEMIN_JSON}")
        exit()

    with open(CHEMIN_JSON, "r", encoding="utf-8") as f:
        produits_a_importer = json.load(f)

    if Produit.query.first():
        reponse = input("Des produits existent déjà dans la base. Importer quand même ? (o/n) : ")
        if reponse.lower() != "o":
            print("Import annulé.")
            exit()

    nb_importes = 0
    nb_images_manquantes = 0

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
            source = os.path.join(DOSSIER_SOURCE, nom_fichier)

            if not os.path.exists(source):
                print(f"  ATTENTION : image introuvable pour '{p['nom']}' -> {nom_fichier}")
                nb_images_manquantes += 1
                continue

            with open(source, "rb") as f_img:
                contenu = f_img.read()
            chemin_stocke = televerser_bytes(contenu, nom_fichier)
            db.session.add(ProduitImage(produit_id=produit.id, chemin=chemin_stocke, ordre=i))

        nb_importes += 1
        print(f"  Importé : {p['nom']}")

    db.session.commit()
    print(f"\n{nb_importes} produits importés avec succès.")
    if nb_images_manquantes:
        print(f"({nb_images_manquantes} image(s) introuvable(s), voir avertissements ci-dessus)")
    print("Tu peux maintenant lancer 'python app.py' et te connecter pour les voir/modifier.")
