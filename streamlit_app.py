import streamlit as st
from streamlit_local_storage import LocalStorage
from reddit_crawler import WSBStockCrawler
from data_analyzer import WSBDataAnalyzer
from config import REDDIT_CONFIG, CRAWLER_CONFIG
import time
import pandas as pd

# --- Initialisierung ---
localS = LocalStorage()

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

st.set_page_config(
    page_title="WSB Stock Analyzer",
    page_icon="🚀",
    layout="wide"
)

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
        
        # Setze API-Daten und Crawler-Konfiguration
        REDDIT_CONFIG['client_id'] = localS.getItem("client_id")
        REDDIT_CONFIG['client_secret'] = localS.getItem("client_secret")
        REDDIT_CONFIG['username'] = localS.getItem("username")
        REDDIT_CONFIG['password'] = localS.getItem("password")
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
    # Lade die neueste CSV-Datei
    try:
        import glob
        import os
        list_of_files = glob.glob('data/results/*.csv')
        if list_of_files:
            latest_file = max(list_of_files, key=os.path.getctime)
            df = pd.read_csv(latest_file)
            st.dataframe(df)
    except Exception as e:
        st.warning(f"Konnte keine Ergebnis-Datei laden: {e}")

with tab_visuals:
    st.header("Visualisierungen")
    if st.session_state.analysis_plots:
        st.pyplot(st.session_state.analysis_plots)
    else:
        st.info("Führen Sie zuerst die Analyse durch, um Visualisierungen anzuzeigen.")

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
