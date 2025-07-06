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
    client_id = st.text_input(
        "Client ID", 
        value=localS.getItem("client_id") or "", 
        type="password"
    )
    client_secret = st.text_input(
        "Client Secret", 
        value=localS.getItem("client_secret") or "", 
        type="password"
    )
    username = st.text_input(
        "Username", 
        value=localS.getItem("username") or ""
    )
    password = st.text_input(
        "Password", 
        value=localS.getItem("password") or "", 
        type="password"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Speichern & Testen"):
            # Save credentials to local storage
            localS.setItem("client_id", client_id, key="set_client_id")
            localS.setItem("client_secret", client_secret, key="set_client_secret")
            localS.setItem("username", username, key="set_username")
            localS.setItem("password", password, key="set_password")
            
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
        if st.button("Daten löschen"):
            localS.setItem("client_id", "", key="delete_client_id")
            localS.setItem("client_secret", "", key="delete_client_secret")
            localS.setItem("username", "", key="delete_username")
            localS.setItem("password", "", key="delete_password")
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
        aws_access_key_id = st.text_input("AWS Access Key ID", value=localS.getItem("aws_access_key_id") or "", type="password")
        aws_secret_access_key = st.text_input("AWS Secret Access Key", value=localS.getItem("aws_secret_access_key") or "", type="password")
        s3_bucket_name = st.text_input("S3 Bucket Name", value=localS.getItem("s3_bucket_name") or "")
        aws_region = st.text_input("AWS Region", value=localS.getItem("aws_region") or "eu-central-1")

        if st.button("S3-Konfiguration speichern & testen"):
            # In LocalStorage speichern
            localS.setItem("storage_type", storage_type, key="set_storage_type")
            localS.setItem("aws_access_key_id", aws_access_key_id, key="set_aws_id")
            localS.setItem("aws_secret_access_key", aws_secret_access_key, key="set_aws_secret")
            localS.setItem("s3_bucket_name", s3_bucket_name, key="set_s3_bucket")
            localS.setItem("aws_region", aws_region, key="set_aws_region")

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
    # Wir suchen in 'data/results/', da dort die primären Session-Ordner erstellt werden
    sessions = s3_handler.list_sessions(base_prefix=DATA_PATHS['results_dir'])
    if sessions:
        st.session_state.selected_session = st.sidebar.selectbox(
            "Wähle eine Session",
            options=sessions,
            index=0,
            key="session_selector",
            help="Zeigt Ordner im Format YYYY-MM-DD/HHMMSS/"
        )
    else:
        st.sidebar.info("Keine S3-Sessions gefunden.")

# --- Crawler-Einstellungen ---
st.sidebar.subheader("Crawler-Einstellungen")
post_limit = st.sidebar.slider("Anzahl Posts", 10, 500, 100)
comment_limit = st.sidebar.slider("Kommentare pro Post", 10, 200, 50)


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

    if st.button("Crawlen und Analysieren", disabled=st.session_state.crawling_in_progress or not api_configured):
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
            df = pd.read_csv(io.StringIO(file_content))
            st.dataframe(df)
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

    if st.button("Logs laden"):
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
