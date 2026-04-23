# =============================================================
# core/excel_reader.py — Lecture, Nettoyage & Filtrage
# =============================================================
import re
import pandas as pd
from datetime import date
from typing import List, Dict, Tuple
from config import (
    EXCEL_HEADER_ROW,
    COL_NOM, COL_TEL, COL_EXPIRATION, COL_GROUPE, COL_MARQUE, COL_MATRICULE,
    AUTO_GROUPE_VALUE, COUNTRY_CODE
)
from core.logger import logger

def clean_phone_string(raw_phone: str) -> List[str]:
    """
    Nettoie et normalise les numéros de téléphone.
    Gère TOUS les séparateurs: espace, virgule, tiret, point, astérisque, slash
    """
    if pd.isna(raw_phone) or not raw_phone:
        return []
    
    raw_str = str(raw_phone).strip()
    
    # Séparateurs ENTRE numéros différents (plusieurs numéros dans une cellule)
    # On remplace d'abord les séparateurs courants par une virgule
    for sep in ['  ', ' ']:  # Espaces multiples puis simples
        raw_str = raw_str.replace(sep, ',')
    
    # Séparer les numéros
    parts = raw_str.split(',')
    valid_phones = []
    
    for part in parts:
        # Nettoyer le numéro individuel
        # Étape 1: Enlever TOUS les séparateurs internes
        # Virgule, tiret, point, astérisque, slash, espace
        clean = re.sub(r'[,\-\.\/\*\s]', '', part)
        
        # Étape 2: Garder uniquement les chiffres
        digits = re.sub(r'[^\d]', '', clean)
        
        # Étape 3: Vérifier la longueur (doit être 10 chiffres pour un numéro algérien)
        if len(digits) != 10:
            continue  # Ignorer les numéros invalides
        
        # Étape 4: Vérifier que ça commence par 07, 05, 06 ou 04
        if not digits.startswith(('07', '05', '06', '04')):
            continue
        
        # Étape 5: Convertir en format international (+213...)
        formatted = f"+213{digits[1:]}"  # Enlève le 0 et ajoute +213
        
        if formatted not in valid_phones:
            valid_phones.append(formatted)
    
    return valid_phones

def load_clients(filepath: str) -> pd.DataFrame:
    """Charge RelanceClient.xlsx et normalise les dates (DD/MM/YYYY -> YYYY-MM-DD)"""
    logger.info(f"📂 Chargement: {filepath}")
    try:
        df = pd.read_excel(filepath, engine="openpyxl", skiprows=5, header=0)
    except Exception as e:
        logger.error(f"❌ Erreur lecture Excel: {e}"); raise

    df.columns = df.columns.str.strip()
    logger.info(f"📋 Colonnes: {list(df.columns)}")

    required = {COL_NOM, COL_TEL, COL_EXPIRATION, COL_GROUPE}
    missing = required - set(df.columns)
    if missing: raise ValueError(f"❌ Colonnes manquantes: {missing}")

    logger.info("📅 Normalisation des dates...")
    df[COL_EXPIRATION] = pd.to_datetime(df[COL_EXPIRATION], dayfirst=True, errors='coerce')
    
    invalid_dates = df[COL_EXPIRATION].isna().sum()
    if invalid_dates > 0:
        logger.warning(f"⚠️ {invalid_dates} dates invalides ignorées")
        df.dropna(subset=[COL_EXPIRATION], inplace=True)
        
    df[COL_EXPIRATION] = df[COL_EXPIRATION].dt.strftime('%Y-%m-%d')

    df[COL_NOM] = df[COL_NOM].astype(str).str.strip().str.upper()
    df[COL_GROUPE] = df[COL_GROUPE].astype(str).str.strip()
    df[COL_MARQUE] = df[COL_MARQUE].astype(str).str.strip()
    df[COL_MATRICULE] = df[COL_MATRICULE].astype(str).str.strip()

    logger.info(f"✅ {len(df)} clients chargés")
    return df

def filter_expiring_clients(df: pd.DataFrame, max_days: int = 10, mode: str = "range") -> Tuple[List[Dict], List[str]]:
    """
    Filtre selon le mode:
    - "range": 0 <= jours <= max_days (Plage)
    - "exact": jours == max_days (Exact)
    """
    today = date.today()
    clients_to_send = []
    no_phone_alerts = []

    logger.info(f"🎯 Filtrage mode '{mode}' avec max_days={max_days}...")

    for _, row in df.iterrows():
        try:
            exp_date = date.fromisoformat(row[COL_EXPIRATION])
            days_left = (exp_date - today).days
        except: continue

        # ✅ Logique conditionnelle
        if mode == "exact":
            if days_left != max_days: continue
        else:
            if days_left < 0 or days_left > max_days: continue

        phones = clean_phone_string(row[COL_TEL])
        client_data = {
            "name": row[COL_NOM], "groupe": row[COL_GROUPE],
            "marque": row.get(COL_MARQUE, ""), "matricule": row.get(COL_MATRICULE, ""),
            "phones": phones, "expiry_date": row[COL_EXPIRATION],
            "days_left": days_left, "raw_tel": row[COL_TEL]
        }

        if not phones:
            logger.warning(f"🚨 '{client_data['name']}' sans numéro")
            no_phone_alerts.append(f"Client '{client_data['name']}' : Aucun numéro valide")
        
        clients_to_send.append(client_data)

    logger.info(f"✅ {len(clients_to_send)} client(s) trouvé(s)")
    if no_phone_alerts: logger.warning(f"⚠️ {len(no_phone_alerts)} sans numéro")
    return clients_to_send, no_phone_alerts