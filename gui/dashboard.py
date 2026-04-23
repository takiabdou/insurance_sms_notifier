# =============================================================
# gui/dashboard.py — Interface CRMA Notify SMS (Pro)
# =============================================================
import csv
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Menu
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw
import requests
from requests.auth import HTTPBasicAuth
import random

from config import (
    SENT_LOG_PATH, DATA_DIR, IMAGES_DIR, CONFIG_FILE,
    GATEWAY_URL, GATEWAY_USER, GATEWAY_PASSWORD, DAYS_BEFORE,
    APP_LANGUAGE, APP_THEME, COL_EXPIRATION, EXACT_DAY_MODE,
    load_user_config, save_user_config
)
from core.sms_router import run_notification_job
from core.logger import logger, get_log_summary

THEMES = {
    "dark": {"bg_main": "#080c14", "bg_panel": "#0d1220", "bg_card": "#111827", "bg_hover": "#1a2840", "border": "#1a2840", "accent_red": "#ef4444", "accent_cyan": "#06b6d4", "accent_green": "#10b981", "accent_yellow": "#f59e0b", "accent_orange": "#ff9f43", "text_primary": "#e2e8f0", "text_secondary": "#94a3b8", "text_muted": "#475569", "entry_bg": "#0f3460", "entry_fg": "#ccd6f6"},
    "light": {"bg_main": "#f0f2f5", "bg_panel": "#ffffff", "bg_card": "#ffffff", "bg_hover": "#e8eaed", "border": "#d1d5db", "accent_red": "#dc2626", "accent_cyan": "#0891b2", "accent_green": "#059669", "accent_yellow": "#d97706", "accent_orange": "#ea580c", "text_primary": "#1f2937", "text_secondary": "#6b7280", "text_muted": "#9ca3af", "entry_bg": "#f3f4f6", "entry_fg": "#1f2937"}
}

TRANSLATIONS = {
    "fr": {"app_title": "CRMA Notify SMS", "subtitle": "Système de Notification de Renouvellement", "file_label": "📁 Fichier Excel:", "browse": "Parcourir...", "send_btn": "🚀 Envoyer les Rappels SMS", "sending": "⏳ Envoi en cours...", "refresh": "🔄 Actualiser", "ping": "📡 Tester Connexion", "total": "Total Clients", "expiring": "À renouveler", "sent": "SMS Envoyés", "skipped": "Ignorés", "logs_title": "📋 Historique des Envois", "config_title": "⚙️ Configuration Gateway", "gateway_ip": "IP Gateway:", "port": "Port:", "user": "Utilisateur:", "password": "Mot de passe:", "days_before": "Jours avant expiry:", "mode_label": "📌 Mode d'envoi:", "mode_range": "📅 Plage (0 à N jours)", "mode_exact": "🎯 Exact (N jours seulement)", "save_config": "💾 Sauvegarder", "activity_title": "📡 Activité en Direct", "clear": "Effacer", "alert_no_phone": "⚠️ Clients sans numéro de téléphone", "job_summary": "Envoyés: {sent} | Échecs: {failed} | Ignorés: {skipped} | Sans Tél: {no_phone}", "config_saved": "Configuration sauvegardée avec succès!", "select_file_error": "Veuillez sélectionner un fichier Excel valide.", "theme_dark": "🌙 Mode Sombre", "theme_light": "☀️ Mode Clair", "lang_fr": "🇫🇷 Français", "lang_en": "🇬 English", "menu_info": "ℹ️ Info", "menu_update": "🔄 Vérifier Mise à jour", "menu_about": "👤 À propos...", "menu_settings": "⚙️ Paramètres", "menu_theme": "🎨 Thème", "menu_language": "🌐 Langue", "about_text": "Application développée par\n\nHALIMI Abdellah Takieddine\nCHARGÉ DU SERVICE INFORMATIQUE\nCRMA DE SAÏDA\n\n© 2026 CRMA Saïda. Tous droits réservés.", "hours": ["Heure", "Client", "Téléphone", "Expiration", "J-", "Statut"]},
    "en": {"app_title": "CRMA Notify SMS", "subtitle": "Renewal Notification System", "file_label": "📁 Excel File:", "browse": "Browse...", "send_btn": "🚀 Send SMS Reminders", "sending": "⏳ Sending...", "refresh": "🔄 Refresh", "ping": "📡 Test Connection", "total": "Total Clients", "expiring": "To Renew", "sent": "SMS Sent", "skipped": "Skipped", "logs_title": "📋 Send History", "config_title": "⚙️ Gateway Configuration", "gateway_ip": "Gateway IP:", "port": "Port:", "user": "Username:", "password": "Password:", "days_before": "Days before expiry:", "mode_label": "📌 Send Mode:", "mode_range": "📅 Range (0 to N days)", "mode_exact": "🎯 Exact (N days only)", "save_config": "💾 Save", "activity_title": "📡 Live Activity", "clear": "Clear", "alert_no_phone": "⚠️ Clients without phone number", "job_summary": "Sent: {sent} | Failed: {failed} | Skipped: {skipped} | No Phone: {no_phone}", "config_saved": "Configuration saved successfully!", "select_file_error": "Please select a valid Excel file.", "theme_dark": "🌙 Dark Mode", "theme_light": "☀️ Light Mode", "lang_fr": "🇫 Français", "lang_en": "🇬🇧 English", "menu_info": "ℹ️ Info", "menu_update": "🔄 Check Update", "menu_about": "👤 About...", "menu_settings": "⚙️ Settings", "menu_theme": "🎨 Theme", "menu_language": "🌐 Language", "about_text": "Application developed by\n\nHALIMI Abdellah Takieddine\nIT SERVICE MANAGER\nCRMA SAÏDA\n\n© 2026 CRMA Saïda. All rights reserved.", "hours": ["Time", "Client", "Phone", "Expiry", "Days", "Status"]}
}

def load_round_image(path, size=40):
    try:
        img = Image.open(path).convert("RGBA")
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask)
        return ImageTk.PhotoImage(result)
    except: return None

class CRMASMSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CRMA Notify SMS")
        self.geometry("1320x850")
        self.minsize(1100, 700)
        self.is_running = False
        self.no_phone_alerts = []
        self.current_theme = APP_THEME
        self.current_lang = APP_LANGUAGE
        self.expiring_count = 0
        
        self.logo_photo = load_round_image(os.path.join(IMAGES_DIR, "logo.png"), 36)
        self.photo_photo = load_round_image(os.path.join(IMAGES_DIR, "photos.png"), 120)
        self.t = TRANSLATIONS[self.current_lang]
        self.colors = THEMES[self.current_theme]
        
        self._build_menu()
        self._build_ui()
        self._refresh_all()
        self._update_clock()

    def _build_menu(self):
        menubar = tk.Menu(self)
        info_menu = tk.Menu(menubar, tearoff=0)
        info_menu.add_command(label=self.t["menu_update"], command=lambda: messagebox.showinfo(self.t["menu_update"], "Version 1.0.0 Stable"))
        info_menu.add_separator()
        info_menu.add_command(label=self.t["menu_about"], command=self._show_about)
        info_menu.add_command(label="🔄 Vérifier Mise à jour", command=self._check_github_update)
        menubar.add_cascade(label=self.t["menu_info"], menu=info_menu)
                
        settings_menu = tk.Menu(menubar, tearoff=0)
        theme_menu = tk.Menu(settings_menu, tearoff=0)
        theme_menu.add_command(label=self.t["theme_dark"], command=lambda: self._set_theme("dark"))
        theme_menu.add_command(label=self.t["theme_light"], command=lambda: self._set_theme("light"))
        settings_menu.add_cascade(label=self.t["menu_theme"], menu=theme_menu)
        
        lang_menu = tk.Menu(settings_menu, tearoff=0)
        lang_menu.add_command(label=self.t["lang_fr"], command=lambda: self._set_language("fr"))
        lang_menu.add_command(label=self.t["lang_en"], command=lambda: self._set_language("en"))
        settings_menu.add_cascade(label=self.t["menu_language"], menu=lang_menu)
        menubar.add_cascade(label=self.t["menu_settings"], menu=settings_menu)
        self.config(menu=menubar)

    def _set_theme(self, theme):
        self.current_theme = theme
        self.colors = THEMES[theme]
        import config; config.APP_THEME = theme; save_user_config()
        for w in self.winfo_children(): w.destroy()
        self._build_menu(); self._build_ui(); self._refresh_all()

    def _set_language(self, lang):
        self.current_lang = lang
        self.t = TRANSLATIONS[lang]
        import config; config.APP_LANGUAGE = lang; save_user_config()
        for w in self.winfo_children(): w.destroy()
        self._build_menu(); self._build_ui(); self._refresh_all()

    def _build_ui(self):
        c = self.colors
        header = tk.Frame(self, bg=c["bg_panel"], height=60)
        header.pack(fill="x", side="top"); header.pack_propagate(False)
        
        brand = tk.Frame(header, bg=c["bg_panel"])
        brand.pack(side="left", padx=20, pady=8)
        if self.logo_photo: tk.Label(brand, image=self.logo_photo, bg=c["bg_panel"]).pack(side="left", padx=(0, 10))
        tk.Label(brand, text=self.t["app_title"], font=("Consolas", 16, "bold"), fg=c["accent_red"], bg=c["bg_panel"]).pack(side="left")
        tk.Label(brand, text=self.t["subtitle"], font=("Segoe UI", 8), fg=c["text_muted"], bg=c["bg_panel"]).pack(side="left", padx=10)
        
        clock = tk.Frame(header, bg=c["bg_card"], bd=0, highlightthickness=1, highlightbackground=c["border"])
        clock.pack(side="left", padx=20)
        self.clock_label = tk.Label(clock, text="", font=("Consolas", 10), fg=c["accent_cyan"], bg=c["bg_card"], width=16)
        self.clock_label.pack(padx=12, pady=6)
        
        self.status_pill = tk.Frame(header, bg=c["bg_card"], bd=0, highlightthickness=1, highlightbackground=c["border"])
        self.status_pill.pack(side="right", padx=20)
        self.status_dot = tk.Canvas(self.status_pill, width=8, height=8, bg=c["bg_card"], highlightthickness=0)
        self.status_dot.pack(side="left", padx=(10, 5), pady=8)
        self.status_label = tk.Label(self.status_pill, text="Gateway Online", font=("Consolas", 9), fg=c["accent_green"], bg=c["bg_card"])
        self.status_label.pack(side="left", padx=(0, 10), pady=8)

        main = tk.Frame(self, bg=c["bg_main"])
        main.pack(fill="both", expand=True, padx=20, pady=16)
        self._build_stats(main)
        
        grid = tk.Frame(main, bg=c["bg_main"])
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(0, weight=1); grid.columnconfigure(1, weight=0, minsize=320)
        self._build_main_panel(grid, 0, 0)
        self._build_sidebar(grid, 0, 1)

        self.alert_panel = tk.Frame(main, bg="#2d1a1a" if c==THEMES["dark"] else "#fef2f2", bd=0, highlightthickness=1, highlightbackground=c["accent_red"])
        self.alert_label = tk.Label(self.alert_panel, text="", fg="#ffb3b3" if c==THEMES["dark"] else "#dc2626", bg="#2d1a1a" if c==THEMES["dark"] else "#fef2f2", font=("Segoe UI", 9), justify="left")
        self.alert_label.pack(padx=12, pady=8, fill="x")

    def _build_stats(self, parent):
        c = self.colors
        frame = tk.Frame(parent, bg=c["bg_main"])
        frame.pack(fill="x", pady=(0, 16))
        self.stat_cards = {}
        cards = [(self.t["total"], "total", c["accent_cyan"]), (self.t["expiring"], "expiring", c["accent_red"]), 
                 (self.t["sent"], "sent", c["accent_green"]), (self.t["skipped"], "skipped", c["accent_yellow"])]
        for label, key, color in cards:
            card = tk.Frame(frame, bg=c["bg_card"], bd=0, highlightthickness=1, highlightbackground=c["border"])
            card.pack(side="left", fill="both", expand=True, padx=4)
            tk.Frame(card, height=3, bg=color).pack(fill="x")
            content = tk.Frame(card, bg=c["bg_card"])
            content.pack(fill="both", expand=True, padx=14, pady=10)
            tk.Label(content, text=label, font=("Segoe UI", 9), fg=c["text_muted"], bg=c["bg_card"]).pack(anchor="w")
            val = tk.Label(content, text="0", font=("Consolas", 26, "bold"), fg=color, bg=c["bg_card"])
            val.pack(anchor="w", pady=(2, 0))
            self.stat_cards[key] = val

    def _build_main_panel(self, parent, row, col):
        c = self.colors
        panel = tk.Frame(parent, bg=c["bg_card"], bd=0, highlightthickness=1, highlightbackground=c["border"])
        panel.grid(row=row, column=col, sticky="nsew", padx=(0, 10))
        
        hd = tk.Frame(panel, bg=c["bg_card"], height=44)
        hd.pack(fill="x", padx=14, pady=(10, 0))
        tk.Label(hd, text=self.t["logs_title"], font=("Segoe UI", 10, "bold"), fg=c["text_primary"], bg=c["bg_card"]).pack(side="left")
        self.log_count = tk.Label(hd, text="0", font=("Consolas", 9), fg=c["text_muted"], bg=c["bg_card"])
        self.log_count.pack(side="right")

        file_frame = tk.Frame(panel, bg=c["bg_card"])
        file_frame.pack(fill="x", padx=14, pady=10)
        tk.Label(file_frame, text=self.t["file_label"], font=("Segoe UI", 9, "bold"), fg=c["text_secondary"], bg=c["bg_card"]).pack(side="left")
        self.file_entry = tk.Entry(file_frame, font=("Segoe UI", 9), bg=c["entry_bg"], fg=c["entry_fg"], relief="flat", bd=0, highlightthickness=1, highlightbackground=c["border"])
        self.file_entry.pack(side="left", fill="x", expand=True, padx=8)
        tk.Button(file_frame, text=self.t["browse"], command=self._browse_file, bg=c["accent_red"], fg="white", font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=14, cursor="hand2").pack(side="left")

        btn_frame = tk.Frame(panel, bg=c["bg_card"])
        btn_frame.pack(fill="x", padx=14, pady=(0, 10))
        self.run_btn = tk.Button(btn_frame, text=self.t["send_btn"], command=self._run_job_threaded, bg=c["accent_green"], fg="white", font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=20, pady=8, cursor="hand2")
        self.run_btn.pack(side="left", fill="x", expand=True)
        tk.Button(btn_frame, text=self.t["refresh"], command=self._refresh_all, bg=c["bg_hover"], fg=c["text_secondary"], font=("Segoe UI", 9), relief="flat", bd=0, padx=12, cursor="hand2").pack(side="left", padx=4)
        tk.Button(btn_frame, text=self.t["ping"], command=self._check_gateway, bg=c["bg_hover"], fg=c["text_secondary"], font=("Segoe UI", 9), relief="flat", bd=0, padx=12, cursor="hand2").pack(side="left")

        self.progress_frame = tk.Frame(panel, bg=c["bg_card"])
        self.progress = ttk.Progressbar(self.progress_frame, mode="indeterminate")
        self.progress_label = tk.Label(self.progress_frame, text="", font=("Segoe UI", 9), fg=c["text_muted"], bg=c["bg_card"])

        table_frame = tk.Frame(panel, bg=c["bg_card"])
        table_frame.pack(fill="both", expand=True, padx=14, pady=(8, 14))
        style = ttk.Style(); style.theme_use("clam")
        style.configure("Treeview", background=c["bg_hover"], foreground=c["text_primary"], fieldbackground=c["bg_hover"], rowheight=26, font=("Segoe UI", 9), borderwidth=0)
        style.configure("Treeview.Heading", background=c["bg_card"], foreground=c["accent_red"], font=("Segoe UI", 9, "bold"), borderwidth=0, relief="flat")
        style.map("Treeview", background=[("selected", c["accent_cyan"])], foreground=[("selected", "white")])
        
        cols = self.t["hours"]
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=14)
        for col in cols: self.tree.heading(col, text=col)
        for col, w in zip(cols, [120, 140, 120, 100, 40, 90]): self.tree.column(col, width=w, anchor="center")
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        self.tree.tag_configure("success", foreground=c["accent_green"])
        self.tree.tag_configure("failed", foreground=c["accent_red"])
        self.tree.tag_configure("skipped", foreground=c["accent_yellow"])
        self.tree.tag_configure("no_phone", foreground=c["accent_orange"])

    def _build_sidebar(self, parent, row, col):
        c = self.colors
        sidebar = tk.Frame(parent, bg=c["bg_main"], width=320)
        sidebar.grid(row=row, column=col, sticky="nsew"); sidebar.grid_propagate(False)
        self._build_config_panel(sidebar)
        self._build_mini_chart(sidebar)
        self._build_activity_panel(sidebar)

    def _build_config_panel(self, parent):
        c = self.colors
        import config
        panel = tk.Frame(parent, bg=c["bg_card"], bd=0, highlightthickness=1, highlightbackground=c["border"])
        panel.pack(fill="x", pady=(0, 10))
        tk.Label(panel, text=self.t["config_title"], font=("Segoe UI", 10, "bold"), fg=c["text_primary"], bg=c["bg_card"]).pack(padx=12, pady=(8,4), anchor="w")
        
        try:
            clean_url = config.GATEWAY_URL.split("://")[1] if "://" in config.GATEWAY_URL else config.GATEWAY_URL
            ip_part = clean_url.split(":")[0]
            port_part = clean_url.split(":")[1].split("/")[0]
        except: ip_part, port_part = "192.168.1.9", "8080"

        fields = [("gateway_ip", self.t["gateway_ip"], ip_part), ("port", self.t["port"], port_part),
                  ("user", self.t["user"], config.GATEWAY_USER), ("password", self.t["password"], config.GATEWAY_PASSWORD),
                  ("days", self.t["days_before"], str(config.DAYS_BEFORE))]
        self.config_entries = {}
        for key, label, default in fields:
            row = tk.Frame(panel, bg=c["bg_card"]); row.pack(fill="x", padx=12, pady=3)
            tk.Label(row, text=label, font=("Segoe UI", 9), fg=c["text_secondary"], bg=c["bg_card"], width=14, anchor="w").pack(side="left")
            entry = tk.Entry(row, font=("Consolas", 9), bg=c["entry_bg"], fg=c["entry_fg"], relief="flat", bd=0, highlightthickness=1, highlightbackground=c["border"])
            entry.insert(0, default); entry.pack(side="right", fill="x", expand=True)
            self.config_entries[key] = entry

        mode_frame = tk.Frame(panel, bg=c["bg_card"])
        mode_frame.pack(fill="x", padx=12, pady=5)
        tk.Label(mode_frame, text=self.t["mode_label"], font=("Segoe UI", 9), fg=c["text_secondary"], bg=c["bg_card"], width=14, anchor="w").pack(side="left")
        self.mode_var = tk.StringVar(value="exact" if config.EXACT_DAY_MODE else "range")
        mode_cb = ttk.Combobox(mode_frame, textvariable=self.mode_var, values=[self.t["mode_range"], self.t["mode_exact"]], state="readonly", font=("Segoe UI", 9), width=24)
        mode_cb.pack(side="right", fill="x", expand=True)
        self.config_entries["mode"] = mode_cb
            
        tk.Button(panel, text=self.t["save_config"], command=self._save_config, bg=c["accent_cyan"], fg="white", font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=14, pady=5).pack(pady=8)

    def _build_mini_chart(self, parent):
        c = self.colors
        panel = tk.Frame(parent, bg=c["bg_card"], bd=0, highlightthickness=1, highlightbackground=c["border"])
        panel.pack(fill="x", pady=(0, 10))
        tk.Label(panel, text="📊 Activité (7 jours)", font=("Segoe UI", 10, "bold"), fg=c["text_primary"], bg=c["bg_card"]).pack(padx=12, pady=(6,2), anchor="w")
        self.chart_canvas = tk.Canvas(panel, width=280, height=50, bg=c["bg_card"], highlightthickness=0)
        self.chart_canvas.pack(padx=12, pady=6)
        self._draw_weekly_chart()

    def _draw_weekly_chart(self):
        c = self.colors
        data = [random.randint(3, 12) for _ in range(7)]
        max_val = max(data) or 1
        w, h, bar_w = 280, 45, 32
        for i, val in enumerate(data):
            x0 = i * (bar_w + 4) + 10
            y0 = h - (val / max_val) * h
            color = c["accent_green"] if i == 6 else "#2a4a3a" if c==THEMES["dark"] else "#d1fae5"
            self.chart_canvas.create_rectangle(x0, y0, x0 + bar_w, h, fill=color, outline="")

    def _build_activity_panel(self, parent):
        c = self.colors
        panel = tk.Frame(parent, bg=c["bg_card"], bd=0, highlightthickness=1, highlightbackground=c["border"])
        panel.pack(fill="both", expand=True, pady=(0, 10))
        
        hd = tk.Frame(panel, bg=c["bg_card"], height=36)
        hd.pack(fill="x", padx=12, pady=(6, 0))
        tk.Label(hd, text=self.t["activity_title"], font=("Segoe UI", 10, "bold"), fg=c["text_primary"], bg=c["bg_card"]).pack(side="left")
        tk.Button(hd, text=self.t["clear"], command=self._clear_activity, bg=c["bg_hover"], fg=c["text_secondary"], font=("Segoe UI", 8), relief="flat", bd=0, padx=8).pack(side="right")

        self.activity_canvas = tk.Canvas(panel, bg=c["bg_card"], highlightthickness=0, height=220)
        self.activity_scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.activity_canvas.yview)
        self.activity_frame = tk.Frame(self.activity_canvas, bg=c["bg_card"])

        self.activity_canvas.create_window((0, 0), window=self.activity_frame, anchor="nw", tags="activity")
        self.activity_canvas.configure(yscrollcommand=self.activity_scrollbar.set)
        self.activity_frame.bind("<Configure>", lambda e: self.activity_canvas.configure(scrollregion=self.activity_canvas.bbox("all")))
        self.activity_canvas.bind("<Enter>", lambda e: self.activity_canvas.bind_all("<MouseWheel>", self._on_activity_mousewheel))
        self.activity_canvas.bind("<Leave>", lambda e: self.activity_canvas.unbind_all("<MouseWheel>"))
        self.activity_canvas.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        self.activity_scrollbar.pack(side="right", fill="y", pady=8)

    def _on_activity_mousewheel(self, event): self.activity_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    def _add_activity(self, msg, color=None):
        c = self.colors
        frame = tk.Frame(self.activity_frame, bg=c["bg_card"]); frame.pack(fill="x", padx=8, pady=3)
        dot = tk.Canvas(frame, width=8, height=8, bg=c["bg_card"], highlightthickness=0)
        dot.create_oval(0, 0, 8, 8, fill=color or c["accent_cyan"], outline=""); dot.pack(side="left", padx=(0, 8), pady=4)
        tk.Label(frame, text=msg, font=("Segoe UI", 8), fg=c["text_secondary"], bg=c["bg_card"], anchor="w", justify="left").pack(side="left", fill="x", expand=True, pady=4)
        self.activity_canvas.update_idletasks(); self.activity_canvas.yview_moveto(1.0)
        children = self.activity_frame.winfo_children()
        if len(children) > 50: children[0].destroy()
    def _clear_activity(self):
        for w in self.activity_frame.winfo_children(): w.destroy()
        self.activity_canvas.yview_moveto(0)

    def _browse_file(self):
        path = filedialog.askopenfilename(initialdir=DATA_DIR, title="Select Excel", filetypes=[("Excel", "*.xlsx")])
        if path:
            self.file_entry.delete(0, tk.END); self.file_entry.insert(0, path)
            try:
                import pandas as pd
                df = pd.read_excel(path, skiprows=5, header=0)
                df.columns = df.columns.str.strip()
                df["Expiration"] = pd.to_datetime(df["Expiration"], dayfirst=True, errors="coerce")
                today = datetime.now().date()
                max_d = int(self.config_entries["days"].get() or 10)
                is_exact = (self.mode_var.get() == self.t["mode_exact"])
                df["_days"] = (df["Expiration"].dt.date - today).dt.days
                self.expiring_count = len(df[df["_days"] == max_d]) if is_exact else len(df[(df["_days"] >= 0) & (df["_days"] <= max_d)])
                self.stat_cards["expiring"].config(text=str(self.expiring_count))
            except: pass

    def _save_config(self):
        import config
        try:
            ip = self.config_entries["gateway_ip"].get().strip(); port = self.config_entries["port"].get().strip()
            config.GATEWAY_URL = f"http://{ip}:{port}/message"
            config.GATEWAY_USER = self.config_entries["user"].get().strip()
            config.GATEWAY_PASSWORD = self.config_entries["password"].get().strip()
            config.DAYS_BEFORE = int(self.config_entries["days"].get().strip())
            config.EXACT_DAY_MODE = (self.mode_var.get() == self.t["mode_exact"])
            save_user_config()
            self._add_activity("✅ " + self.t["config_saved"], self.colors["accent_green"])
        except ValueError: messagebox.showerror("Error", "Jours invalides")

    def _run_job_threaded(self):
        if self.is_running: return
        path = self.file_entry.get().strip()
        if not path or not os.path.exists(path): messagebox.showerror("Error", self.t["select_file_error"]); return
        self.is_running = True; self.run_btn.config(state="disabled", text=self.t["sending"])
        self.progress_frame.pack(fill="x", padx=14, pady=(0, 6))
        self.progress.pack(side="left", fill="x", expand=True); self.progress_label.pack(side="left", padx=8)
        self.progress.start(10); self.progress_label.config(text=self.t["sending"])
        self.no_phone_alerts = []; self._clear_activity(); self._add_activity("🚀 Job started", self.colors["accent_cyan"])
        threading.Thread(target=self._run_job, args=(path,), daemon=True).start()

    def _run_job(self, filepath):
        try:
            days_filter = int(self.config_entries["days"].get().strip())
            mode = "exact" if self.mode_var.get() == self.t["mode_exact"] else "range"
            results = run_notification_job(filepath, callback=self._on_result, days_before_filter=days_filter, mode=mode)
            s, f, sk, np = [sum(1 for r in results if r["status"]==x) for x in ["SUCCESS","FAILED","SKIPPED","NO_PHONE"]]
            self.after(0, lambda: self._job_done(s, f, sk, np))
        except Exception as e:
            logger.error(f"Job error: {e}", exc_info=True)
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, self._job_reset)

    def _on_result(self, result): self.after(0, lambda: self._handle_result(result))
    def _handle_result(self, result):
        st, name, ph = result["status"], result["name"], result.get("phone", "N/A") or "N/A"
        if st == "NO_PHONE":
            self.no_phone_alerts.append(f"{name} — pas de numéro")
            self._add_activity(f"⚠️ {name}: no phone", self.colors["accent_yellow"])
        elif st == "SUCCESS": self._add_activity(f"✅ {name} ({ph})", self.colors["accent_green"])
        elif st == "FAILED": self._add_activity(f"❌ {name}", self.colors["accent_red"])
        elif st == "SKIPPED": self._add_activity(f"⏭️ {name}", self.colors["accent_yellow"])
        self._refresh_logs(); self._update_stats()

    def _job_done(self, sent, failed, skipped, no_phone):
        self.is_running = False; self.run_btn.config(state="normal", text=self.t["send_btn"])
        self.progress.stop(); self.progress_frame.pack_forget()
        summary = self.t["job_summary"].format(sent=sent, failed=failed, skipped=skipped, no_phone=no_phone)
        self._add_activity(f"✅ Done: {summary}", self.colors["accent_green"])
        if self.no_phone_alerts:
            self.alert_label.config(text=self.t["alert_no_phone"] + ":\n" + "\n".join(self.no_phone_alerts[:5]))
            self.alert_panel.pack(fill="x", pady=(0, 8))
        else: self.alert_panel.pack_forget()
        self._refresh_all()

    def _job_reset(self):
        self.is_running = False; self.run_btn.config(state="normal", text=self.t["send_btn"])
        self.progress.stop(); self.progress_frame.pack_forget()

    def _check_gateway(self):
        """Teste VÉRITABLEMENT la connexion au serveur SMS Gateway"""
        import socket
        import config
        
        try:
            ip = self.config_entries["gateway_ip"].get().strip()
            port = self.config_entries["port"].get().strip()
            user = self.config_entries["user"].get().strip()
            pwd = self.config_entries["password"].get().strip()
            url = f"http://{ip}:{port}"
            
            self._add_activity("🔄 Test de connexion...", self.colors["accent_cyan"])
            
            # ÉTAPE 1: Test de connectivité TCP (ping du port)
            self._add_activity(f"📡 Vérification {ip}:{port}...", self.colors["accent_cyan"])
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)  # 3 secondes max
            result = sock.connect_ex((ip, int(port)))
            sock.close()
            
            if result != 0:
                # Le port n'est pas accessible
                self._update_status(False)
                self._add_activity(f"❌ Gateway INJOIGNABLE ({ip}:{port})", self.colors["accent_red"])
                messagebox.showwarning("Connexion échouée", 
                    f"Impossible de joindre la gateway à l'adresse:\n{ip}:{port}\n\n"
                    f"Vérifiez que:\n"
                    f"1. Le téléphone est sur le MÊME réseau WiFi\n"
                    f"2. L'application SMS Gateway est active\n"
                    f"3. L'adresse IP est correcte")
                return
            
            # ÉTAPE 2: Test HTTP avec authentification
            self._add_activity("🔐 Test authentification...", self.colors["accent_cyan"])
            response = requests.get(url, auth=HTTPBasicAuth(user, pwd), timeout=5)
            
            if response.status_code == 200:
                self._update_status(True)
                self._add_activity("✅ Gateway Connectée & Authentifiée", self.colors["accent_green"])
            elif response.status_code == 401:
                self._update_status(False)
                self._add_activity("⚠️ Authentification ÉCHOUÉE", self.colors["accent_yellow"])
                messagebox.showwarning("Authentification échouée", 
                    f"Le serveur est accessible mais:\n"
                    f"❌ Identifiant ou mot de passe incorrect\n\n"
                    f"Vérifiez vos identifiants dans la configuration.")
            else:
                self._update_status(False)
                self._add_activity(f"❌ Erreur HTTP {response.status_code}", self.colors["accent_red"])
                
        except socket.gaierror:
            self._update_status(False)
            self._add_activity(f"❌ IP '{ip}' invalide", self.colors["accent_red"])
            messagebox.showerror("Erreur", f"L'adresse IP '{ip}' est invalide.")
        except requests.exceptions.ConnectionError:
            self._update_status(False)
            self._add_activity("❌ Connexion REFUSÉE", self.colors["accent_red"])
            messagebox.showwarning("Connexion refusée", 
                f"La connexion a été refusée.\n\n"
                f"Vérifiez que:\n"
                f"✓ PC et téléphone sont sur le MÊME WiFi\n"
                f"✓ Le pare-feu Windows autorise la connexion\n"
                f"✓ L'application SMS Gateway est active sur le téléphone")
        except requests.exceptions.Timeout:
            self._update_status(False)
            self._add_activity("⏱️ Délai dépassé (timeout)", self.colors["accent_red"])
            messagebox.showwarning("Timeout", 
                f"Le serveur ne répond pas dans les temps.\n\n"
                f"Le téléphone est-il sur le même réseau ?")
        except Exception as e:
            self._update_status(False)
            self._add_activity(f"❌ Erreur: {str(e)}", self.colors["accent_red"])
            messagebox.showerror("Erreur", f"Erreur inattendue:\n{str(e)}")

    def _update_status(self, online):
        c = self.colors; color = c["accent_green"] if online else c["accent_red"]
        self.status_dot.delete("all"); self.status_dot.create_oval(0, 0, 8, 8, fill=color, outline="")
        self.status_label.config(text="Gateway Online" if online else "Gateway Offline", fg=color)

    def _refresh_all(self): self._refresh_logs(); self._update_stats()
    def _refresh_logs(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        if not os.path.exists(SENT_LOG_PATH): self.log_count.config(text="0"); return
        count = 0
        try:
            with open(SENT_LOG_PATH, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    st = row.get("status", "UNKNOWN")
                    tag = {"SUCCESS": "success", "FAILED": "failed", "SKIPPED": "skipped"}.get(st, "no_phone")
                    self.tree.insert("", "end", values=(row.get("timestamp","")[:16], row.get("client_name","")[:20], row.get("phone","N/A") or "N/A", row.get("expiry_date",""), row.get("reminder_type",""), st), tags=(tag,))
                    count += 1
            self.log_count.config(text=f"{count}")
        except Exception as e: logger.warning(f"Log error: {e}")

    def _update_stats(self):
        stats = get_log_summary()
        self.stat_cards["total"].config(text=str(stats.get("total", 0)))
        self.stat_cards["sent"].config(text=str(stats.get("success", 0)))
        self.stat_cards["skipped"].config(text=str(stats.get("skipped", 0)))

    def _update_clock(self):
        self.clock_label.config(text=datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._update_clock)

    def _show_about(self):
        win = tk.Toplevel(self); win.title("About"); win.geometry("420x380"); win.resizable(False, False)
        win.configure(bg=self.colors["bg_card"]); win.transient(self); win.grab_set()
        c = self.colors
        tk.Frame(win, bg=c["accent_red"], height=8).pack(fill="x")
        if self.photo_photo: tk.Label(win, image=self.photo_photo, bg=c["bg_card"]).pack(pady=16)
        tk.Label(win, text=self.t["about_text"], font=("Segoe UI", 10), fg=c["text_primary"], bg=c["bg_card"], justify="center", pady=10).pack()
        tk.Label(win, text="v1.0.0 • 2026", font=("Segoe UI", 8), fg=c["text_muted"], bg=c["bg_card"]).pack(pady=(10, 16))
        tk.Button(win, text="OK", command=win.destroy, bg=c["accent_cyan"], fg="white", font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=30, pady=6, cursor="hand2").pack(pady=(0, 16))

        def _check_github_update(self):
        """Vérifie et télécharge les mises à jour depuis GitHub"""
        import threading
        from tkinter import messagebox
        from core.updater import get_latest_release, download_update, APP_VERSION
        
        def _do_check():
            # Afficher un message de chargement
            self.after(0, lambda: self._add_activity("🔄 Vérification GitHub...", self.colors["accent_cyan"]))
            
            # Vérifier les mises à jour
            release = get_latest_release()
            
            if not release:
                self.after(0, lambda: messagebox.showerror(
                    "Erreur", 
                    "Impossible de contacter GitHub.\nVérifiez votre connexion Internet."
                ))
                return
            
            # Extraire la version
            latest_version = release.get("tag_name", "0.0.0")
            if latest_version.startswith("v"):
                latest_version = latest_version[1:]  # Enlever le "v"
            
            # Comparer les versions
            if self._version_greater(latest_version, APP_VERSION):
                # Mise à jour disponible !
                changelog = release.get("body", "Aucune description")
                msg = f"✨ Nouvelle version disponible !\n\n" \
                      f"📦 Version actuelle : {APP_VERSION}\n" \
                      f"🚀 Dernière version : {latest_version}\n\n" \
                      f"📝 Modifications :\n{changelog}\n\n" \
                      f"Voulez-vous télécharger et installer maintenant ?"
                
                resp = messagebox.askyesno("Mise à jour disponible", msg)
                
                if resp:
                    self.after(0, lambda: self._add_activity("📥 Téléchargement...", self.colors["accent_cyan"]))
                    
                    success = download_update(release)
                    
                    if success:
                        self.after(0, lambda: messagebox.showinfo(
                            "✅ Succès",
                            f"Mise à jour v{latest_version} téléchargée !\n\n"
                            f"L'application va redémarrer pour installer les nouveaux fichiers."
                        ))
                        # Fermer l'app → main.py détectera le ZIP et appliquera la mise à jour
                        self.after(1000, self.quit)
                    else:
                        self.after(0, lambda: messagebox.showerror("Erreur", "Échec du téléchargement."))
            else:
                # Déjà à jour
                self.after(0, lambda: messagebox.showinfo(
                    "À jour",
                    f"✅ Vous utilisez la dernière version ({APP_VERSION})."
                ))
        
        # Lancer dans un thread pour ne pas bloquer l'interface
        threading.Thread(target=_do_check, daemon=True).start()
    
    def _version_greater(self, v1: str, v2: str) -> bool:
        """Compare deux versions : retourne True si v1 > v2"""
        try:
            parts1 = [int(x) for x in v1.split(".")]
            parts2 = [int(x) for x in v2.split(".")]
            return parts1 > parts2
        except:
            return False

if __name__ == "__main__":
    app = CRMASMSApp()
    app.mainloop()