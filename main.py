# =============================================================
# main.py — Point d'entrée CRMA Notify SMS
# =============================================================

import sys
import os
from core.updater import apply_update, restart_application
from gui.dashboard import CRMASMSApp
from config import APP_VERSION

if __name__ == "__main__":
    # ✅ ÉTAPE 1 : Appliquer toute mise à jour en attente
    if apply_update():
        print("✅ Mise à jour installée ! Redémarrage...")
        restart_application()
    
    # ✅ ÉTAPE 2 : Lancer l'application normalement
    print(f"🚀 CRMA Notify SMS v{APP_VERSION} — Démarrage...")
    app = CRMASMSApp()
    app.mainloop()