"""
AL MUBARACK Service - Configuration
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)


class Config:
    # En ligne (Render) : DATABASE_URL pointe vers Supabase (PostgreSQL).
    # En local (pour tester avant de déployer) : SQLite.
    _database_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(INSTANCE_DIR, "boutique.db"))
    if _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("ALMUBARACK_SECRET_KEY", "cle-a-changer-en-production")
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 Mo par upload

    # Stockage des photos : Supabase Storage si configuré (obligatoire en ligne,
    # sinon les photos uploadées disparaîtraient à chaque redémarrage du serveur).
    # Vide -> l'app retombe sur un stockage local (pratique seulement pour tester en local).
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
    SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", "produits")

    NUMERO_WHATSAPP = "224625476147"
    NOM_BOUTIQUE = "AL MUBARACK SERVICE"
    NB_NOUVEAUTES = 4

    CATEGORIES = [
        ("telephones", "📱 Téléphones"),
        ("accessoires", "🔌 Accessoires"),
        ("solaire", "☀️ Énergie solaire"),
        ("electromenager", "🍳 Électroménager"),
        ("tablettes", "📟 Tablettes enfants"),
        ("climatiseurs", "❄️ Climatiseurs"),
    ]
