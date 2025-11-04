# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Important**: When working on this Korean project, provide all responses, explanations, and documentation in Korean (한국어) unless specifically requested otherwise.

## Project Overview

NICL (News Information Collection & Library) is a Korean news aggregation system that combines:
- Naver News API for structured news data
- Google News web crawling for broader coverage
- SQLite database for storage with automatic deduplication
- Unified CLI interface for news collection

## Essential Commands

### Development Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file with Naver API credentials
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
```

### Running the Application
```bash
# Basic usage (API + crawling)
python main.py --keyword "인공지능" --count 20

# API only
python main.py --keyword "ChatGPT" --count 30 --api-only

# Crawling only
python main.py --keyword "ChatGPT" --count 30 --crawl-only

# Multiple keywords
python main.py --keywords "정치" "경제" "사회" --count 10

# Section-based collection
python main.py --section politics --count 30

# Database statistics
python main.py --stats

# Validate configuration
python main.py --validate
```

## Architecture

### Data Flow
1. **Entry Point** ([main.py](main.py)): CLI argument parsing and orchestration
2. **NewsCollector** ([src/news_collector.py](src/news_collector.py)): Main coordinator that integrates API and crawling
3. **Data Sources**:
   - **NaverNewsAPI** ([src/api/naver_news.py](src/api/naver_news.py)): Fetches from Naver News API
   - **NewsWebCrawler** ([src/crawler/news_crawler.py](src/crawler/news_crawler.py)): Scrapes Google News
4. **DatabaseManager** ([src/database/manager.py](src/database/manager.py)): SQLAlchemy-based persistence with deduplication
5. **Models** ([src/models/news.py](src/models/news.py)): NewsArticle and CollectionLog tables

### Key Design Patterns

**Dual-Source Collection**: When both API and crawling are enabled, `NewsCollector.collect_news_by_keyword()` splits the target count evenly between sources (e.g., 50 total = 25 API + 25 crawling). Each source adds a `source` field to distinguish origin.

**Deduplication**: The `DatabaseManager` checks `original_link` before inserting. Duplicates are silently skipped and counted but not saved. Existing duplicates get `is_duplicate=True` flag.

**Context Manager Pattern**: `NewsCollector` implements `__enter__`/`__exit__` for resource cleanup. Always use `with NewsCollector() as collector:` to ensure proper session/database closure.

**Configuration**: [src/utils/config.py](src/utils/config.py) loads `.env` via `python-dotenv` and provides typed config objects (`NaverAPIConfig`, `DatabaseConfig`, `LogConfig`). The singleton `config` instance is imported across modules.

### Data Model

**NewsArticle** table ([src/models/news.py](src/models/news.py)):
- `title`, `original_link` (used for dedup), `link`, `description`, `pub_date`
- `source`: 'naver_api', 'web_crawling', or 'google_crawling'
- `keyword`, `category`: search metadata
- `is_duplicate`, `is_processed`: status flags

**CollectionLog** table:
- Logs each collection run with `source`, `keyword`, `total_collected`, `duplicates_found`, `success`, `error_message`, `execution_time`

### Web Scraping

The `NewsWebCrawler` targets Google News (not Naver despite method naming for backward compatibility). Key selectors in [src/crawler/news_crawler.py](src/crawler/news_crawler.py):
- **Articles**: Tries multiple selectors (`article`, `div.xrnccd`, etc.) and falls back to link extraction
- **Titles**: Tries `a.gPFEn`, `a.JtKRv`, `h3 a`, `a[href*="./articles/"]`
- **Press**: Extracts from `div.vr1PYe`, `span.vr1PYe`, etc.

Google News selectors change frequently. If crawling fails, check and update selectors in `_parse_google_news_results()` and `_extract_google_news_data()`.

### API Integration

Naver News API ([src/api/naver_news.py](src/api/naver_news.py)):
- Requires `X-Naver-Client-Id` and `X-Naver-Client-Secret` headers
- Limits: 100 results per request, 1000 total per query
- Keyword filtering: `_process_news_item()` checks if keyword appears in title or description (case-insensitive)
- HTML cleanup: Removes tags like `<b>`, converts entities (`&amp;` → `&`)

## Working with This Codebase

### Adding New Data Sources

1. Create a new module in `src/api/` or `src/crawler/`
2. Implement a collection method returning `List[Dict[str, Any]]` with keys: `title`, `original_link`, `link`, `description`, `pub_date`, `source`, `keyword`, `category`
3. Update `NewsCollector.collect_news_by_keyword()` to integrate the new source
4. Update `main.py` to add CLI flags if needed

### Database Schema Changes

1. Modify models in [src/models/news.py](src/models/news.py)
2. SQLAlchemy auto-creates tables on first run. For migrations on existing DBs, manually update the schema or use Alembic
3. Update `DatabaseManager` methods if new fields require special handling

### Debugging Collection Issues

- Check logs in `logs/nicl.log` (configured in [src/utils/config.py](src/utils/config.py))
- Use `--validate` to test API credentials and DB connection
- Use `--api-only` or `--crawl-only` to isolate source issues
- Enable SQLAlchemy echo: Set `echo=True` in `DatabaseManager._setup_database()` to see SQL queries

### Environment Variables

Required in `.env`:
- `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`: Naver API credentials

Optional:
- `NAVER_API_BASE_URL`: Default `https://openapi.naver.com/v1/search/news.json`
- `REQUEST_DELAY`: Seconds between requests (default 1.0)
- `MAX_DISPLAY`: Max results per API call (default 100)
- `DATABASE_PATH`: DB file path (default `data/nicl_news.db`)
- `LOG_LEVEL`, `LOG_FILE`: Logging configuration

### Important Constraints

- Never commit `.env` to version control (already in `.gitignore`)
- Respect Naver API rate limits (built-in 1s delay between requests)
- Google News may block excessive crawling; the default 2s delay in `NewsWebCrawler` is intentional
- SQLite is used with `check_same_thread=False` for compatibility; avoid concurrent writes from multiple processes
