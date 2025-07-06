"""
Datenanalyse-Modul für WSB Stock Crawler
Erstellt tabellarische Übersichten und Analysen der Crawling-Ergebnisse
"""

import pandas as pd
import json
import os
import glob
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import logging
from config import DATA_PATHS

class WSBDataAnalyzer:
    def __init__(self):
        """Initialisiert den Datenanalyzer"""
        self.setup_logging()
        self.all_results = []
        self.combined_df = None
        
    def setup_logging(self):
        """Konfiguriert das Logging"""
        os.makedirs(DATA_PATHS['logs_dir'], exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{DATA_PATHS['logs_dir']}/analyzer.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_all_results(self):
        """Lädt alle gespeicherten Crawling-Ergebnisse"""
        try:
            # Finde alle JSON-Dateien im Results-Verzeichnis
            json_files = glob.glob(f"{DATA_PATHS['results_dir']}/*.json")
            
            if not json_files:
                self.logger.warning("No result files found")
                return False
                
            self.all_results = []
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.all_results.append(data)
                except Exception as e:
                    self.logger.error(f"Error loading {json_file}: {e}")
                    
            self.logger.info(f"Loaded {len(self.all_results)} result files")
            return len(self.all_results) > 0
            
        except Exception as e:
            self.logger.error(f"Error loading results: {e}")
            return False
            
    def create_combined_dataframe(self):
        """Erstellt einen kombinierten DataFrame aus allen Ergebnissen"""
        if not self.all_results:
            self.logger.error("No results loaded")
            return False
            
        try:
            combined_data = []
            
            for result in self.all_results:
                timestamp = result.get('timestamp', '')
                crawl_date = result.get('crawl_date', '')
                
                # Konvertiere Datum
                try:
                    if crawl_date:
                        date_obj = datetime.fromisoformat(crawl_date.replace('Z', '+00:00'))
                    else:
                        # Fallback: Parse aus Timestamp
                        date_obj = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                except:
                    date_obj = datetime.now()
                    
                # Füge jeden Symbol-Mention als Zeile hinzu
                for symbol, mentions in result.get('results', {}).items():
                    combined_data.append({
                        'Date': date_obj.date(),
                        'DateTime': date_obj,
                        'Timestamp': timestamp,
                        'Symbol': symbol,
                        'Mentions': mentions,
                        'TotalMentions': result.get('total_mentions', 0),
                        'UniqueSymbols': result.get('total_symbols_found', 0)
                    })
                    
            self.combined_df = pd.DataFrame(combined_data)
            
            if not self.combined_df.empty:
                # Sortiere nach Datum
                self.combined_df = self.combined_df.sort_values('DateTime')
                self.logger.info(f"Created combined dataframe with {len(self.combined_df)} rows")
                return True
            else:
                self.logger.warning("Combined dataframe is empty")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating combined dataframe: {e}")
            return False
            
    def get_top_symbols_overall(self, limit=20):
        """Gibt die Top-Symbole über alle Crawls hinweg zurück"""
        if self.combined_df is None or self.combined_df.empty:
            return pd.DataFrame()
            
        try:
            # Gruppiere nach Symbol und summiere Mentions
            top_symbols = (self.combined_df.groupby('Symbol')['Mentions']
                          .sum()
                          .sort_values(ascending=False)
                          .head(limit))
            
            return top_symbols.reset_index()
            
        except Exception as e:
            self.logger.error(f"Error getting top symbols: {e}")
            return pd.DataFrame()
            
    def get_trending_symbols(self, days=7, limit=10):
        """Findet trending Symbole der letzten N Tage"""
        if self.combined_df is None or self.combined_df.empty:
            return pd.DataFrame()
            
        try:
            # Filtere nach den letzten N Tagen
            cutoff_date = datetime.now().date() - timedelta(days=days)
            recent_df = self.combined_df[self.combined_df['Date'] >= cutoff_date]
            
            if recent_df.empty:
                return pd.DataFrame()
                
            # Berechne Trend (Mentions der letzten Tage)
            trending = (recent_df.groupby('Symbol')['Mentions']
                       .sum()
                       .sort_values(ascending=False)
                       .head(limit))
            
            return trending.reset_index()
            
        except Exception as e:
            self.logger.error(f"Error getting trending symbols: {e}")
            return pd.DataFrame()
            
    def get_symbol_timeline(self, symbol):
        """Gibt die Timeline für ein bestimmtes Symbol zurück"""
        if self.combined_df is None or self.combined_df.empty:
            return pd.DataFrame()
            
        try:
            symbol_data = self.combined_df[self.combined_df['Symbol'] == symbol.upper()]
            return symbol_data.sort_values('DateTime')
            
        except Exception as e:
            self.logger.error(f"Error getting timeline for {symbol}: {e}")
            return pd.DataFrame()
            
    def create_summary_report(self):
        """Erstellt einen Zusammenfassungsbericht"""
        if not self.all_results:
            return None
            
        try:
            # Grundlegende Statistiken
            total_crawls = len(self.all_results)
            
            if self.combined_df is not None and not self.combined_df.empty:
                unique_symbols = self.combined_df['Symbol'].nunique()
                total_mentions = self.combined_df['Mentions'].sum()
                date_range = f"{self.combined_df['Date'].min()} bis {self.combined_df['Date'].max()}"
                
                # Top 10 Symbole
                top_symbols = self.get_top_symbols_overall(10)
                
                # Trending Symbole (letzte 7 Tage)
                trending = self.get_trending_symbols(7, 5)
                
                summary = {
                    'report_date': datetime.now().isoformat(),
                    'total_crawls': total_crawls,
                    'unique_symbols': unique_symbols,
                    'total_mentions': total_mentions,
                    'date_range': date_range,
                    'top_symbols': top_symbols.to_dict('records') if not top_symbols.empty else [],
                    'trending_symbols': trending.to_dict('records') if not trending.empty else []
                }
                
                return summary
            else:
                return {
                    'report_date': datetime.now().isoformat(),
                    'total_crawls': total_crawls,
                    'error': 'No valid data found'
                }
                
        except Exception as e:
            self.logger.error(f"Error creating summary report: {e}")
            return None
            
    def save_analysis_results(self):
        """Speichert die Analyseergebnisse"""
        try:
            os.makedirs(DATA_PATHS['analysis_dir'], exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Speichere kombinierten DataFrame
            if self.combined_df is not None and not self.combined_df.empty:
                csv_filename = f"{DATA_PATHS['analysis_dir']}/combined_analysis_{timestamp}.csv"
                self.combined_df.to_csv(csv_filename, index=False)
                self.logger.info(f"Combined analysis saved to {csv_filename}")
                
                # Speichere Top-Symbole
                top_symbols = self.get_top_symbols_overall(50)
                if not top_symbols.empty:
                    top_filename = f"{DATA_PATHS['analysis_dir']}/top_symbols_{timestamp}.csv"
                    top_symbols.to_csv(top_filename, index=False)
                    
                # Speichere Trending-Symbole
                trending = self.get_trending_symbols(7, 20)
                if not trending.empty:
                    trending_filename = f"{DATA_PATHS['analysis_dir']}/trending_symbols_{timestamp}.csv"
                    trending.to_csv(trending_filename, index=False)
                    
            # Speichere Summary Report
            summary = self.create_summary_report()
            if summary:
                summary_filename = f"{DATA_PATHS['analysis_dir']}/summary_report_{timestamp}.json"
                with open(summary_filename, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
                self.logger.info(f"Summary report saved to {summary_filename}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving analysis results: {e}")
            return False
            
    def create_visualizations(self, save_plots=True):
        """Erstellt Visualisierungen der Daten"""
        if self.combined_df is None or self.combined_df.empty:
            self.logger.warning("No data available for visualization")
            return False
            
        try:
            # Setze Stil für Plots
            plt.style.use('default')
            sns.set_palette("husl")
            
            # 1. Top 15 Symbole (Balkendiagramm)
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('WSB Stock Mentions Analysis', fontsize=16, fontweight='bold')
            
            # Top Symbole
            top_symbols = self.get_top_symbols_overall(15)
            if not top_symbols.empty:
                axes[0, 0].barh(top_symbols['Symbol'], top_symbols['Mentions'])
                axes[0, 0].set_title('Top 15 Most Mentioned Stocks')
                axes[0, 0].set_xlabel('Total Mentions')
                
            # Mentions über Zeit (Timeline)
            daily_mentions = (self.combined_df.groupby('Date')['Mentions']
                            .sum()
                            .reset_index())
            if not daily_mentions.empty:
                axes[0, 1].plot(daily_mentions['Date'], daily_mentions['Mentions'], marker='o')
                axes[0, 1].set_title('Daily Mention Trends')
                axes[0, 1].set_xlabel('Date')
                axes[0, 1].set_ylabel('Total Mentions')
                axes[0, 1].tick_params(axis='x', rotation=45)
                
            # Top 10 Symbole Heatmap über Zeit
            top_10_symbols = self.get_top_symbols_overall(10)['Symbol'].tolist()
            if top_10_symbols:
                heatmap_data = (self.combined_df[self.combined_df['Symbol'].isin(top_10_symbols)]
                              .pivot_table(index='Symbol', columns='Date', values='Mentions', fill_value=0))
                
                if not heatmap_data.empty:
                    sns.heatmap(heatmap_data, ax=axes[1, 0], cmap='YlOrRd', cbar_kws={'label': 'Mentions'})
                    axes[1, 0].set_title('Top 10 Stocks Mention Heatmap')
                    axes[1, 0].set_xlabel('Date')
                    
            # Verteilung der Mentions
            mention_dist = self.combined_df['Mentions'].value_counts().head(20)
            if not mention_dist.empty:
                axes[1, 1].bar(range(len(mention_dist)), mention_dist.values)
                axes[1, 1].set_title('Distribution of Mention Counts')
                axes[1, 1].set_xlabel('Mention Count')
                axes[1, 1].set_ylabel('Frequency')
                
            plt.tight_layout()
            
            if save_plots:
                os.makedirs(DATA_PATHS['analysis_dir'], exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                plot_filename = f"{DATA_PATHS['analysis_dir']}/wsb_analysis_plots_{timestamp}.png"
                plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
                self.logger.info(f"Plots saved to {plot_filename}")
                
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating visualizations: {e}")
            return False
            
    def run_full_analysis(self):
        """Führt eine vollständige Analyse durch"""
        self.logger.info("Starting full analysis...")
        
        # Lade alle Ergebnisse
        if not self.load_all_results():
            self.logger.error("Failed to load results")
            return False
            
        # Erstelle kombinierten DataFrame
        if not self.create_combined_dataframe():
            self.logger.error("Failed to create combined dataframe")
            return False
            
        # Speichere Analyseergebnisse
        if not self.save_analysis_results():
            self.logger.error("Failed to save analysis results")
            return False
            
        # Erstelle Visualisierungen
        self.create_visualizations()
        
        self.logger.info("Full analysis completed successfully")
        return True

if __name__ == "__main__":
    # Test des Analyzers
    analyzer = WSBDataAnalyzer()
    
    if analyzer.run_full_analysis():
        print("Analysis completed successfully!")
        
        # Zeige Summary
        summary = analyzer.create_summary_report()
        if summary:
            print(f"\nAnalysis Summary:")
            print(f"Total Crawls: {summary.get('total_crawls', 0)}")
            print(f"Unique Symbols: {summary.get('unique_symbols', 0)}")
            print(f"Total Mentions: {summary.get('total_mentions', 0)}")
            print(f"Date Range: {summary.get('date_range', 'N/A')}")
            
            print(f"\nTop 5 Symbols:")
            for symbol in summary.get('top_symbols', [])[:5]:
                print(f"  {symbol.get('Symbol', 'N/A')}: {symbol.get('Mentions', 0)} mentions")
    else:
        print("Analysis failed!")
