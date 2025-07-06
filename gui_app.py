"""
GUI-Anwendung für den WSB Stock Crawler
Hauptanwendung mit grafischer Benutzeroberfläche
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import queue
import json
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

from reddit_crawler import WSBStockCrawler
from data_analyzer import WSBDataAnalyzer
from config import GUI_CONFIG, REDDIT_CONFIG, CRAWLER_CONFIG, DATA_PATHS

class WSBCrawlerGUI:
    def __init__(self, root):
        """Initialisiert die GUI-Anwendung"""
        self.root = root
        self.setup_window()
        self.setup_variables()
        self.setup_widgets()
        self.setup_menu()
        
        # Threading für Crawler
        self.crawler_thread = None
        self.analyzer_thread = None
        self.progress_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # Instanzen
        self.crawler = WSBStockCrawler()
        self.analyzer = WSBDataAnalyzer()
        
        # Starte Queue-Monitoring
        self.check_queues()
        
    def setup_window(self):
        """Konfiguriert das Hauptfenster"""
        self.root.title(GUI_CONFIG['window_title'])
        self.root.geometry(GUI_CONFIG['window_size'])
        self.root.minsize(800, 600)
        
        # Icon setzen (falls vorhanden)
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
            
    def setup_variables(self):
        """Initialisiert die GUI-Variablen"""
        self.is_crawling = tk.BooleanVar(value=False)
        self.is_analyzing = tk.BooleanVar(value=False)
        self.progress_var = tk.DoubleVar(value=0)
        self.status_var = tk.StringVar(value="Bereit")
        self.post_limit_var = tk.IntVar(value=CRAWLER_CONFIG['post_limit'])
        self.comment_limit_var = tk.IntVar(value=CRAWLER_CONFIG['comment_limit'])
        
    def setup_widgets(self):
        """Erstellt die GUI-Widgets"""
        # Hauptcontainer
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Konfiguriere Grid-Gewichte
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Titel
        title_label = ttk.Label(main_frame, text="WSB Stock Crawler", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Konfigurationsbereich
        config_frame = ttk.LabelFrame(main_frame, text="Crawler-Konfiguration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Post Limit
        ttk.Label(config_frame, text="Anzahl Posts:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        post_limit_spin = ttk.Spinbox(config_frame, from_=10, to=500, width=10, 
                                     textvariable=self.post_limit_var)
        post_limit_spin.grid(row=0, column=1, sticky=tk.W)
        
        # Comment Limit
        ttk.Label(config_frame, text="Kommentare pro Post:").grid(row=0, column=2, sticky=tk.W, padx=(20, 10))
        comment_limit_spin = ttk.Spinbox(config_frame, from_=10, to=200, width=10,
                                        textvariable=self.comment_limit_var)
        comment_limit_spin.grid(row=0, column=3, sticky=tk.W)
        
        # Steuerungsbereich
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=3, pady=(0, 10))
        
        # Buttons
        self.crawl_button = ttk.Button(control_frame, text="Crawling starten", 
                                      command=self.start_crawling, width=15)
        self.crawl_button.grid(row=0, column=0, padx=(0, 10))
        
        self.analyze_button = ttk.Button(control_frame, text="Analyse starten", 
                                        command=self.start_analysis, width=15)
        self.analyze_button.grid(row=0, column=1, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stoppen", 
                                     command=self.stop_operations, width=15,
                                     state=tk.DISABLED)
        self.stop_button.grid(row=0, column=2, padx=(0, 10))
        
        self.view_results_button = ttk.Button(control_frame, text="Ergebnisse anzeigen", 
                                             command=self.view_results, width=15)
        self.view_results_button.grid(row=0, column=3)
        
        # Progress Bar und Status
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=1)
        
        # Notebook für Tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tab 1: Log-Ausgabe
        self.setup_log_tab()
        
        # Tab 2: Ergebnisse
        self.setup_results_tab()
        
        # Tab 3: Visualisierungen
        self.setup_visualization_tab()
        
        # Tab 4: Konfiguration
        self.setup_config_tab()
        
    def setup_log_tab(self):
        """Erstellt den Log-Tab"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Log")
        
        # Log-Text-Widget
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log-Buttons
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(log_button_frame, text="Log leeren", 
                  command=self.clear_log).pack(side=tk.LEFT)
        ttk.Button(log_button_frame, text="Log speichern", 
                  command=self.save_log).pack(side=tk.LEFT, padx=(10, 0))
        
    def setup_results_tab(self):
        """Erstellt den Ergebnisse-Tab"""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="Ergebnisse")
        
        # Treeview für Ergebnisse
        columns = ('Symbol', 'Mentions', 'Datum', 'Zeit')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        # Spalten konfigurieren
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=100)
            
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid Layout
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Buttons für Ergebnisse
        results_button_frame = ttk.Frame(results_frame)
        results_button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(results_button_frame, text="Aktualisieren", 
                  command=self.refresh_results).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(results_button_frame, text="Exportieren", 
                  command=self.export_results).pack(side=tk.LEFT)
        
    def setup_visualization_tab(self):
        """Erstellt den Visualisierungs-Tab"""
        viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(viz_frame, text="Visualisierungen")
        
        # Matplotlib-Canvas
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.suptitle('WSB Stock Analysis')
        
        self.canvas = FigureCanvasTkAgg(self.fig, viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Buttons für Visualisierungen
        viz_button_frame = ttk.Frame(viz_frame)
        viz_button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(viz_button_frame, text="Diagramme aktualisieren", 
                  command=self.update_visualizations).pack(side=tk.LEFT, padx=10)
        ttk.Button(viz_button_frame, text="Diagramme speichern", 
                  command=self.save_visualizations).pack(side=tk.LEFT, padx=10)
        
    def setup_config_tab(self):
        """Erstellt den Konfigurations-Tab"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="Konfiguration")
        
        # Reddit API Konfiguration
        api_frame = ttk.LabelFrame(config_frame, text="Reddit API Konfiguration", padding="10")
        api_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # API Status
        self.api_status_var = tk.StringVar(value="Nicht verbunden")
        ttk.Label(api_frame, text="API Status:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(api_frame, textvariable=self.api_status_var, foreground="red").grid(row=0, column=1, sticky=tk.W)
        
        ttk.Button(api_frame, text="Verbindung testen", 
                  command=self.test_reddit_connection).grid(row=0, column=2, padx=(10, 0))
        
        # Pfad-Konfiguration
        paths_frame = ttk.LabelFrame(config_frame, text="Dateipfade", padding="10")
        paths_frame.pack(fill=tk.X, padx=10, pady=10)
        
        for i, (key, path) in enumerate(DATA_PATHS.items()):
            ttk.Label(paths_frame, text=f"{key}:").grid(row=i, column=0, sticky=tk.W)
            ttk.Label(paths_frame, text=path, foreground="blue").grid(row=i, column=1, sticky=tk.W, padx=(10, 0))
            
    def setup_menu(self):
        """Erstellt die Menüleiste"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Datei-Menü
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Ergebnisse laden", command=self.load_results)
        file_menu.add_command(label="Konfiguration laden", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.quit)
        
        # Tools-Menü
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Datenverzeichnis öffnen", command=self.open_data_directory)
        tools_menu.add_command(label="Log-Verzeichnis öffnen", command=self.open_log_directory)
        
        # Hilfe-Menü
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hilfe", menu=help_menu)
        help_menu.add_command(label="Über", command=self.show_about)
        
    def log_message(self, message):
        """Fügt eine Nachricht zum Log hinzu"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
    def clear_log(self):
        """Leert das Log"""
        self.log_text.delete(1.0, tk.END)
        
    def save_log(self):
        """Speichert das Log in eine Datei"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Erfolg", f"Log gespeichert: {filename}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")
                
    def start_crawling(self):
        """Startet den Crawling-Prozess"""
        if self.is_crawling.get():
            return
            
        # Aktualisiere Konfiguration
        CRAWLER_CONFIG['post_limit'] = self.post_limit_var.get()
        CRAWLER_CONFIG['comment_limit'] = self.comment_limit_var.get()
        
        self.is_crawling.set(True)
        self.crawl_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.status_var.set("Crawling gestartet...")
        
        self.log_message("Starte Crawling-Prozess...")
        
        # Starte Crawler in separatem Thread
        self.crawler_thread = threading.Thread(target=self.run_crawler, daemon=True)
        self.crawler_thread.start()
        
    def run_crawler(self):
        """Führt den Crawler aus (in separatem Thread)"""
        try:
            def progress_callback(progress, message):
                self.progress_queue.put(('progress', progress, message))
                
            # Verbinde zu Reddit
            if not self.crawler.connect_to_reddit():
                self.result_queue.put(('error', 'Fehler bei Reddit-Verbindung'))
                return
                
            # Starte Crawling
            success = self.crawler.crawl_subreddit(progress_callback)
            
            if success:
                # Speichere Ergebnisse
                json_file, csv_file = self.crawler.save_results()
                
                if json_file:
                    summary = self.crawler.get_crawl_summary()
                    self.result_queue.put(('success', 'Crawling erfolgreich abgeschlossen', summary))
                else:
                    self.result_queue.put(('error', 'Fehler beim Speichern der Ergebnisse'))
            else:
                self.result_queue.put(('error', 'Crawling fehlgeschlagen'))
                
        except Exception as e:
            self.result_queue.put(('error', f'Unerwarteter Fehler: {e}'))
            
    def start_analysis(self):
        """Startet die Datenanalyse"""
        if self.is_analyzing.get():
            return
            
        self.is_analyzing.set(True)
        self.analyze_button.config(state=tk.DISABLED)
        self.status_var.set("Analyse gestartet...")
        
        self.log_message("Starte Datenanalyse...")
        
        # Starte Analyzer in separatem Thread
        self.analyzer_thread = threading.Thread(target=self.run_analyzer, daemon=True)
        self.analyzer_thread.start()
        
    def run_analyzer(self):
        """Führt die Analyse aus (in separatem Thread)"""
        try:
            success = self.analyzer.run_full_analysis()
            
            if success:
                summary = self.analyzer.create_summary_report()
                self.result_queue.put(('analysis_success', 'Analyse erfolgreich abgeschlossen', summary))
            else:
                self.result_queue.put(('error', 'Analyse fehlgeschlagen'))
                
        except Exception as e:
            self.result_queue.put(('error', f'Fehler bei der Analyse: {e}'))
            
    def stop_operations(self):
        """Stoppt laufende Operationen"""
        self.is_crawling.set(False)
        self.is_analyzing.set(False)
        self.crawl_button.config(state=tk.NORMAL)
        self.analyze_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Gestoppt")
        self.log_message("Operationen gestoppt")
        
    def check_queues(self):
        """Überprüft die Queues für Updates"""
        # Progress Queue
        try:
            while True:
                msg_type, *args = self.progress_queue.get_nowait()
                if msg_type == 'progress':
                    progress, message = args
                    self.progress_var.set(progress)
                    self.status_var.set(message)
        except queue.Empty:
            pass
            
        # Result Queue
        try:
            while True:
                msg_type, *args = self.result_queue.get_nowait()
                
                if msg_type == 'success':
                    message, summary = args
                    self.log_message(f"✓ {message}")
                    self.show_crawl_summary(summary)
                    self.stop_operations()
                    self.refresh_results()
                    
                elif msg_type == 'analysis_success':
                    message, summary = args
                    self.log_message(f"✓ {message}")
                    self.show_analysis_summary(summary)
                    self.is_analyzing.set(False)
                    self.analyze_button.config(state=tk.NORMAL)
                    self.update_visualizations()
                    
                elif msg_type == 'error':
                    error_message = args[0]
                    self.log_message(f"✗ {error_message}")
                    messagebox.showerror("Fehler", error_message)
                    self.stop_operations()
                    
        except queue.Empty:
            pass
            
        # Plane nächste Überprüfung
        self.root.after(100, self.check_queues)
        
    def show_crawl_summary(self, summary):
        """Zeigt eine Zusammenfassung des Crawlings"""
        if not summary:
            return
            
        message = f"""Crawling abgeschlossen!

Gesamte Erwähnungen: {summary.get('total_mentions', 0)}
Einzigartige Symbole: {summary.get('unique_symbols', 0)}
Top Symbol: {summary.get('top_symbol', ['N/A', 0])[0]} ({summary.get('top_symbol', ['N/A', 0])[1]} Erwähnungen)
Zeit: {summary.get('crawl_time', 'N/A')}"""
        
        messagebox.showinfo("Crawling abgeschlossen", message)
        
    def show_analysis_summary(self, summary):
        """Zeigt eine Zusammenfassung der Analyse"""
        if not summary:
            return
            
        message = f"""Analyse abgeschlossen!

Gesamte Crawls: {summary.get('total_crawls', 0)}
Einzigartige Symbole: {summary.get('unique_symbols', 0)}
Gesamte Erwähnungen: {summary.get('total_mentions', 0)}
Zeitraum: {summary.get('date_range', 'N/A')}"""
        
        messagebox.showinfo("Analyse abgeschlossen", message)
        
    def refresh_results(self):
        """Aktualisiert die Ergebnisanzeige"""
        # Leere aktuelle Ergebnisse
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        try:
            # Lade neueste Ergebnisse
            import glob
            json_files = glob.glob(f"{DATA_PATHS['results_dir']}/*.json")
            
            if not json_files:
                return
                
            # Sortiere nach Datum (neueste zuerst)
            json_files.sort(reverse=True)
            
            # Lade die neuesten 5 Dateien
            for json_file in json_files[:5]:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    crawl_date = data.get('crawl_date', '')
                    timestamp = data.get('timestamp', '')
                    
                    # Parse Datum
                    try:
                        if crawl_date:
                            date_obj = datetime.fromisoformat(crawl_date.replace('Z', '+00:00'))
                            date_str = date_obj.strftime("%Y-%m-%d")
                            time_str = date_obj.strftime("%H:%M:%S")
                        else:
                            date_str = timestamp[:8]
                            time_str = timestamp[9:]
                    except:
                        date_str = "N/A"
                        time_str = "N/A"
                        
                    # Füge Top-Ergebnisse hinzu
                    results = data.get('results', {})
                    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
                    
                    for symbol, mentions in sorted_results[:20]:  # Top 20
                        self.results_tree.insert('', tk.END, values=(symbol, mentions, date_str, time_str))
                        
                except Exception as e:
                    self.log_message(f"Fehler beim Laden von {json_file}: {e}")
                    
        except Exception as e:
            self.log_message(f"Fehler beim Aktualisieren der Ergebnisse: {e}")
            
    def export_results(self):
        """Exportiert die Ergebnisse"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Sammle alle Daten aus der Treeview
                data = []
                for item in self.results_tree.get_children():
                    values = self.results_tree.item(item)['values']
                    data.append(values)
                    
                # Erstelle DataFrame und speichere
                df = pd.DataFrame(data, columns=['Symbol', 'Mentions', 'Datum', 'Zeit'])
                df.to_csv(filename, index=False)
                
                messagebox.showinfo("Erfolg", f"Ergebnisse exportiert: {filename}")
                
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Exportieren: {e}")
                
    def update_visualizations(self):
        """Aktualisiert die Visualisierungen"""
        try:
            # Lade Analyzer-Daten
            if not self.analyzer.load_all_results():
                self.log_message("Keine Daten für Visualisierung verfügbar")
                return
                
            if not self.analyzer.create_combined_dataframe():
                self.log_message("Fehler beim Erstellen des DataFrames")
                return
                
            # Leere aktuelle Plots
            for ax in self.axes.flat:
                ax.clear()
                
            # Erstelle neue Plots
            df = self.analyzer.combined_df
            
            if df is not None and not df.empty:
                # Top 10 Symbole
                top_symbols = self.analyzer.get_top_symbols_overall(10)
                if not top_symbols.empty:
                    self.axes[0, 0].barh(top_symbols['Symbol'], top_symbols['Mentions'])
                    self.axes[0, 0].set_title('Top 10 Symbole')
                    self.axes[0, 0].set_xlabel('Erwähnungen')
                    
                # Timeline
                daily_mentions = df.groupby('Date')['Mentions'].sum().reset_index()
                if not daily_mentions.empty:
                    self.axes[0, 1].plot(daily_mentions['Date'], daily_mentions['Mentions'], marker='o')
                    self.axes[0, 1].set_title('Tägliche Erwähnungen')
                    self.axes[0, 1].tick_params(axis='x', rotation=45)
                    
                # Verteilung
                mention_counts = df['Mentions'].value_counts().head(15)
                if not mention_counts.empty:
                    self.axes[1, 0].bar(range(len(mention_counts)), mention_counts.values)
                    self.axes[1, 0].set_title('Verteilung der Erwähnungen')
                    self.axes[1, 0].set_xlabel('Erwähnungsanzahl')
                    self.axes[1, 0].set_ylabel('Häufigkeit')
                    
                # Trending (letzte 7 Tage)
                trending = self.analyzer.get_trending_symbols(7, 10)
                if not trending.empty:
                    self.axes[1, 1].barh(trending['Symbol'], trending['Mentions'])
                    self.axes[1, 1].set_title('Trending (7 Tage)')
                    self.axes[1, 1].set_xlabel('Erwähnungen')
                    
            self.fig.tight_layout()
            self.canvas.draw()
            
            self.log_message("Visualisierungen aktualisiert")
            
        except Exception as e:
            self.log_message(f"Fehler bei Visualisierung: {e}")
            
    def save_visualizations(self):
        """Speichert die Visualisierungen"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.fig.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Erfolg", f"Visualisierungen gespeichert: {filename}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")
                
    def test_reddit_connection(self):
        """Testet die Reddit-API-Verbindung"""
        try:
            if self.crawler.connect_to_reddit():
                self.api_status_var.set("Verbunden ✓")
                self.log_message("Reddit-API-Verbindung erfolgreich")
                messagebox.showinfo("Erfolg", "Reddit-API-Verbindung erfolgreich!")
            else:
                self.api_status_var.set("Fehler ✗")
                self.log_message("Reddit-API-Verbindung fehlgeschlagen")
                messagebox.showerror("Fehler", "Reddit-API-Verbindung fehlgeschlagen!")
        except Exception as e:
            self.api_status_var.set("Fehler ✗")
            self.log_message(f"Reddit-API-Fehler: {e}")
            messagebox.showerror("Fehler", f"Reddit-API-Fehler: {e}")
            
    def view_results(self):
        """Wechselt zum Ergebnisse-Tab"""
        self.notebook.select(1)  # Ergebnisse-Tab
        self.refresh_results()
        
    def load_results(self):
        """Lädt Ergebnisse aus einer Datei"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.log_message(f"JSON-Datei geladen: {filename}")
                    messagebox.showinfo("Erfolg", f"Ergebnisse geladen: {filename}")
                elif filename.endswith('.csv'):
                    df = pd.read_csv(filename)
                    self.log_message(f"CSV-Datei geladen: {filename}")
                    messagebox.showinfo("Erfolg", f"Ergebnisse geladen: {filename}")
                    
                self.refresh_results()
                
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Laden: {e}")
                
    def load_config(self):
        """Lädt Konfiguration aus einer Datei"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                # Aktualisiere GUI-Variablen
                if 'post_limit' in config_data:
                    self.post_limit_var.set(config_data['post_limit'])
                if 'comment_limit' in config_data:
                    self.comment_limit_var.set(config_data['comment_limit'])
                    
                self.log_message(f"Konfiguration geladen: {filename}")
                messagebox.showinfo("Erfolg", f"Konfiguration geladen: {filename}")
                
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Laden der Konfiguration: {e}")
                
    def open_data_directory(self):
        """Öffnet das Datenverzeichnis"""
        try:
            import subprocess
            import platform
            
            data_dir = os.path.abspath("data")
            
            if platform.system() == "Windows":
                os.startfile(data_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", data_dir])
            else:  # Linux
                subprocess.run(["xdg-open", data_dir])
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Öffnen des Verzeichnisses: {e}")
            
    def open_log_directory(self):
        """Öffnet das Log-Verzeichnis"""
        try:
            import subprocess
            import platform
            
            log_dir = os.path.abspath(DATA_PATHS['logs_dir'])
            
            if platform.system() == "Windows":
                os.startfile(log_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", log_dir])
            else:  # Linux
                subprocess.run(["xdg-open", log_dir])
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Öffnen des Log-Verzeichnisses: {e}")
            
    def show_about(self):
        """Zeigt das Über-Dialog"""
        about_text = """WSB Stock Crawler v1.0

Ein Tool zum Crawlen von r/wallstreetbets nach Aktiensymbolen.

Features:
• Reddit-Crawling mit PRAW
• Datenanalyse und Visualisierung
• GUI mit tkinter
• Export-Funktionen

Entwickelt für Bildungszwecke.
"""
        messagebox.showinfo("Über WSB Stock Crawler", about_text)


def main():
    """Hauptfunktion zum Starten der Anwendung"""
    # Erstelle notwendige Verzeichnisse (nur Verzeichnisse, keine Dateien)
    # Die 'data/' Verzeichnis wird implizit durch 'data/results/' erstellt
    directories_to_create = [
        DATA_PATHS['results_dir'],
        DATA_PATHS['analysis_dir'],
        DATA_PATHS['logs_dir']
    ]
    for path in directories_to_create:
        os.makedirs(path, exist_ok=True)
    
    # Starte GUI
    root = tk.Tk()
    app = WSBCrawlerGUI(root)
    
    # Zeige Willkommensnachricht
    app.log_message("WSB Stock Crawler gestartet")
    app.log_message("Bitte konfiguriere deine Reddit API-Credentials in der .env Datei")
    
    # Starte Hauptschleife
    root.mainloop()


if __name__ == "__main__":
    main()
