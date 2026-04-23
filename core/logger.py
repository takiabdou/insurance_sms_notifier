# =============================================================
# core/logger.py — Logging avec support NO_PHONE
# =============================================================

import csv
import logging
import os
from datetime import datetime
from config import APP_LOG_PATH, SENT_LOG_PATH

def setup_logger() -> logging.Logger:
    logger = logging.getLogger("InsuranceSMS")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    
    fh = logging.FileHandler(APP_LOG_PATH, encoding="utf-8", mode="a")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

logger = setup_logger()

# ── CSV Headers enrichis ─────────────────────────────────────
CSV_HEADERS = ["timestamp", "client_name", "phone", "expiry_date", "reminder_type", "status", "attempt_count"]

def _ensure_sent_log():
    if not os.path.exists(SENT_LOG_PATH):
        with open(SENT_LOG_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()

def was_already_sent(phone: str, expiry_date: str, reminder_type: int) -> bool:
    """Check duplicate with reminder type"""
    _ensure_sent_log()
    try:
        with open(SENT_LOG_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row.get("phone") == phone and 
                    row.get("expiry_date") == expiry_date and
                    str(row.get("reminder_type")) == str(reminder_type)):
                    return True
    except Exception as e:
        logger.warning(f"Error reading sent log: {e}")
    return False

def record_sent(client_name: str, phone: str, expiry_date: str, reminder_type: int, status: str, attempt: int = 1):
    """Log with reminder type"""
    _ensure_sent_log()
    with open(SENT_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writerow({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "client_name": client_name,
            "phone": phone,
            "expiry_date": expiry_date,
            "reminder_type": reminder_type,
            "status": status,
            "attempt_count": attempt,
        })

def get_log_summary() -> dict:
    """Stats with NO_PHONE support"""
    _ensure_sent_log()
    stats = {"total": 0, "success": 0, "failed": 0, "skipped": 0, "no_phone": 0, "by_type": {}}
    
    try:
        with open(SENT_LOG_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats["total"] += 1
                status = row.get("status", "UNKNOWN")
                
                if status == "NO_PHONE":
                    stats["no_phone"] += 1
                elif status == "SUCCESS":
                    stats["success"] += 1
                elif status == "FAILED":
                    stats["failed"] += 1
                elif status == "SKIPPED":
                    stats["skipped"] += 1
                
                rtype = row.get("reminder_type", "N/A")
                if rtype not in stats["by_type"]:
                    stats["by_type"][rtype] = {"success": 0, "failed": 0, "no_phone": 0}
                if status == "SUCCESS":
                    stats["by_type"][rtype]["success"] += 1
                elif status == "FAILED":
                    stats["by_type"][rtype]["failed"] += 1
                elif status == "NO_PHONE":
                    stats["by_type"][rtype]["no_phone"] += 1
    except Exception as e:
        logger.warning(f"Could not generate summary: {e}")
    
    return stats