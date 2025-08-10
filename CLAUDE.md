# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WSB Stock Analyzer is a Streamlit-based web application that analyzes stock mentions from the r/wallstreetbets subreddit. The application crawls Reddit posts and comments, extracts stock symbols, analyzes their frequency, and presents results through an interactive dashboard.

**Live Demo:** https://wsb-analyzer.streamlit.app

## Core Architecture

The application consists of four main modules:

1. **Reddit Crawler** (`reddit_crawler.py`): Uses PRAW to collect data from Reddit API
2. **Data Analyzer** (`data_analyzer.py`): Processes crawled data and creates visualizations using pandas/matplotlib/seaborn
3. **S3 Handler** (`s3_handler.py`): Optional cloud storage integration with AWS S3
4. **Streamlit UI** (`streamlit_app.py`): Main web interface and orchestration

Configuration is centralized in `config.py` with support for both environment variables and Streamlit secrets.

## Common Development Commands

### Running the Application
```bash
# Start the Streamlit app
streamlit run streamlit_app.py

# Alternative entry point
python run_app.py
```

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Unix/macOS)  
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

The app supports two configuration methods:
1. **Via UI (Recommended)**: Configure through the Streamlit sidebar - credentials are stored in browser LocalStorage
2. **Via .env file**: Create from `.env.example` template

Required Reddit API credentials:
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET` 
- `REDDIT_USERNAME`
- `REDDIT_PASSWORD`

Optional AWS S3 configuration:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET_NAME`
- `AWS_REGION`

## Key Technical Details

### Data Storage
- **Local mode**: Results stored in `data/results/`, analysis in `data/analysis/`, logs in `logs/`
- **S3 mode**: All data stored in configured S3 bucket
- Stock symbols loaded from `data/stock_symbols.csv`

### Session Management
- Each crawling session gets timestamped directory: `YYYYMMDD_HHMMSS`
- Results saved as JSON with metadata
- Historical sessions can be loaded and compared

### Symbol Extraction
- Extracts 1-5 character symbols from posts/comments
- Filters against extensive excluded words list in `config.py`
- Cross-references with known stock symbols from CSV file

### Logging
- Session-specific log files with timestamps
- Configurable logging levels
- Both file and console output

## File Structure Notes

- `gui_app.py`: Legacy Tkinter interface (superseded by Streamlit)
- `run_app.py`: Alternative entry point
- Main business logic separated cleanly from UI concerns
- Configuration abstracted to support multiple deployment scenarios (local, Streamlit Cloud, etc.)

## Development Considerations

- The app is designed to work both locally and on Streamlit Cloud
- Credentials are handled securely via LocalStorage or Streamlit secrets
- S3 integration is optional - app falls back to local storage
- German language is used in UI and documentation
- Modular design allows easy testing of individual components