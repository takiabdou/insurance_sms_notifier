# =============================================================
# core/sms_router.py — Dispatch & Envoi SMS
# =============================================================
from datetime import date
from config import (
    SMS_TEMPLATES_FR, SMS_TEMPLATES_EN, AUTO_GROUPE_VALUE,
    GATEWAY_URL, GATEWAY_USER, GATEWAY_PASSWORD, APP_LANGUAGE,
    COL_TEL
)
from core.sms_gateway import send_sms_gateway
from core.logger import logger, was_already_sent, record_sent

def get_templates():
    return SMS_TEMPLATES_FR if APP_LANGUAGE == "fr" else SMS_TEMPLATES_EN

def build_message(client: dict) -> str:
    templates = get_templates()
    name = client["name"]
    groupe = client["groupe"]
    marque = client.get("marque", "")
    matricule = client.get("matricule", "")
    days_left = client["days_left"]
    
    if groupe == AUTO_GROUPE_VALUE and marque and matricule:
        return templates["auto"].format(nom=name, marque=marque, matricule=matricule, days_left=days_left)
    return templates["generic"].format(nom=name, groupe=groupe, days_left=days_left)

def dispatch_sms_for_client(client: dict, callback=None) -> list:
    name = client["name"]
    phones = client["phones"]
    expiry_date = client["expiry_date"]
    days_left = client["days_left"]
    results = []
    
    if not phones:
        result = {"name": name, "phone": None, "expiry_date": expiry_date, "days_left": days_left, "status": "NO_PHONE", "skipped": True, "message": f"Client '{name}' n'a pas de numéro"}
        results.append(result)
        if callback: callback(result)
        return results
    
    for phone in phones:
        result = {"name": name, "phone": phone, "expiry_date": expiry_date, "days_left": days_left, "status": None, "skipped": False}
        
        if was_already_sent(phone, expiry_date, days_left):
            result["status"] = "SKIPPED"; result["skipped"] = True
            results.append(result)
            if callback: callback(result)
            continue
        
        message = build_message(client)
        success = send_sms_gateway(phone, message)
        status = "SUCCESS" if success else "FAILED"
        record_sent(name, phone, expiry_date, days_left, status)
        result["status"] = status
        results.append(result)
        if callback: callback(result)
    return results

def run_notification_job(filepath: str, callback=None, days_before_filter=None, mode="range") -> list:
    from core.excel_reader import load_clients, filter_expiring_clients
    all_results = []
    try:
        logger.info("🚀 Démarrage du Job CRMA Notify SMS...")
        df = load_clients(filepath)
        if days_before_filter is None: days_before_filter = 10
        
        logger.info(f"📅 Envoi mode '{mode}' pour jours: {days_before_filter}")
        clients, _ = filter_expiring_clients(df, max_days=days_before_filter, mode=mode)
        
        if not clients: logger.info("✓ Aucun client à relancer"); return all_results
        
        for client in clients:
            results = dispatch_sms_for_client(client, callback)
            all_results.extend(results)
                
    except Exception as e:
        logger.error(f"💥 Job failed: {e}", exc_info=True); raise
    
    return all_results