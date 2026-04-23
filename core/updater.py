# =============================================================
# core/updater.py — Système de mise à jour GitHub
# =============================================================

import os
import sys
import json
import zipfile
import shutil
import requests
from config import APP_VERSION, GITHUB_OWNER, GITHUB_REPO, BASE_DIR
from core.logger import logger

# Chemins pour les fichiers de mise à jour
UPDATE_DIR = os.path.join(BASE_DIR, "data", "_update")
UPDATE_ZIP = os.path.join(BASE_DIR, "data", "_update", "release.zip")

# Éléments à NE JAMAIS écraser (données utilisateur)
PRESERVE_FOLDERS = ["data", "logs", "images", "__pycache__", ".git"]
PRESERVE_FILES = ["user_config.json", "config.py", "settings.json"]

def get_latest_release():
    """Récupère les infos de la dernière release depuis l'API GitHub"""
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    headers = {"User-Agent": "CRMA-SMS-App/1.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"❌ Échec vérification update: {e}")
    return None

def download_update(release_data):
    """Télécharge le fichier ZIP de la release"""
    assets = release_data.get("assets", [])
    if not assets:
        logger.error("Aucun fichier trouvé dans cette release")
        return False
    
    # Prendre le premier fichier ZIP trouvé
    asset = None
    for a in assets:
        if a.get("name", "").endswith(".zip"):
            asset = a
            break
    
    if not asset:
        logger.error("Aucun fichier ZIP trouvé")
        return False
    
    url = asset.get("browser_download_url")
    filename = asset.get("name")
    
    logger.info(f"📥 Téléchargement de {filename}...")
    
    # Créer le dossier temporaire
    if not os.path.exists(UPDATE_DIR):
        os.makedirs(UPDATE_DIR)
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(UPDATE_ZIP, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info("✅ Mise à jour téléchargée")
        return True
    except Exception as e:
        logger.error(f"❌ Échec téléchargement: {e}")
        return False

def is_update_pending():
    """Vérifie s'il y a une mise à jour en attente d'installation"""
    return os.path.exists(UPDATE_ZIP)

def apply_update():
    """
    Extrait et applique la mise à jour.
    Doit être appelé AU DÉMARRAGE de l'application.
    """
    if not is_update_pending():
        return False
    
    logger.info("📦 Application de la mise à jour...")
    
    try:
        # Extraire le ZIP
        with zipfile.ZipFile(UPDATE_ZIP, 'r') as zip_ref:
            zip_ref.extractall(UPDATE_DIR)
        
        # Trouver le dossier racine du ZIP (ex: "crma-sms-v1.0.0")
        items = os.listdir(UPDATE_DIR)
        if not items:
            raise Exception("ZIP vide ou mal structuré")
        
        root_folder = items[0]
        source_folder = os.path.join(UPDATE_DIR, root_folder)
        
        # Copier les fichiers en préservant les données utilisateur
        for item in os.listdir(source_folder):
            if item in PRESERVE_FOLDERS or item in PRESERVE_FILES:
                logger.info(f"⏭️ Préservé: {item}")
                continue
            
            src = os.path.join(source_folder, item)
            dst = os.path.join(BASE_DIR, item)
            
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                logger.info(f"📁 Dossier copié: {item}")
            else:
                shutil.copy2(src, dst)
                logger.info(f"📄 Fichier copié: {item}")
        
        # Nettoyage
        shutil.rmtree(UPDATE_DIR)
        if os.path.exists(UPDATE_ZIP):
            os.remove(UPDATE_ZIP)
        
        logger.info("🚀 Mise à jour appliquée avec succès")
        return True
        
    except Exception as e:
        logger.error(f"❌ Échec application update: {e}")
        return False

def restart_application():
    """Redémarre l'application avec les nouveaux fichiers"""
    logger.info("🔄 Redémarrage de l'application...")
    python = sys.executable
    # os.execl remplace le processus actuel (plus propre que subprocess)
    os.execl(python, python, *sys.argv)