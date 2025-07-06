"""
Konfigurationsdatei für den WSB Stock Crawler
"""

import os
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus .env Datei
load_dotenv()

# Reddit API Konfiguration
REDDIT_CONFIG = {
    'client_id': os.getenv('REDDIT_CLIENT_ID', 'your_client_id'),
    'client_secret': os.getenv('REDDIT_CLIENT_SECRET', 'your_client_secret'),
    'user_agent': 'WSB_Stock_Crawler/1.0 by YourUsername',
    'username': os.getenv('REDDIT_USERNAME', 'your_username'),
    'password': os.getenv('REDDIT_PASSWORD', 'your_password')
}

# Crawler Einstellungen
CRAWLER_CONFIG = {
    'subreddit': 'wallstreetbets',
    'post_limit': 100,  # Anzahl der Posts pro Suchlauf
    'comment_limit': 50,  # Anzahl der Kommentare pro Post
    'min_symbol_length': 1,  # Minimale Länge für Aktiensymbole
    'max_symbol_length': 5,  # Maximale Länge für Aktiensymbole
    'excluded_words': ['THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BUT', 'WHAT', 'YOUR', 'WHEN', 'HIM', 'MY', 'HAS', 'IT', 'I', 'A', 'TO', 'OF', 'IN', 'IS', 'ON', 'AT', 'BE', 'OR', 'AS', 'FROM', 'UP', 'BY', 'IF', 'DO', 'NO', 'SO', 'WE', 'GO', 'ME', 'AM', 'US', 'AN', 'HE', 'SHE', 'WHO', 'OIL', 'GAS', 'CAR', 'CEO', 'CFO', 'CTO', 'IPO', 'SEC', 'FDA', 'FED', 'GDP', 'CPI', 'ATH', 'ATL', 'DD', 'TA', 'PE', 'EPS', 'ROI', 'YOY', 'QOQ', 'MOM', 'EOD', 'AH', 'PM', 'WSB', 'YOLO', 'FD', 'HODL', 'MOON', 'STONK', 'STONKS', 'TENDIES', 'DIAMOND', 'HANDS', 'PAPER', 'ROCKET', 'BULL', 'BEAR', 'APES', 'APE', 'RETARD', 'AUTIST', 'WIFE', 'BOYFRIEND', 'LOSS', 'GAIN', 'PORN', 'LOSS', 'GAIN', 'BUY', 'SELL', 'HOLD', 'LONG', 'SHORT', 'CALL', 'PUT', 'PUTS', 'CALLS', 'OPTION', 'OPTIONS', 'STRIKE', 'EXPIRY', 'DTE', 'IV', 'THETA', 'DELTA', 'GAMMA', 'VEGA', 'RHO']
}

# Dateipfade
DATA_PATHS = {
    'stock_symbols': 'data/stock_symbols.csv',
    'results_dir': 'data/results/',
    'analysis_dir': 'data/analysis/',
    'logs_dir': 'logs/'
}

# GUI Einstellungen
GUI_CONFIG = {
    'window_title': 'WSB Stock Crawler',
    'window_size': '1200x800',
    'theme': 'default'
}
