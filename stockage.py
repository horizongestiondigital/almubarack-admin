"""
AL MUBARACK Service - Stockage des photos produits
Utilise Supabase Storage si configuré (nécessaire en ligne, pour que les photos
ne disparaissent jamais). Sinon, retombe sur le disque local (pratique seulement
pour tester en local, PAS utilisable une fois en ligne sur Render).
"""
import os
import uuid

import requests
from flask import current_app
from werkzeug.utils import secure_filename

EXTENSIONS_AUTORISEES = {"png", "jpg", "jpeg", "webp"}


def extension_valide(nom_fichier):
    return "." in nom_fichier and nom_fichier.rsplit(".", 1)[1].lower() in EXTENSIONS_AUTORISEES


def _supabase_configure():
    return bool(current_app.config.get("SUPABASE_URL") and current_app.config.get("SUPABASE_SERVICE_KEY"))


def televerser_image(fichier):
    """Sauvegarde une image (upload Flask) et renvoie le chemin/URL à stocker en base.
    - Si Supabase est configuré : renvoie une URL publique complète (https://...)
    - Sinon : renvoie un chemin relatif local (uploads/...)"""
    nom_securise = secure_filename(fichier.filename)
    extension = nom_securise.rsplit(".", 1)[1].lower()
    nom_fichier = f"produit_{uuid.uuid4().hex[:10]}.{extension}"

    if _supabase_configure():
        url_supabase = current_app.config["SUPABASE_URL"].rstrip("/")
        bucket = current_app.config["SUPABASE_BUCKET"]
        cle = current_app.config["SUPABASE_SERVICE_KEY"]

        contenu = fichier.read()
        type_mime = {
            "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp",
        }.get(extension, "application/octet-stream")

        reponse = requests.post(
            f"{url_supabase}/storage/v1/object/{bucket}/{nom_fichier}",
            headers={"Authorization": f"Bearer {cle}", "Content-Type": type_mime},
            data=contenu,
            timeout=20,
        )
        reponse.raise_for_status()

        return f"{url_supabase}/storage/v1/object/public/{bucket}/{nom_fichier}"

    else:
        dossier = os.path.join(current_app.static_folder, "uploads")
        os.makedirs(dossier, exist_ok=True)
        fichier.save(os.path.join(dossier, nom_fichier))
        return f"uploads/{nom_fichier}"


def televerser_bytes(contenu, nom_fichier_original):
    """Comme televerser_image, mais pour du contenu déjà en mémoire (utilisé par le script d'import)."""
    extension = nom_fichier_original.rsplit(".", 1)[1].lower()
    nom_fichier = f"produit_{uuid.uuid4().hex[:10]}.{extension}"

    if _supabase_configure():
        url_supabase = current_app.config["SUPABASE_URL"].rstrip("/")
        bucket = current_app.config["SUPABASE_BUCKET"]
        cle = current_app.config["SUPABASE_SERVICE_KEY"]

        type_mime = {
            "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp",
        }.get(extension, "application/octet-stream")

        reponse = requests.post(
            f"{url_supabase}/storage/v1/object/{bucket}/{nom_fichier}",
            headers={"Authorization": f"Bearer {cle}", "Content-Type": type_mime},
            data=contenu,
            timeout=20,
        )
        reponse.raise_for_status()

        return f"{url_supabase}/storage/v1/object/public/{bucket}/{nom_fichier}"

    else:
        dossier = os.path.join(current_app.static_folder, "uploads")
        os.makedirs(dossier, exist_ok=True)
        with open(os.path.join(dossier, nom_fichier), "wb") as f:
            f.write(contenu)
        return f"uploads/{nom_fichier}"


def supprimer_image(chemin):
    """Supprime une image du stockage (Supabase ou local selon le format du chemin)."""
    if chemin.startswith("http"):
        if not _supabase_configure():
            return  # rien à faire, cette image ne vient pas de ce stockage
        url_supabase = current_app.config["SUPABASE_URL"].rstrip("/")
        bucket = current_app.config["SUPABASE_BUCKET"]
        cle = current_app.config["SUPABASE_SERVICE_KEY"]
        nom_fichier = chemin.rsplit("/", 1)[-1]
        try:
            requests.delete(
                f"{url_supabase}/storage/v1/object/{bucket}/{nom_fichier}",
                headers={"Authorization": f"Bearer {cle}"},
                timeout=10,
            )
        except requests.exceptions.RequestException:
            pass  # la suppression de la fiche produit ne doit jamais échouer à cause de ça
    else:
        chemin_local = os.path.join(current_app.static_folder, chemin.replace("uploads/", "uploads/", 1))
        if os.path.exists(chemin_local):
            os.remove(chemin_local)


def url_affichage(chemin):
    """Renvoie l'URL à utiliser dans un <img src=...> : directe si Supabase (déjà une URL complète),
    sinon construite via /static/... pour le stockage local."""
    if chemin.startswith("http"):
        return chemin
    from flask import url_for
    return url_for("static", filename=chemin)
