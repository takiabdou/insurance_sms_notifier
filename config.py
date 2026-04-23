# =============================================================
# config.py — Configuration Centrale & Persistance
# =============================================================
import os
import json

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
DATA_DIR        = os.path.join(BASE_DIR, "data")
LOG_DIR         = os.path.join(BASE_DIR, "logs")
IMAGES_DIR      = os.path.join(BASE_DIR, "images")
SENT_LOG_PATH   = os.path.join(DATA_DIR, "sent_log.csv")
APP_LOG_PATH    = os.path.join(LOG_DIR,  "app.log")
CONFIG_FILE     = os.path.join(BASE_DIR, "user_config.json")
# ── Configuration GitHub pour les mises à jour ───────────────
GITHUB_OWNER = "takiabdou"      #← Remplacez par votre nom GitHub
GITHUB_REPO  = "crma-sms-notifier"          #← Nom exact de votre dépôt

# ── Version de l'application ─────────────────────────────────
APP_VERSION = "1.0.0"  #← Incrémentez à chaque nouvelle version (1.0.1, 1.1.0, etc.)

# ── Valeurs par défaut ────────────────────────────────────────
DEFAULT_GATEWAY_URL      = "http://192.168.1.9:8080/message"
DEFAULT_GATEWAY_USER     = "admin"
DEFAULT_GATEWAY_PASSWORD = "lg_1HUtj"
DEFAULT_DAYS_BEFORE      = 5
DEFAULT_EXACT_MODE       = False

# ── Variables Globales ────────────────────────────────────────
GATEWAY_URL      = DEFAULT_GATEWAY_URL
GATEWAY_USER     = DEFAULT_GATEWAY_USER
GATEWAY_PASSWORD = DEFAULT_GATEWAY_PASSWORD
DAYS_BEFORE      = DEFAULT_DAYS_BEFORE
EXACT_DAY_MODE   = DEFAULT_EXACT_MODE  # False=Plage, True=Exact
APP_LANGUAGE     = "fr"
APP_THEME        = "dark"

# ── 📝 Templates de Messages SMS ──────────────────────────────
SMS_TEMPLATES_FR = {
    "auto": "Monsieur {nom}, votre assurance {marque} immatriculée {matricule} expire dans {days_left} jour(s). Merci de renouveler à temps. CRMA Saïda.",
    "generic": "Monsieur {nom}, votre assurance {groupe} expire dans {days_left} jour(s). Merci de renouveler à temps. CRMA Saïda.",
}

SMS_TEMPLATES_EN = {
    "auto": "Monsieur {nom}, votre assurance {marque} immatriculée {matricule} expire dans {days_left} jour(s). Merci de renouveler à temps. CRMA Saïda.",
    "generic": "Monsieur {nom}, votre assurance {groupe} expire dans {days_left} jour(s). Merci de renouveler à temps. CRMA Saïda.",
}

# ── Colonnes Excel & Métier ───────────────────────────────────
COL_NOM         = "Nom"
COL_TEL         = "Tél"
COL_EXPIRATION  = "Expiration"
COL_GROUPE      = "Groupe"
COL_MARQUE      = "Marque"
COL_MATRICULE   = "Matricule"
AUTO_GROUPE_VALUE = "10 Auto Matériel"
COUNTRY_CODE    = "+213"

# ── Structure du fichier Excel ────────────────────────────────
EXCEL_HEADER_ROW = 5        # Ligne 6 (index 0-based = 5) contient les en-têtes
EXCEL_DATA_START = 7        # Ligne 8 (index 0-based = 7) contient les données

# ── Chargement et Sauvegarde ──────────────────────────────────
def load_user_config():
    global GATEWAY_URL, GATEWAY_USER, GATEWAY_PASSWORD, DAYS_BEFORE
    global EXACT_DAY_MODE, APP_LANGUAGE, APP_THEME
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            GATEWAY_URL      = data.get("gateway_url", DEFAULT_GATEWAY_URL)
            GATEWAY_USER     = data.get("gateway_user", DEFAULT_GATEWAY_USER)
            GATEWAY_PASSWORD = data.get("gateway_password", DEFAULT_GATEWAY_PASSWORD)
            DAYS_BEFORE      = int(data.get("days_before", DEFAULT_DAYS_BEFORE))
            EXACT_DAY_MODE   = bool(data.get("exact_mode", DEFAULT_EXACT_MODE))
            APP_LANGUAGE     = data.get("language", "fr")
            APP_THEME        = data.get("theme", "dark")
        except Exception as e:
            print(f"⚠️ Erreur chargement config: {e}")

def save_user_config():
    data = {
        "gateway_url": GATEWAY_URL,
        "gateway_user": GATEWAY_USER,
        "gateway_password": GATEWAY_PASSWORD,
        "days_before": DAYS_BEFORE,
        "exact_mode": EXACT_DAY_MODE,
        "language": APP_LANGUAGE,
        "theme": APP_THEME,
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Erreur sauvegarde config: {e}")

# Charger au démarrage
load_user_config()

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)