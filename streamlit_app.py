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

st.title("📈 WSB Stock Analyzer")
st.markdown("Eine moderne Web-Anwendung zur Analyse von Reddit's r/wallstreetbets.")

# --- Seitenleiste für Konfiguration ---
st.sidebar.header("Konfiguration")

# --- Reddit API Konfiguration ---
with st.sidebar.expander("Reddit API Credentials", expanded=True):
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

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Crawling starten", disabled=st.session_state.crawling_in_progress or not api_configured):
            st.session_state.crawling_in_progress = True
            st.rerun()

    with col2:
        if st.button("Analyse starten", disabled=st.session_state.analysis_in_progress or not st.session_state.crawl_results):
            st.session_state.analysis_in_progress = True
            st.rerun()

    if not api_configured:
        st.warning("Bitte geben Sie Ihre API-Daten in der Seitenleiste ein und klicken Sie auf 'Speichern & Testen'.")

    # Crawling Prozess
    if st.session_state.crawling_in_progress:
        st.header("Crawling...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Konfiguration ist bereits am Anfang des Skripts geladen
        # Setze nur die Crawler-spezifischen Laufzeit-Parameter
        CRAWLER_CONFIG['post_limit'] = post_limit
        CRAWLER_CONFIG['comment_limit'] = comment_limit

        crawler = WSBStockCrawler()
        
        def progress_callback(progress, message):
            progress_bar.progress(int(progress))
            status_text.text(message)

        if crawler.crawl_subreddit(progress_callback):
            st.session_state.crawl_results = crawler.get_crawl_summary()
            crawler.save_results()
            st.success("Crawling erfolgreich abgeschlossen!")
        else:
            st.error("Crawling fehlgeschlagen. Überprüfen Sie die Logs.")
        
        st.session_state.crawling_in_progress = False
        time.sleep(2)
        st.rerun()

    # Analyse Prozess
    if st.session_state.analysis_in_progress:
        st.header("Analyse...")
        with st.spinner("Daten werden analysiert..."):
            analyzer = WSBDataAnalyzer()
            if analyzer.run_full_analysis():
                st.session_state.analysis_summary = analyzer.create_summary_report()
                st.session_state.analysis_plots = analyzer.create_visualizations(save_plots=True)
                st.success("Analyse erfolgreich abgeschlossen!")
            else:
                st.error("Analyse fehlgeschlagen. Überprüfen Sie die Logs.")
        
        st.session_state.analysis_in_progress = False
        time.sleep(2)
        st.rerun()

with tab_results:
    st.header("Ergebnisse")
    if st.session_state.crawl_results:
        st.subheader("Letzter Crawl-Zusammenfassung")
        st.json(st.session_state.crawl_results)

    st.subheader("Neueste Erwähnungen")
    # Lade die neueste CSV-Datei von lokal oder S3
    try:
        latest_file_content = None
        if STORAGE_CONFIG['type'] == 's3' and s3_handler:
            st.info("Lade neueste Ergebnisse von S3...")
            s3_files = s3_handler.list_files(prefix=DATA_PATHS['results_dir'])
            if s3_files:
                csv_files = [f for f in s3_files if f.endswith('.csv')]
                if csv_files:
                    latest_file_key = max(csv_files) # Sortiert nach Name (Zeitstempel)
                    latest_file_content = s3_handler.get_file_content(latest_file_key)
        else:
            st.info("Lade neueste Ergebnisse vom lokalen Speicher...")
            list_of_files = glob.glob(f"{DATA_PATHS['results_dir']}/*.csv")
            if list_of_files:
                latest_file_path = max(list_of_files, key=os.path.getctime)
                with open(latest_file_path, 'r', encoding='utf-8') as f:
                    latest_file_content = f.read()

        if latest_file_content:
            df = pd.read_csv(io.StringIO(latest_file_content))
            st.dataframe(df)
        else:
            st.info("Noch keine Ergebnisdateien gefunden.")
            
    except Exception as e:
        st.warning(f"Konnte keine Ergebnis-Datei laden: {e}")

with tab_visuals:
    st.header("Visualisierungen")
    st.info("Die neueste Analyse-Visualisierung wird geladen...")

    try:
        latest_plot = None
        if STORAGE_CONFIG['type'] == 's3' and s3_handler:
            s3_files = s3_handler.list_files(prefix=DATA_PATHS['analysis_dir'])
            if s3_files:
                plot_files = [f for f in s3_files if f.endswith('.png')]
                if plot_files:
                    latest_plot_key = max(plot_files)
                    # Temporär herunterladen zum Anzeigen
                    temp_plot_path = "temp_plot.png"
                    if s3_handler.download_file(latest_plot_key, temp_plot_path):
                        latest_plot = temp_plot_path
        else:
            list_of_files = glob.glob(f"{DATA_PATHS['analysis_dir']}/*.png")
            if list_of_files:
                latest_plot = max(list_of_files, key=os.path.getctime)

        if latest_plot:
            st.image(latest_plot)
            if os.path.exists("temp_plot.png"):
                os.remove("temp_plot.png") # Aufräumen
        else:
            st.info("Führen Sie zuerst die Analyse durch, um Visualisierungen anzuzeigen.")
    except Exception as e:
        st.error(f"Fehler beim Laden der Visualisierung: {e}")

with tab_logs:
    st.header("Logs")
    log_expander = st.expander("Logs anzeigen")
    with log_expander:
        try:
            with open("logs/crawler.log", "r") as f:
                st.text(f.read())
            with open("logs/analyzer.log", "r") as f:
                st.text(f.read())
        except FileNotFoundError:
            st.text("Noch keine Logs vorhanden.")
