#!/usr/bin/env python3
"""
Startskript für den WSB Stock Crawler
Einfacher Einstiegspunkt für die Anwendung
"""

import sys
import os
import subprocess

def check_dependencies():
    """Überprüft ob alle notwendigen Abhängigkeiten installiert sind"""
    try:
        import praw
        import pandas
        import matplotlib
        import seaborn
        import tkinter
        return True
    except ImportError as e:
        print(f"Fehlende Abhängigkeit: {e}")
        print("Bitte installiere die Abhängigkeiten mit: pip install -r requirements.txt")
        return False

def check_env_file():
    """Überprüft ob die .env Datei existiert"""
    if not os.path.exists('.env'):
        print("⚠️  .env Datei nicht gefunden!")
        print("Bitte kopiere .env.example zu .env und füge deine Reddit API-Credentials hinzu.")
        print("Anleitung: https://www.reddit.com/prefs/apps/")
        return False
    return True

def main():
    """Hauptfunktion"""
    print("🚀 WSB Stock Crawler wird gestartet...")
    print("=" * 50)
    
    # Überprüfe Abhängigkeiten
    print("📦 Überprüfe Abhängigkeiten...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ Alle Abhängigkeiten gefunden")
    
    # Überprüfe .env Datei
    print("🔑 Überprüfe Konfiguration...")
    if not check_env_file():
        print("❌ Konfiguration unvollständig")
        print("\nErstelle .env Datei:")
        print("1. Kopiere .env.example zu .env")
        print("2. Bearbeite .env mit deinen Reddit API-Credentials")
        print("3. Starte die Anwendung erneut")
        sys.exit(1)
    print("✅ Konfiguration gefunden")
    
    # Erstelle notwendige Verzeichnisse
    print("📁 Erstelle Verzeichnisse...")
    directories = ['data/results', 'data/analysis', 'logs']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("✅ Verzeichnisse erstellt")
    
    print("=" * 50)
    print("🎯 Starte GUI-Anwendung...")
    print("Tipp: Teste zuerst die Reddit-Verbindung im Konfiguration-Tab!")
    print("=" * 50)
    
    # Starte die GUI-Anwendung
    try:
        from gui_app import main as gui_main
        gui_main()
    except KeyboardInterrupt:
        print("\n👋 Anwendung beendet")
    except Exception as e:
        print(f"❌ Fehler beim Starten der Anwendung: {e}")
        print("Versuche die Anwendung direkt zu starten: python gui_app.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
