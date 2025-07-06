# WSB Stock Analyzer 🚀

Ein umfassendes Tool zur Analyse von Aktienerwähnungen im Subreddit r/wallstreetbets. Dieses Projekt bietet eine Web-Oberfläche mit Streamlit, um die neuesten Trends zu crawlen, zu analysieren und zu visualisieren.

![Streamlit App Screenshot](https://user-images.githubusercontent.com/12345/placeholder.png) _(Hinweis: Fügen Sie hier einen Screenshot der laufenden Anwendung ein)_

## ✨ Features

- **Reddit Crawler**: Sammelt Posts und Kommentare von r/wallstreetbets und extrahiert Erwähnungen von Aktiensymbolen.
- **Datenanalyse**: Verarbeitet die gesammelten Daten, um Trends, Top-Erwähnungen und historische Daten zu analysieren.
- **Interaktive Web-Oberfläche**: Eine mit Streamlit erstellte, benutzerfreundliche Oberfläche zur Steuerung des Crawlers und zur Anzeige der Ergebnisse.
- **Visualisierungen**: Erstellt Diagramme und Heatmaps, um die Daten verständlich darzustellen.
- **Lokale Speicherung**: Speichert Ergebnisse und Analysen lokal für zukünftige Vergleiche.
- **Sichere Konfiguration**: Speichert Reddit API-Anmeldeinformationen sicher im lokalen Speicher des Browsers.
- **Alternative Desktop-GUI**: Enthält auch eine mit Tkinter erstellte Desktop-Anwendung.

## 🏗️ Architektur

Das Projekt ist modular aufgebaut und besteht aus mehreren Kernkomponenten:

- `reddit_crawler.py`: Verantwortlich für die Verbindung zur Reddit-API und das Sammeln von Daten.
- `data_analyzer.py`: Lädt die gesammelten Daten, führt Analysen durch und erstellt Visualisierungen.
- `streamlit_app.py`: Die empfohlene, moderne Web-Anwendung zur Interaktion mit dem Tool.
- `gui_app.py`: Eine alternative Desktop-Anwendung, die mit Tkinter erstellt wurde.
- `config.py`: Zentrale Konfigurationsdatei für Crawler-Einstellungen und Dateipfade.

## 📋 Voraussetzungen

- Python 3.8+
- Ein Reddit-Konto und API-Anmeldeinformationen.

## 🛠️ Installation & Konfiguration

Folgen Sie diesen Schritten, um das Projekt lokal einzurichten:

**1. Repository klonen**
```bash
git clone https://github.com/spiral023/wsb-analyzer.git
cd wsb-analyzer
```

**2. Abhängigkeiten installieren**
Es wird empfohlen, eine virtuelle Umgebung zu verwenden.
```bash
python -m venv venv
source venv/bin/activate  # Auf Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Reddit API Konfiguration**
Sie benötigen API-Anmeldeinformationen von Reddit, um auf deren Daten zugreifen zu können.

- Gehen Sie zu [Reddit Apps](https://www.reddit.com/prefs/apps) und erstellen Sie eine neue App.
- Wählen Sie den Typ `script`.
- Geben Sie einen Namen und eine `redirect uri` an (z.B. `http://localhost:8501`).
- Kopieren Sie die `client_id` (unter dem App-Namen) und den `client_secret`.

**Für die Streamlit App (empfohlen):**
Die Anmeldeinformationen werden direkt in der Web-Oberfläche eingegeben und sicher im lokalen Speicher Ihres Browsers gespeichert. Sie müssen keine `.env`-Datei manuell erstellen.

**Für die Tkinter Desktop App:**
- Erstellen Sie eine Kopie der `.env.example`-Datei und benennen Sie sie in `.env` um.
```bash
cp .env.example .env
```
- Öffnen Sie die `.env`-Datei und tragen Sie Ihre Reddit-Anmeldeinformationen ein:
```env
REDDIT_CLIENT_ID="Ihre_Client_ID"
REDDIT_CLIENT_SECRET="Ihr_Client_Secret"
REDDIT_USERNAME="Ihr_Reddit_Benutzername"
REDDIT_PASSWORD="Ihr_Reddit_Passwort"
```

## 🚀 Verwendung

### Streamlit Web App (Empfohlen)

Dies ist der einfachste Weg, die Anwendung zu nutzen.

1.  **Starten Sie die Streamlit-App:**
    ```bash
    streamlit run streamlit_app.py
    ```
2.  Öffnen Sie Ihren Webbrowser und navigieren Sie zu der angezeigten lokalen URL (normalerweise `http://localhost:8501`).
3.  **Konfigurieren Sie die API-Daten:**
    - Geben Sie Ihre Reddit-API-Anmeldeinformationen in der Seitenleiste ein.
    - Klicken Sie auf "Speichern & Testen", um die Verbindung zu überprüfen. Die Daten werden sicher im lokalen Speicher Ihres Browsers gespeichert.
4.  **Starten Sie das Crawling:**
    - Passen Sie bei Bedarf die Crawler-Einstellungen in der Seitenleiste an.
    - Klicken Sie im Dashboard auf "Crawling starten".
5.  **Starten Sie die Analyse:**
    - Sobald das Crawling abgeschlossen ist, klicken Sie auf "Analyse starten", um die Daten zu verarbeiten und Visualisierungen zu erstellen.

### Tkinter Desktop App

1.  Stellen Sie sicher, dass Sie die `.env`-Datei wie oben beschrieben konfiguriert haben.
2.  **Starten Sie die GUI-Anwendung:**
    ```bash
    python run_app.py
    ```
    oder
    ```bash
    python gui_app.py
    ```

## 📂 Dateistruktur

```
.
├── .env.example          # Vorlage für die Konfigurationsdatei
├── .gitignore            # Git-Ignore-Datei
├── config.py             # Zentrale Konfiguration
├── data_analyzer.py      # Modul für die Datenanalyse
├── gui_app.py            # Tkinter Desktop-Anwendung
├── README.md             # Diese Datei
├── reddit_crawler.py     # Modul zum Crawlen von Reddit
├── requirements.txt      # Python-Abhängigkeiten
├── run_app.py            # Startskript für die Tkinter-App
├── streamlit_app.py      # Streamlit Web-Anwendung
├── data/                 # Verzeichnis für Daten
│   ├── stock_symbols.csv # Liste der Aktiensymbole
│   ├── analysis/         # Gespeicherte Analyseergebnisse
│   └── results/          # Gespeicherte Crawling-Ergebnisse
└── logs/                 # Log-Dateien
```

## 📄 Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
