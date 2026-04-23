# =============================================================
# core/sms_gateway.py — HTTP Gateway SMS (Lecture Dynamique)
# =============================================================

import requests
from requests.auth import HTTPBasicAuth
from core.logger import logger

def send_sms_gateway(phone: str, message: str) -> bool:
    """
    Envoie un SMS via android-sms-gateway (capcom6)
    ✅ Lit la configuration ACTUELLE depuis config.py à chaque appel
    """
    # 🔁 Lecture DYNAMIQUE des variables (pas d'import statique)
    import config
    gateway_url = config.GATEWAY_URL
    gateway_user = config.GATEWAY_USER
    gateway_password = config.GATEWAY_PASSWORD
    
    # Format requis par l'app : phoneNumbers = liste
    payload = {
        "phoneNumbers": [phone],
        "message": message,
    }
    
    try:
        logger.debug(f"[GATEWAY] Envoi vers {gateway_url} pour {phone}")
        
        response = requests.post(
            gateway_url,
            json=payload,
            auth=HTTPBasicAuth(gateway_user, gateway_password),
            timeout=10,
        )
        
        if response.status_code in [200, 202]:
            logger.info(f"[GATEWAY] ✓ SMS queued for {phone} — HTTP {response.status_code}")
            return True
        else:
            logger.error(f"[GATEWAY] ✗ Failed for {phone} — HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error(f"[GATEWAY] ✗ Connection refused. Vérifiez : phone ONLINE + même WiFi + IP={gateway_url}")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"[GATEWAY] ✗ Timeout for {phone}")
        return False
    except Exception as e:
        logger.error(f"[GATEWAY] ✗ Unexpected error for {phone}: {e}")
        return False