import streamlit as st

# set_page_config() muss der erste Streamlit-Befehl sein.
st.set_page_config(
    page_title="WSB Stock Analyzer",
    page_icon="🚀",
    layout="wide"
)

from streamlit_local_storage import LocalStorage
from reddit_crawler import WSBStockCrawler
from data_analyzer import WSBDataAnalyzer
from config import REDDIT_CONFIG, CRAWLER_CONFIG, STORAGE_CONFIG, S3_CONFIG, DATA_PATHS
import time
import pandas as pd
import os
import io
import glob

try:
    import s3_handler
except ImportError as e:
    st.error(f"Fehler beim Import von s3_handler: {e}")
    s3_handler = None

# --- Initialisierung ---
localS = LocalStorage()

# Konfiguration zu Beginn aus dem LocalStorage laden, um den Zustand wiederherzustellen
def load_config_from_storage():
    storage_type = localS.getItem("storage_type") or 'local'
    STORAGE_CONFIG['type'] = storage_type
    
    if storage_type == 's3':
        S3_CONFIG['aws_access_key_id'] = localS.getItem("aws_access_key_id")
        S3_CONFIG['aws_secret_access_key'] = localS.getItem("aws_secret_access_key")
        S3_CONFIG['bucket_name'] = localS.getItem("s3_bucket_name")
        S3_CONFIG['region_name'] = localS.getItem("aws_region")

    REDDIT_CONFIG['client_id'] = localS.getItem("client_id")
    REDDIT_CONFIG['client_secret'] = localS.getItem("client_secret")
    REDDIT_CONFIG['username'] = localS.getItem("username")
    REDDIT_CONFIG['password'] = localS.getItem("password")

load_config_from_storage()

# Initialisiere Session State
if 'crawling_in_progress' not in st.session_state:
    st.session_state.crawling_in_progress = False
if 'analysis_in_progress' not in st.session_state:
    st.session_state.analysis_in_progress = False
if 'crawl_results' not in st.session_state:
    st.session_state.crawl_results = None
if 'analysis_summary' not in st.session_state:
    st.session_state.analysis_summary = None
if 'analysis_plots' not in st.session_state:
    st.session_state.analysis_plots = None
if 'selected_session' not in st.session_state:
    st.session_state.selected_session = None

st.title("📈 WSB Stock Analyzer")
st.markdown("Eine moderne Web-Anwendung zur Analyse von Reddit's r/wallstreetbets.")

# --- Seitenleiste für Konfiguration ---
st.sidebar.header("Konfiguration")

# --- Reddit API Konfiguration ---
with st.sidebar.expander("Reddit API Credentials", expanded=False):
    st.markdown("[Reddit API Settings](https://www.reddit.com/prefs/apps)")

    if st.button("Streamlit Secrets nutzen", key="use_streamlit_secrets"):
        secrets_password = st.text_input("Secrets Passwort", type="password", key="secrets_password_input")
        if secrets_password:
            if secrets_password == st.secrets.get("secrets_password"):
                st.success("Passwort korrekt! Lade Konfiguration aus Streamlit Secrets.")
                
                # Lade Reddit-Daten
                localS.setItem("client_id", st.secrets.get("client_id", ""), key="secret_client_id")
                localS.setItem("client_secret", st.secrets.get("client_secret", ""), key="secret_client_secret")
                localS.setItem("username", st.secrets.get("username", ""), key="secret_username")
                localS.setItem("password", st.secrets.get("password", ""), key="secret_password")

                # Lade Speicher-Daten
                localS.setItem("storage_type", st.secrets.get("storage_type", "local"), key="secret_storage_type")
                if st.secrets.get("storage_type") == 's3':
                    localS.setItem("aws_access_key_id", st.secrets.get("aws_access_key_id", ""), key="secret_aws_id")
                    localS.setItem("aws_secret_access_key", st.secrets.get("aws_secret_access_key", ""), key="secret_aws_secret")
                    localS.setItem("s3_bucket_name", st.secrets.get("s3_bucket_name", ""), key="secret_s3_bucket")
                    localS.setItem("aws_region", st.secrets.get("aws_region", "eu-central-1"), key="secret_aws_region")
                
                load_config_from_storage() # Globale Konfiguration neu laden
                time.sleep(2)
                st.rerun()
            else:
                st.error("Falsches Passwort.")

    client_id = st.text_input(
        "Client ID", 
        value=localS.getItem("client_id") or "", 
        type="password",
        key="reddit_client_id_input"
    )
    client_secret = st.text_input(
        "Client Secret", 
        value=localS.getItem("client_secret") or "", 
        type="password",
        key="reddit_client_secret_input"
    )
    username = st.text_input(
        "Username", 
        value=localS.getItem("username") or "",
        key="reddit_username_input"
    )
    password = st.text_input(
        "Password", 
        value=localS.getItem("password") or "", 
        type="password",
        key="reddit_password_input"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Speichern & Testen", key="save_test_reddit_button"):
            # Save credentials to local storage
            localS.setItem("client_id", client_id, key="ls_client_id")
            localS.setItem("client_secret", client_secret, key="ls_client_secret")
            localS.setItem("username", username, key="ls_username")
            localS.setItem("password", password, key="ls_password")
            
            with st.spinner("Verbindung wird getestet..."):
                # Temporär Konfiguration für den Test überschreiben
                from config import REDDIT_CONFIG
                REDDIT_CONFIG['client_id'] = client_id
                REDDIT_CONFIG['client_secret'] = client_secret
                REDDIT_CONFIG['username'] = username
                REDDIT_CONFIG['password'] = password
                
                crawler = WSBStockCrawler()
                if crawler.connect_to_reddit():
                    st.success("Verbindung erfolgreich!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Verbindung fehlgeschlagen. Bitte überprüfen Sie Ihre Daten.")

    with col2:
        if st.button("Daten löschen", key="delete_reddit_data_button"):
            localS.setItem("client_id", "", key="ls_delete_client_id")
            localS.setItem("client_secret", "", key="ls_delete_client_secret")
            localS.setItem("username", "", key="ls_delete_username")
            localS.setItem("password", "", key="ls_delete_password")
            st.info("Gespeicherte API-Daten gelöscht.")
            time.sleep(2)
            st.rerun()

# --- Speicher-Konfiguration ---
with st.sidebar.expander("Speicher-Konfiguration"):
    storage_type = st.selectbox(
        "Speichertyp",
        ["local", "s3"],
        index=0 if (localS.getItem("storage_type") or "local") == "local" else 1,
        key="storage_type_selector"
    )

    if storage_type == 's3':
        aws_access_key_id = st.text_input("AWS Access Key ID", value=localS.getItem("aws_access_key_id") or "", type="password", key="aws_access_key_id_input")
        aws_secret_access_key = st.text_input("AWS Secret Access Key", value=localS.getItem("aws_secret_access_key") or "", type="password", key="aws_secret_access_key_input")
        s3_bucket_name = st.text_input("S3 Bucket Name, z.B. arn:aws:s3:::<bucket-name>", value=localS.getItem("s3_bucket_name") or "", key="s3_bucket_name_input")
        aws_region = st.text_input("AWS Region, z.B. eu-west-1", value=localS.getItem("aws_region") or "eu-central-1", key="aws_region_input")

        if st.button("S3-Konfiguration speichern & testen", key="save_test_s3_button"):
            # In LocalStorage speichern
            localS.setItem("storage_type", storage_type, key="ls_storage_type")
            localS.setItem("aws_access_key_id", aws_access_key_id, key="ls_aws_id")
            localS.setItem("aws_secret_access_key", aws_secret_access_key, key="ls_aws_secret")
            localS.setItem("s3_bucket_name", s3_bucket_name, key="ls_s3_bucket")
            localS.setItem("aws_region", aws_region, key="ls_aws_region")

            # Konfiguration zur Laufzeit aktualisieren und sofort laden
            load_config_from_storage()
            
            with st.spinner("Teste S3-Verbindung..."):
                if s3_handler and s3_handler.get_s3_client():
                    st.success("S3-Verbindung erfolgreich!")
                else:
                    st.error("S3-Verbindung fehlgeschlagen. Überprüfen Sie Ihre Daten.")
                time.sleep(2)
                st.rerun()
    else:
        # Wenn local gewählt wird, auch speichern
        if storage_type != localS.getItem("storage_type"):
             localS.setItem("storage_type", "local")
             STORAGE_CONFIG['type'] = "local"
             st.info("Speichertyp auf 'local' gesetzt.")
             time.sleep(1)
             st.rerun()

# --- Session-Auswahl für S3 ---
if STORAGE_CONFIG['type'] == 's3' and s3_handler:
    st.sidebar.subheader("S3 Session-Auswahl")
    if st.sidebar.button("S3 Sessions laden", key="load_s3_sessions_button"):
        # Wir suchen in 'data/results/', da dort die primären Session-Ordner erstellt werden
        sessions = s3_handler.list_sessions(base_prefix=DATA_PATHS['results_dir'])
        if sessions:
            st.session_state.s3_sessions = sessions
        else:
            st.session_state.s3_sessions = []
            st.sidebar.info("Keine S3-Sessions gefunden.")

    if 's3_sessions' in st.session_state and st.session_state.s3_sessions:
        st.session_state.selected_session = st.sidebar.selectbox(
            "Wähle eine Session",
            options=st.session_state.s3_sessions,
            index=0,
            key="session_selector",
            help="Zeigt Ordner im Format YYYY-MM-DD/HHMMSS/"
        )
    elif 's3_sessions' in st.session_state:
        st.sidebar.info("Keine S3-Sessions gefunden.")

# --- Crawler-Einstellungen ---
st.sidebar.subheader("Crawler-Einstellungen")
post_limit = st.sidebar.slider("Anzahl Posts", 10, 500, 100, key="post_limit_slider")
comment_limit = st.sidebar.slider("Kommentare pro Post", 10, 200, 50, key="comment_limit_slider")

st.sidebar.markdown("---")
st.sidebar.markdown("Built by sp23")

# --- Konfiguration Import/Export ---
st.sidebar.subheader("Konfiguration Import/Export")

def get_all_config_from_local_storage():
    config_data = {}
    # Reddit API
    config_data['client_id'] = localS.getItem("client_id")
    config_data['client_secret'] = localS.getItem("client_secret")
    config_data['username'] = localS.getItem("username")
    config_data['password'] = localS.getItem("password")
    # Storage
    config_data['storage_type'] = localS.getItem("storage_type")
    config_data['aws_access_key_id'] = localS.getItem("aws_access_key_id")
    config_data['aws_secret_access_key'] = localS.getItem("aws_secret_access_key")
    config_data['s3_bucket_name'] = localS.getItem("s3_bucket_name")
    config_data['aws_region'] = localS.getItem("aws_region")
    return config_data

def set_all_config_to_local_storage(config_data):
    # Reddit API
    localS.setItem("client_id", config_data.get('client_id', ''), key="import_client_id")
    localS.setItem("client_secret", config_data.get('client_secret', ''), key="import_client_secret")
    localS.setItem("username", config_data.get('username', ''), key="import_username")
    localS.setItem("password", config_data.get('password', ''), key="import_password")
    # Storage
    localS.setItem("storage_type", config_data.get('storage_type', 'local'), key="import_storage_type")
    localS.setItem("aws_access_key_id", config_data.get('aws_access_key_id', ''), key="import_aws_access_key_id")
    localS.setItem("aws_secret_access_key", config_data.get('aws_secret_access_key', ''), key="import_aws_secret_access_key")
    localS.setItem("s3_bucket_name", config_data.get('s3_bucket_name', ''), key="import_s3_bucket_name")
    localS.setItem("aws_region", config_data.get('aws_region', 'eu-central-1'), key="import_aws_region")
    load_config_from_storage() # Reload global config after setting local storage

import json

with st.sidebar.expander("Konfiguration Import/Export"):
    if st.button("Konfiguration exportieren", key="export_config_button"):
        config_to_export = get_all_config_from_local_storage()
        json_string = json.dumps(config_to_export, indent=4)
        st.download_button(
            label="Konfiguration herunterladen",
            data=json_string,
            file_name="wsb_analyzer_config.json",
            mime="application/json",
            key="download_config_button"
        )

    uploaded_file = st.file_uploader("Konfiguration importieren", type="json", key="upload_config_uploader")
    if uploaded_file is not None:
        try:
            config_data = json.load(uploaded_file)
            set_all_config_to_local_storage(config_data)
            st.success("Konfiguration erfolgreich importiert! Bitte laden Sie die Seite neu, um die Änderungen zu sehen.")
            time.sleep(2)
            # st.rerun() # Verursacht die Endlosschleife
        except Exception as e:
            st.error(f"Fehler beim Import der Konfiguration: {e}")

# --- Hauptbereich ---
tab_dashboard, tab_results, tab_visuals, tab_logs = st.tabs(["📊 Dashboard", "📋 Ergebnisse", "📈 Visualisierungen", "📜 Logs"])

with tab_dashboard:
    st.header("Dashboard")

    # Überprüfe ob API-Daten vorhanden sind
    api_configured = all([
        localS.getItem("client_id"),
        localS.getItem("client_secret"),
        localS.getItem("username"),
        localS.getItem("password")
    ])

    if st.button("Crawlen und Analysieren", disabled=st.session_state.crawling_in_progress or not api_configured, key="crawl_analyze_button"):
        st.session_state.crawling_in_progress = True
        st.rerun()

    if not api_configured:
        st.warning("Bitte geben Sie Ihre API-Daten in der Seitenleiste ein und klicken Sie auf 'Speichern & Testen'.")

    # Gekoppelter Crawling- und Analyse-Prozess
    if st.session_state.crawling_in_progress:
        st.header("Crawling & Analyse...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # --- Crawling-Phase ---
        status_text.text("Phase 1: Crawling wird gestartet...")
        CRAWLER_CONFIG['post_limit'] = post_limit
        CRAWLER_CONFIG['comment_limit'] = comment_limit
        crawler = WSBStockCrawler()
        
        def progress_callback(progress, message):
            # Skaliere den Crawling-Fortschritt auf 50% der Gesamtleiste
            progress_bar.progress(int(progress / 2))
            status_text.text(f"Phase 1: Crawling... ({message})")

        crawl_success = crawler.crawl_subreddit(progress_callback)
        
        if crawl_success:
            st.session_state.crawl_results = crawler.get_crawl_summary()
            status_text.text("Phase 1: Crawling abgeschlossen. Speichere Ergebnisse...")
            crawler.save_results()
            st.success("Crawling erfolgreich abgeschlossen!")
            
            # --- Analyse-Phase ---
            progress_bar.progress(50)
            status_text.text("Phase 2: Analyse wird gestartet...")
            
            # Holen des gerade erstellten Session-Pfads
            session_to_analyze = crawler.session_path
            
            with st.spinner(f"Analysiere Daten für neue Session '{session_to_analyze}'..."):
                analyzer = WSBDataAnalyzer()
                if analyzer.run_full_analysis(session_path=session_to_analyze):
                    st.session_state.analysis_summary = analyzer.create_summary_report()
                    st.session_state.analysis_plots = analyzer.create_visualizations(save_plots=True)
                    progress_bar.progress(100)
                    st.success("Analyse erfolgreich abgeschlossen!")
                else:
                    st.error("Analyse fehlgeschlagen. Überprüfen Sie die Logs.")
        else:
            st.error("Crawling fehlgeschlagen. Überprüfen Sie die Logs.")
        
        st.session_state.crawling_in_progress = False
        time.sleep(3)
        st.rerun()

with tab_results:
    st.header("Ergebnisse")
    if st.session_state.crawl_results:
        st.subheader("Letzter Crawl-Zusammenfassung")
        st.json(st.session_state.crawl_results)

    st.subheader("Erwähnungen der ausgewählten Session")
    try:
        # Lade die Stock-Symbole für die Anreicherung
        try:
            stock_symbols_df = pd.read_csv(DATA_PATHS['stock_symbols'])
        except FileNotFoundError:
            st.error(f"Stock-Symbol-Datei nicht gefunden unter: {DATA_PATHS['stock_symbols']}")
            stock_symbols_df = pd.DataFrame() # Leerer DataFrame, um Fehler zu vermeiden

        file_content = None
        if STORAGE_CONFIG['type'] == 's3' and s3_handler:
            if st.session_state.selected_session:
                st.info(f"Lade Ergebnisse für Session {st.session_state.selected_session} von S3...")
                file_key = f"{DATA_PATHS['results_dir']}{st.session_state.selected_session}wsb_mentions.csv"
                file_content = s3_handler.get_file_content(file_key)
            else:
                st.info("Bitte wählen Sie eine S3-Session in der Seitenleiste aus.")
        else:
            st.info("Lade neueste Ergebnisse vom lokalen Speicher...")
            # Lokale Logik: Finde die neueste Datei im verschachtelten Verzeichnis
            list_of_files = glob.glob(f"{DATA_PATHS['results_dir']}/**/wsb_mentions.csv", recursive=True)
            if list_of_files:
                latest_file_path = max(list_of_files, key=os.path.getctime)
                with open(latest_file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()

        if file_content:
            mentions_df = pd.read_csv(io.StringIO(file_content))
            
            # Anreichern der Daten
            if not stock_symbols_df.empty:
                # Annahme: Die Spalte in wsb_mentions.csv heißt 'Symbol'
                if 'Symbol' in mentions_df.columns and 'Symbol' in stock_symbols_df.columns:
                    merged_df = pd.merge(mentions_df, stock_symbols_df, on='Symbol', how='left')
                    st.dataframe(merged_df)
                else:
                    st.warning("Die Spalte 'Symbol' wurde nicht in beiden Dateien gefunden. Zeige unbearbeitete Daten.")
                    st.dataframe(mentions_df)
            else:
                st.dataframe(mentions_df)
        else:
            st.info("Noch keine Ergebnisdateien gefunden.")
            
    except Exception as e:
        st.warning(f"Konnte keine Ergebnis-Datei laden: {e}")

with tab_visuals:
    st.header("Visualisierungen")
    
    try:
        plot_path = None
        if STORAGE_CONFIG['type'] == 's3' and s3_handler:
            if st.session_state.selected_session:
                st.info(f"Lade Visualisierung für Session {st.session_state.selected_session} von S3...")
                plot_key = f"{DATA_PATHS['analysis_dir']}{st.session_state.selected_session}wsb_analysis_plots.png"
                temp_plot_path = "temp_plot.png"
                if s3_handler.download_file(plot_key, temp_plot_path):
                    plot_path = temp_plot_path
                else:
                    st.warning(f"Visualisierung für Session {st.session_state.selected_session} nicht gefunden.")
            else:
                st.info("Bitte wählen Sie eine S3-Session in der Seitenleiste aus.")
        else:
            st.info("Lade neueste Visualisierung vom lokalen Speicher...")
            list_of_files = glob.glob(f"{DATA_PATHS['analysis_dir']}/**/wsb_analysis_plots.png", recursive=True)
            if list_of_files:
                plot_path = max(list_of_files, key=os.path.getctime)

        if plot_path:
            st.image(plot_path)
            if os.path.exists("temp_plot.png"):
                os.remove("temp_plot.png") # Aufräumen
        else:
            st.info("Führen Sie zuerst die Analyse durch, um Visualisierungen anzuzeigen.")
    except Exception as e:
        st.error(f"Fehler beim Laden der Visualisierung: {e}")

with tab_logs:
    st.header("Logs der ausgewählten Session")

    if st.button("Logs laden", key="load_logs_button"):
        session = st.session_state.get('selected_session')
        if not session:
            st.warning("Bitte wählen Sie zuerst eine Session in der Seitenleiste aus.")
        else:
            st.info(f"Lade Logs für Session: {session}")
            
            log_contents = {}
            
            if STORAGE_CONFIG['type'] == 's3' and s3_handler:
                # Lade von S3
                crawler_log_key = f"{DATA_PATHS['results_dir']}{session}crawler.log"
                analyzer_log_key = f"{DATA_PATHS['analysis_dir']}{session}analyzer.log"
                
                log_contents['crawler'] = s3_handler.get_file_content(crawler_log_key)
                log_contents['analyzer'] = s3_handler.get_file_content(analyzer_log_key)
            else:
                # Lade lokal
                crawler_log_path = os.path.join(DATA_PATHS['results_dir'], session.replace('/', os.sep), "crawler.log")
                analyzer_log_path = os.path.join(DATA_PATHS['analysis_dir'], session.replace('/', os.sep), "analyzer.log")
                
                try:
                    with open(crawler_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        log_contents['crawler'] = f.read()
                except FileNotFoundError:
                    log_contents['crawler'] = "Crawler-Log für diese Session nicht gefunden."
                
                try:
                    with open(analyzer_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        log_contents['analyzer'] = f.read()
                except FileNotFoundError:
                    log_contents['analyzer'] = "Analyzer-Log für diese Session nicht gefunden."

            # Anzeige der Logs
            st.subheader("Crawler Log")
            st.text_area("Crawler Log Content", value=log_contents.get('crawler') or "Kein Inhalt.", height=300)
            
            st.subheader("Analyzer Log")
            st.text_area("Analyzer Log Content", value=log_contents.get('analyzer') or "Kein Inhalt.", height=300)
