# WSB Stock Crawler

Ein Python-Tool mit grafischer Benutzeroberfläche zum Crawlen von r/wallstreetbets nach Aktiensymbolen und zur Analyse der Erwähnungshäufigkeit.

## Features

- **Reddit-Crawling**: Durchsucht Posts und Kommentare in r/wallstreetbets nach Aktiensymbolen
- **Datenanalyse**: Erstellt tabellarische Übersichten und Trends über alle Crawling-Läufe
- **GUI-Interface**: Benutzerfreundliche grafische Oberfläche mit tkinter
- **Visualisierungen**: Diagramme und Charts zur Datenvisualisierung
- **Export-Funktionen**: Speichert Ergebnisse in JSON und CSV-Formaten
- **Konfigurierbar**: Anpassbare Crawler-Parameter

## Installation

### Voraussetzungen

- Python 3.8 oder höher
- Reddit API-Zugang (kostenlos)

### 1. Repository klonen oder herunterladen

```bash
git clone <repository-url>
cd wsb-stock-crawler
```

### 2. Virtuelle Python-Umgebung erstellen (empfohlen)

Eine virtuelle Umgebung isoliert die Projektabhängigkeiten von anderen Python-Projekten:

#### Windows:
```bash
# Virtuelle Umgebung erstellen
python -m venv venv

# Virtuelle Umgebung aktivieren
venv\Scripts\activate

# Zur Deaktivierung später:
# deactivate
```

#### macOS/Linux:
```bash
# Virtuelle Umgebung erstellen
python3 -m venv venv

# Virtuelle Umgebung aktivieren
source venv/bin/activate

# Zur Deaktivierung später:
# deactivate
```

**Wichtig:** Die virtuelle Umgebung muss bei jeder neuen Terminal-Sitzung erneut aktiviert werden!

### 3. Abhängigkeiten installieren

Stelle sicher, dass die virtuelle Umgebung aktiviert ist (du solltest `(venv)` am Anfang deiner Kommandozeile sehen):

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Optional: pip auf neueste Version aktualisieren
pip install --upgrade pip
```

### 4. Reddit API konfigurieren

1. Gehe zu [Reddit Apps](https://www.reddit.com/prefs/apps/)
2. Klicke auf "Create App" oder "Create Another App"
3. Wähle "script" als App-Typ
4. Notiere dir die `client_id` und `client_secret`

5. Kopiere `.env.example` zu `.env`:
```bash
cp .env.example .env
```

6. Bearbeite die `.env` Datei mit deinen Reddit-Credentials:
```
REDDIT_CLIENT_ID=deine_client_id
REDDIT_CLIENT_SECRET=dein_client_secret
REDDIT_USERNAME=dein_reddit_username
REDDIT_PASSWORD=dein_reddit_passwort
```

## Verwendung

**Wichtig:** Stelle sicher, dass die virtuelle Umgebung aktiviert ist, bevor du die Anwendung startest!

### Einfacher Start mit dem Startskript (empfohlen)

```bash
# Virtuelle Umgebung aktivieren (falls noch nicht aktiv)
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Anwendung mit automatischen Checks starten
python run_app.py
```

Das Startskript überprüft automatisch:
- Ob alle Abhängigkeiten installiert sind
- Ob die .env-Datei existiert
- Erstellt notwendige Verzeichnisse
- Startet die GUI-Anwendung

### Manuelle Starts

#### GUI-Anwendung direkt starten:
```bash
python gui_app.py
```

#### Kommandozeilen-Tools

##### Nur Crawling ausführen:
```bash
python reddit_crawler.py
```

##### Nur Datenanalyse ausführen:
```bash
python data_analyzer.py
```

### Erste Schritte nach dem Start

1. **Reddit-Verbindung testen**: Gehe zum "Konfiguration"-Tab und klicke auf "Verbindung testen"
2. **Crawler-Parameter anpassen**: Stelle die gewünschte Anzahl Posts und Kommentare ein
3. **Crawling starten**: Klicke auf "Crawling starten" und warte auf die Ergebnisse
4. **Ergebnisse anzeigen**: Wechsle zum "Ergebnisse"-Tab oder "Visualisierungen"-Tab
5. **Analyse durchführen**: Klicke auf "Analyse starten" für erweiterte Auswertungen

## Projektstruktur

```
wsb-stock-crawler/
├── gui_app.py              # Hauptanwendung mit GUI
├── reddit_crawler.py       # Reddit-Crawler-Modul
├── data_analyzer.py        # Datenanalyse-Modul
├── config.py              # Konfigurationsdatei
├── requirements.txt       # Python-Abhängigkeiten
├── .env.example          # Beispiel-Umgebungsvariablen
├── README.md             # Diese Datei
├── data/
│   ├── stock_symbols.csv # Liste der Aktiensymbole
│   ├── results/          # Crawling-Ergebnisse (JSON/CSV)
│   └── analysis/         # Analyseergebnisse
└── logs/                 # Log-Dateien
```

## Funktionsweise

### 1. Crawler
- Verbindet sich zur Reddit API
- Durchsucht r/wallstreetbets nach Hot Posts
- Extrahiert Aktiensymbole aus Posts und Kommentaren
- Filtert bekannte Aktiensymbole gegen eine vordefinierte Liste
- Zählt Erwähnungshäufigkeiten
- Speichert Ergebnisse mit Zeitstempel

### 2. Analyzer
- Lädt alle gespeicherten Crawling-Ergebnisse
- Erstellt kombinierte Datenanalysen
- Berechnet Trends und Top-Symbole
- Generiert Visualisierungen
- Exportiert Zusammenfassungen

### 3. GUI
- Benutzerfreundliche Oberfläche
- Live-Progress-Anzeige
- Integrierte Visualisierungen
- Export-Funktionen
- Konfigurationsmöglichkeiten

## Konfiguration

### Crawler-Einstellungen (config.py)

```python
CRAWLER_CONFIG = {
    'subreddit': 'wallstreetbets',
    'post_limit': 100,        # Anzahl Posts pro Lauf
    'comment_limit': 50,      # Kommentare pro Post
    'min_symbol_length': 1,   # Min. Symbollänge
    'max_symbol_length': 5,   # Max. Symbollänge
}
```

### Aktiensymbole anpassen

Bearbeite `data/stock_symbols.csv` um die Liste der zu suchenden Aktiensymbole anzupassen.

## Ausgabeformate

### JSON-Ergebnisse
```json
{
  "timestamp": "20240106_143022",
  "crawl_date": "2024-01-06T14:30:22Z",
  "total_symbols_found": 45,
  "total_mentions": 234,
  "subreddit": "wallstreetbets",
  "results": {
    "AAPL": 23,
    "TSLA": 18,
    "GME": 15
  }
}
```

### CSV-Ergebnisse
```csv
Symbol,Mentions,Timestamp,Date
AAPL,23,20240106_143022,2024-01-06 14:30:22
TSLA,18,20240106_143022,2024-01-06 14:30:22
```

## Visualisierungen

Die Anwendung erstellt automatisch:
- Top-Symbole Balkendiagramm
- Zeitliche Trends (Timeline)
- Erwähnungsverteilung
- Trending-Symbole (letzte 7 Tage)
- Heatmap der Top-Symbole über Zeit

## Troubleshooting

### Reddit API-Fehler
- Überprüfe deine API-Credentials in der `.env` Datei
- Stelle sicher, dass dein Reddit-Account aktiv ist
- Teste die Verbindung über die GUI (Konfiguration → Verbindung testen)

### Keine Daten gefunden
- Überprüfe die Internetverbindung
- Stelle sicher, dass r/wallstreetbets erreichbar ist
- Prüfe die Log-Dateien für detaillierte Fehlermeldungen

### Import-Fehler
- Installiere alle Abhängigkeiten: `pip install -r requirements.txt`
- Verwende Python 3.8 oder höher

## Rechtliche Hinweise

- Dieses Tool ist nur für Bildungszwecke gedacht
- Beachte die Reddit API-Nutzungsbedingungen
- Verwende die Daten nicht für kommerzielle Zwecke ohne entsprechende Lizenz
- Die Aktiensymbole dienen nur als Beispiel und stellen keine Anlageberatung dar

## Lizenz

Dieses Projekt ist für Bildungszwecke erstellt. Bitte beachte die entsprechenden API-Nutzungsbedingungen.

## Beitragen

Verbesserungen und Erweiterungen sind willkommen! Bitte erstelle einen Pull Request oder öffne ein Issue.
