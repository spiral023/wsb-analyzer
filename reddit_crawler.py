"""
Reddit Crawler für WSB Stock Mentions
Durchsucht r/wallstreetbets nach Aktiensymbolen und zählt deren Häufigkeit
"""

import praw
import pandas as pd
import re
import json
import os
import io
from datetime import datetime, timezone
from collections import defaultdict, Counter
import logging
from config import REDDIT_CONFIG, CRAWLER_CONFIG, DATA_PATHS, STORAGE_CONFIG
import s3_handler

class WSBStockCrawler:
    def __init__(self):
        """Initialisiert den Reddit Crawler"""
        self.reddit = None
        self.stock_symbols = set()
        self.excluded_words = set(CRAWLER_CONFIG['excluded_words'])
        self.results = defaultdict(int)
        self.session_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.log_file_path = None
        self.session_path = None
        self.setup_logging()
        self.load_stock_symbols()
        
    def setup_logging(self):
        """Konfiguriert das Logging für die aktuelle Session."""
        os.makedirs(DATA_PATHS['logs_dir'], exist_ok=True)
        self.log_file_path = f"{DATA_PATHS['logs_dir']}/crawler_{self.session_timestamp}.log"
        
        # Entferne bestehende Handler, um Doppel-Logging zu vermeiden
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file_path),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_stock_symbols(self):
        """Lädt die Aktiensymbole aus der CSV-Datei"""
        try:
            df = pd.read_csv(DATA_PATHS['stock_symbols'])
            self.stock_symbols = set(df['Symbol'].str.upper())
            self.logger.info(f"Loaded {len(self.stock_symbols)} stock symbols")
        except FileNotFoundError:
            self.logger.error(f"Stock symbols file not found: {DATA_PATHS['stock_symbols']}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading stock symbols: {e}")
            raise
            
    def connect_to_reddit(self):
        """Stellt Verbindung zur Reddit API her"""
        try:
            self.reddit = praw.Reddit(
                client_id=REDDIT_CONFIG['client_id'],
                client_secret=REDDIT_CONFIG['client_secret'],
                user_agent=REDDIT_CONFIG['user_agent'],
                username=REDDIT_CONFIG['username'],
                password=REDDIT_CONFIG['password']
            )
            # Test der Verbindung
            self.reddit.user.me()
            self.logger.info("Successfully connected to Reddit API")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Reddit API: {e}")
            return False
            
    def extract_symbols_from_text(self, text):
        """Extrahiert Aktiensymbole aus einem Text"""
        if not text:
            return []
            
        # Bereinige den Text und konvertiere zu Großbuchstaben
        text = text.upper()
        
        # Finde alle Wörter, die potentielle Aktiensymbole sein könnten
        # Suche nach Wörtern mit 1-5 Buchstaben, die nicht in excluded_words sind
        pattern = r'\b[A-Z]{1,5}\b'
        potential_symbols = re.findall(pattern, text)
        
        # Filtere nach bekannten Aktiensymbolen und schließe ausgeschlossene Wörter aus
        found_symbols = []
        for symbol in potential_symbols:
            if (symbol in self.stock_symbols and 
                symbol not in self.excluded_words and
                len(symbol) >= CRAWLER_CONFIG['min_symbol_length'] and
                len(symbol) <= CRAWLER_CONFIG['max_symbol_length']):
                found_symbols.append(symbol)
                
        return found_symbols
        
    def crawl_subreddit(self, progress_callback=None):
        """Crawlt das WSB Subreddit nach Aktiensymbolen"""
        if not self.reddit:
            if not self.connect_to_reddit():
                return False
                
        try:
            subreddit = self.reddit.subreddit(CRAWLER_CONFIG['subreddit'])
            self.results = defaultdict(int)
            
            # Crawle Hot Posts
            posts_processed = 0
            total_posts = CRAWLER_CONFIG['post_limit']
            
            self.logger.info(f"Starting to crawl r/{CRAWLER_CONFIG['subreddit']}")
            
            for post in subreddit.hot(limit=CRAWLER_CONFIG['post_limit']):
                # Extrahiere Symbole aus Titel und Text des Posts
                title_symbols = self.extract_symbols_from_text(post.title)
                selftext_symbols = self.extract_symbols_from_text(post.selftext)
                
                # Zähle die gefundenen Symbole
                for symbol in title_symbols + selftext_symbols:
                    self.results[symbol] += 1
                    
                # Crawle Kommentare
                try:
                    post.comments.replace_more(limit=0)  # Entferne "more comments"
                    comments_processed = 0
                    
                    for comment in post.comments.list()[:CRAWLER_CONFIG['comment_limit']]:
                        if hasattr(comment, 'body'):
                            comment_symbols = self.extract_symbols_from_text(comment.body)
                            for symbol in comment_symbols:
                                self.results[symbol] += 1
                            comments_processed += 1
                            
                except Exception as e:
                    self.logger.warning(f"Error processing comments for post {post.id}: {e}")
                    
                posts_processed += 1
                
                # Update Progress
                if progress_callback:
                    progress = (posts_processed / total_posts) * 100
                    progress_callback(progress, f"Processed {posts_processed}/{total_posts} posts")
                    
                self.logger.info(f"Processed post {posts_processed}/{total_posts}: {post.title[:50]}...")
                
            self.logger.info(f"Crawling completed. Found {len(self.results)} unique symbols")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during crawling: {e}")
            return False
            
    def _upload_log_file(self, session_path):
        """Lädt die Log-Datei für die aktuelle Session nach S3 hoch."""
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            self.logger.error("Log-Datei nicht gefunden zum Hochladen.")
            return

        try:
            # Fährt alle Logger herunter und schließt die Dateien sicher
            logging.shutdown()
            
            with open(self.log_file_path, 'rb') as log_file_obj:
                log_s3_key = f"{DATA_PATHS['results_dir']}{session_path}crawler.log"
                self.logger.info(f"Lade Log-Datei nach {log_s3_key} hoch...")
                s3_handler.upload_file_obj(log_file_obj, log_s3_key)
            
            # Lokale Log-Datei nach dem Hochladen löschen
            os.remove(self.log_file_path)
            self.logger.info(f"Lokale Log-Datei {self.log_file_path} gelöscht.")

        except Exception as e:
            # Da der Logger heruntergefahren wurde, verwenden wir print für den Fehler
            print(f"Fehler beim Hochladen der Log-Datei: {e}")
        finally:
            # Re-initialisiere das Logging für den Fall, dass das Objekt weiterverwendet wird
            self.setup_logging()

    def save_results(self):
        """Speichert die Crawling-Ergebnisse entweder lokal oder auf S3."""
        try:
            # Verwende den im Konstruktor erstellten Zeitstempel für Konsistenz
            now = datetime.strptime(self.session_timestamp, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
            session_date = now.strftime("%Y-%m-%d")
            session_time = now.strftime("%H%M%S")
            self.session_path = f"{session_date}/{session_time}/"
            
            sorted_results = dict(sorted(self.results.items(), key=lambda x: x[1], reverse=True))

            # JSON-Daten vorbereiten
            result_data = {
                'timestamp': self.session_timestamp,
                'crawl_date': now.isoformat(),
                'total_symbols_found': len(sorted_results),
                'total_mentions': sum(sorted_results.values()),
                'subreddit': CRAWLER_CONFIG['subreddit'],
                'results': sorted_results
            }
            json_content = json.dumps(result_data, indent=2, ensure_ascii=False)
            
            # CSV-Daten vorbereiten
            df = pd.DataFrame(list(sorted_results.items()), columns=['Symbol', 'Mentions'])
            df['Timestamp'] = f"{session_date.replace('-', '')}_{session_time}"
            df['Date'] = now.strftime("%Y-%m-%d %H:%M:%S")
            csv_content = df.to_csv(index=False)

            json_filename = "wsb_mentions.json"
            csv_filename = "wsb_mentions.csv"

            if STORAGE_CONFIG['type'] == 's3':
                self.logger.info(f"Speichere Ergebnisse auf S3 in Session-Pfad: {self.session_path}")
                base_path = DATA_PATHS['results_dir']
                json_obj_name = f"{base_path}{self.session_path}{json_filename}"
                csv_obj_name = f"{base_path}{self.session_path}{csv_filename}"

                json_buffer = io.BytesIO(json_content.encode('utf-8'))
                s3_handler.upload_file_obj(json_buffer, json_obj_name)
                csv_buffer = io.BytesIO(csv_content.encode('utf-8'))
                s3_handler.upload_file_obj(csv_buffer, csv_obj_name)
                
                self.logger.info(f"Ergebnisse auf S3 unter {json_obj_name} und {csv_obj_name} gespeichert")
                
                # Lade die Log-Datei hoch
                self._upload_log_file(self.session_path)

                return json_obj_name, csv_obj_name
            else:
                # Lokal speichern
                local_session_dir = os.path.join(DATA_PATHS['results_dir'], self.session_path.replace('/', os.sep))
                self.logger.info(f"Speichere Ergebnisse lokal in: {local_session_dir}")
                os.makedirs(local_session_dir, exist_ok=True)
                
                local_json_path = os.path.join(local_session_dir, json_filename)
                with open(local_json_path, 'w', encoding='utf-8') as f:
                    f.write(json_content)

                local_csv_path = os.path.join(local_session_dir, csv_filename)
                with open(local_csv_path, 'w', encoding='utf-8') as f:
                    f.write(csv_content)
                
                self.logger.info(f"Ergebnisse lokal unter {local_json_path} und {local_csv_path} gespeichert")
                return local_json_path, local_csv_path

        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Ergebnisse: {e}")
            return None, None
            
    def get_top_mentions(self, limit=20):
        """Gibt die Top-Erwähnungen zurück"""
        if not self.results:
            return []
            
        sorted_results = sorted(self.results.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:limit]
        
    def get_crawl_summary(self):
        """Gibt eine Zusammenfassung des Crawling-Laufs zurück"""
        if not self.results:
            return None
            
        total_mentions = sum(self.results.values())
        unique_symbols = len(self.results)
        top_symbol = max(self.results.items(), key=lambda x: x[1]) if self.results else None
        
        return {
            'total_mentions': total_mentions,
            'unique_symbols': unique_symbols,
            'top_symbol': top_symbol,
            'crawl_time': datetime.now(timezone.utc).isoformat()
        }

if __name__ == "__main__":
    # Test des Crawlers
    crawler = WSBStockCrawler()
    
    if crawler.connect_to_reddit():
        print("Starting crawl...")
        if crawler.crawl_subreddit():
            print("Crawl completed successfully!")
            
            # Zeige Top-Ergebnisse
            top_mentions = crawler.get_top_mentions(10)
            print("\nTop 10 Mentions:")
            for symbol, count in top_mentions:
                print(f"{symbol}: {count}")
                
            # Speichere Ergebnisse
            json_file, csv_file = crawler.save_results()
            if json_file:
                print(f"\nResults saved to: {json_file}")
        else:
            print("Crawl failed!")
    else:
        print("Failed to connect to Reddit API!")
