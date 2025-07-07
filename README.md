# WSB Stock Analyzer 🚀

[![CI/CD Status](https://img.shields.io/badge/CI%2FCD-passing-brightgreen)](https://github.com/spiral023/wsb-analyzer)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://wsb-analyzer.streamlit.app)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Eine moderne, interaktive Web-Anwendung zur Analyse von Aktienerwähnungen im beliebten Subreddit r/wallstreetbets. Die App crawlt die neuesten Posts und Kommentare, extrahiert Aktiensymbole, analysiert deren Häufigkeit und präsentiert die Ergebnisse in einer übersichtlichen und ansprechenden Oberfläche.

**Live Demo:** [https://wsb-analyzer.streamlit.app](https://wsb-analyzer.streamlit.app)

![Screenshot der App](https://via.placeholder.com/800x400.png?text=WSB+Analyzer+Dashboard)

---

## Inhaltsverzeichnis

- [Über das Projekt](#über-das-projekt)
  - [Technologien](#technologien)
- [Features](#features)
- [Erste Schritte](#erste-schritte)
  - [Voraussetzungen](#voraussetzungen)
  - [Installation & Konfiguration](#installation--konfiguration)
- [Nutzung](#nutzung)
- [Projektstruktur](#projektstruktur)
- [Design und Responsivität](#design-und-responsivität)
- [Lizenz](#lizenz)
- [Kontakt](#kontakt)

---

## Über das Projekt

Der **WSB Stock Analyzer** bietet eine einfache Möglichkeit, die Stimmung und die am häufigsten diskutierten Aktien auf r/wallstreetbets zu verfolgen. Anstatt manuell Hunderte von Posts und Kommentaren zu durchsuchen, automatisiert diese Anwendung den Prozess und liefert wertvolle Einblicke auf einen Blick.

Die Anwendung ist in mehrere Module unterteilt:
- **Reddit Crawler**: Sammelt Daten direkt von der Reddit-API.
- **Data Analyzer**: Verarbeitet die gesammelten Daten, erstellt Statistiken und Visualisierungen.
- **S3 Handler**: Ermöglicht die optionale Speicherung von Ergebnissen und Logs in der Cloud.
- **Streamlit UI**: Eine interaktive und benutzerfreundliche Weboberfläche.

### Technologien

- **[Streamlit](https://streamlit.io/)**: Für die schnelle Entwicklung der interaktiven Web-GUI.
- **[PRAW (Python Reddit API Wrapper)](https://praw.readthedocs.io/en/latest/)**: Für die Kommunikation mit der Reddit-API.
- **[Pandas](https://pandas.pydata.org/)**: Für die Datenmanipulation und -analyse.
- **[Matplotlib](https://matplotlib.org/) & [Seaborn](https://seaborn.pydata.org/)**: Zur Erstellung von Diagrammen und Visualisierungen.
- **[Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)**: Für die optionale Integration mit AWS S3.
- **[python-dotenv](https://github.com/theskumar/python-dotenv)**: Zum Verwalten von Umgebungsvariablen.

---

## Features

- **Dynamisches Crawling**: Crawlt r/wallstreetbets nach den neuesten "Hot"-Posts und deren Kommentaren.
- **Symbol-Extraktion**: Identifiziert und zählt Erwähnungen von US-Aktiensymbolen (z.B. GME, TSLA).
- **Interaktives Dashboard**: Zeigt die Ergebnisse in Echtzeit an.
- **Flexible Konfiguration**: Passen Sie API-Keys, Crawler-Limits und Speichereinstellungen direkt in der App an.
- **Lokale & Cloud-Speicherung**: Speichern Sie Ergebnisse und Logs wahlweise lokal oder in einem AWS S3 Bucket.
- **Datenvisualisierung**: Generiert automatisch Diagramme zu den Top-Aktien, Trends und Erwähnungs-Heatmaps.
- **Session-Management**: Lädt und analysiert vergangene Crawling-Sessions, ideal für Vergleiche über die Zeit.
- **Sicheres Credential-Handling**: Speichert sensible Daten wie API-Keys im Browser LocalStorage oder über Streamlit Secrets.

---

## Erste Schritte

Folgen Sie diesen Schritten, um eine lokale Kopie des Projekts zum Laufen zu bringen.

### Voraussetzungen

- Python 3.9 oder höher
- Git
- Ein Reddit-Konto und API-Anmeldedaten

### Installation & Konfiguration

1.  **Repository klonen**
    ```sh
    git clone https://github.com/spiral023/wsb-analyzer.git
    cd wsb-analyzer
    ```

2.  **Python-Abhängigkeiten installieren**
    Es wird empfohlen, eine virtuelle Umgebung zu verwenden.
    ```sh
    python -m venv venv
    source venv/bin/activate  # Auf Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Reddit API-Anmeldedaten erstellen**
    - Gehen Sie zu [Reddit Apps](https://www.reddit.com/prefs/apps).
    - Klicken Sie auf "Are you a developer? Create an app...".
    - Geben Sie einen Namen an (z.B. "WSB Analyzer"), wählen Sie "script" als App-Typ und setzen Sie `http://localhost:8501` als `redirect uri`.
    - Nach dem Erstellen sehen Sie Ihre `client_id` (unter dem App-Namen) und Ihr `client_secret`.

4.  **Konfigurationsdatei einrichten**
    Die Anwendung kann auf zwei Arten konfiguriert werden:
    - **(A) Über die App-Oberfläche (Empfohlen)**: Starten Sie die App und geben Sie Ihre Anmeldedaten in der Seitenleiste ein. Diese werden sicher im LocalStorage Ihres Browsers gespeichert.
    - **(B) Über eine `.env`-Datei**:
        - Erstellen Sie eine Kopie der `.env.example`-Datei und benennen Sie sie in `.env` um.
        - Tragen Sie Ihre Reddit-API-Daten und optional Ihre AWS-S3-Daten ein.
        ```
        # .env
        # --- Reddit API Credentials ---
        # Erforderlich für den Betrieb der App.
        # Erstellen Sie eine App unter: https://www.reddit.com/prefs/apps
        REDDIT_CLIENT_ID=""
        REDDIT_CLIENT_SECRET=""
        REDDIT_USERNAME=""
        REDDIT_PASSWORD=""

        # --- AWS S3 Configuration (Optional) ---
        # Wenn Sie S3 zur Speicherung verwenden möchten, füllen Sie diese Variablen aus.
        # Andernfalls werden die Daten lokal im 'data/' Verzeichnis gespeichert.
        AWS_ACCESS_KEY_ID=""
        AWS_SECRET_ACCESS_KEY=""
        S3_BUCKET_NAME=""
        AWS_REGION="eu-central-1"

        ```

---

## Nutzung

Starten Sie die Streamlit-Anwendung mit dem folgenden Befehl:

```sh
streamlit run streamlit_app.py
```

Die App öffnet sich automatisch in Ihrem Standardbrowser.

1.  **Konfigurieren**: Öffnen Sie die Seitenleiste und geben Sie Ihre Reddit-API-Daten ein. Klicken Sie auf "Speichern & Testen".
2.  **Anpassen**: Stellen Sie die Anzahl der zu crawlenden Posts und Kommentare ein.
3.  **Starten**: Klicken Sie auf dem Dashboard auf "Crawlen und Analysieren".
4.  **Analysieren**:
    - **Dashboard**: Verfolgen Sie den Fortschritt des Crawling- und Analyseprozesses.
    - **Ergebnisse**: Sehen Sie sich die Rohdaten der letzten Analyse an.
    - **Visualisierungen**: Betrachten Sie die generierten Diagramme.
    - **Logs**: Überprüfen Sie die Log-Dateien für detaillierte Informationen zum Prozess.

![Screenshot der Konfiguration](https://via.placeholder.com/800x300.png?text=Konfiguration+in+der+Seitenleiste)

---

## Projektstruktur

```
wsb-analyzer/
│
├── .streamlit/
│   ├── secrets.example.toml      # Vorlage für Streamlit Secrets
│   └── secrets.toml              # (Optional) Lokale Secrets für Streamlit Cloud
│
├── data/
│   ├── stock_symbols.csv         # Liste der US-Aktiensymbole
│   ├── results/                  # Speicherort für lokale Crawling-Ergebnisse
│   └── analysis/                 # Speicherort für lokale Analyseergebnisse
│
├── logs/                         # Speicherort für lokale Log-Dateien
│
├── .env.example                  # Vorlage für Umgebungsvariablen
├── .gitignore                    # Von Git ignorierte Dateien
├── config.py                     # Zentrale Konfigurationsdatei
├── data_analyzer.py              # Modul für die Datenanalyse
├── reddit_crawler.py             # Modul zum Crawlen von Reddit
├── requirements.txt              # Python-Abhängigkeiten
├── s3_handler.py                 # Modul für AWS S3-Interaktionen
└── streamlit_app.py              # Hauptdatei der Streamlit-Anwendung
```

---

## Design und Responsivität

Die Benutzeroberfläche wurde mit **Streamlit** erstellt, einem Framework, das automatisch für eine saubere und responsive Darstellung auf verschiedenen Geräten sorgt. Das Layout passt sich dynamisch an Desktop- und mobile Ansichten an, um eine optimale Benutzererfahrung zu gewährleisten. Das Design ist bewusst minimalistisch gehalten, um den Fokus auf die Daten und Analysen zu legen.

---

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Weitere Informationen finden Sie in der `LICENSE`-Datei.

---

## Kontakt

Projekt-Link: [https://github.com/spiral023/wsb-analyzer](https://github.com/spiral023/wsb-analyzer)
