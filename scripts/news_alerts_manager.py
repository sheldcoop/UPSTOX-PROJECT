#!/usr/bin/env python3
"""
News Alerts Manager - Real-time Market News Monitoring

Monitors and alerts on breaking market news from multiple sources:
- Company-specific news (earnings, announcements, management changes)
- Sector news (regulatory changes, industry trends)
- Market news (circuit breakers, trading halts, index changes)
- Breaking news alerts
- Sentiment analysis (basic keyword-based)
- Position-based alerts (news for holdings)

Features:
- Multi-source news aggregation
- Real-time monitoring
- Keyword and symbol tracking
- Sentiment classification (POSITIVE/NEGATIVE/NEUTRAL)
- Priority alerts (HIGH/MEDIUM/LOW)
- News history and analytics
- Integration with positions

Usage:
    # Get latest news for symbol
    python news_alerts_manager.py --action latest --symbol INFY --limit 10

    # Monitor news in real-time
    python news_alerts_manager.py --action monitor --symbols INFY,TCS --interval 300

    # Get breaking news
    python news_alerts_manager.py --action breaking --minutes 30

    # Search news by keyword
    python news_alerts_manager.py --action search --keyword "dividend" --days 7

    # Get sentiment analysis
    python news_alerts_manager.py --action sentiment --symbol INFY --days 30

    # Monitor positions for news
    python news_alerts_manager.py --action monitor-positions --interval 600

Author: Upstox Backend Team
Date: 2026-01-31
"""

import os
import sys
import json
import sqlite3
import requests
import argparse
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Try to import FinBERT for sentiment analysis
try:
    from transformers import BertTokenizer, BertForSequenceClassification
    import torch

    FINBERT_AVAILABLE = True
except ImportError:
    FINBERT_AVAILABLE = False
    logger.warning(
        "FinBERT not available. Install with: pip install transformers torch"
    )


class NewsAlertsManager:
    """Manages news alerts and real-time monitoring."""

    def __init__(
        self, db_path: str = "market_data.db", news_api_key: Optional[str] = None
    ):
        """
        Initialize the News Alerts Manager.

        Args:
            db_path: Path to SQLite database
            news_api_key: NewsAPI.org API key (optional, uses env var if not provided)
        """
        self.db_path = db_path
        self.news_api_key = news_api_key or os.getenv("NEWS_API_KEY")

        # Sentiment keywords (fallback if FinBERT not available)
        self.positive_keywords = [
            "profit",
            "growth",
            "gain",
            "rise",
            "surge",
            "boost",
            "upgrade",
            "expand",
            "acquisition",
            "merger",
            "dividend",
            "bonus",
            "buy",
            "outperform",
            "strong",
            "record",
            "high",
            "beat",
            "exceed",
        ]

        self.negative_keywords = [
            "loss",
            "decline",
            "fall",
            "drop",
            "plunge",
            "downgrade",
            "cut",
            "weak",
            "miss",
            "below",
            "concern",
            "risk",
            "delay",
            "cancel",
            "sell",
            "underperform",
            "regulatory",
            "fine",
            "lawsuit",
            "fraud",
        ]

        # Initialize FinBERT if available
        self.finbert_model = None
        self.finbert_tokenizer = None
        if FINBERT_AVAILABLE:
            try:
                logger.info("Loading FinBERT model for sentiment analysis...")
                self.finbert_tokenizer = BertTokenizer.from_pretrained(
                    "yiyanghkust/finbert-tone"
                )
                self.finbert_model = BertForSequenceClassification.from_pretrained(
                    "yiyanghkust/finbert-tone"
                )
                logger.info("FinBERT model loaded successfully")
            except Exception as e:
                logger.warning(
                    f"Failed to load FinBERT: {e}. Using keyword-based sentiment."
                )

        self._init_database()

    def _init_database(self):
        """Initialize database tables for news management."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # News articles table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id TEXT UNIQUE,
                headline TEXT NOT NULL,
                summary TEXT,
                content TEXT,
                source TEXT,
                author TEXT,
                published_at DATETIME,
                symbols TEXT,
                category TEXT,
                sentiment TEXT,
                sentiment_score REAL,
                priority TEXT,
                url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(news_id)
            )
        """
        )

        # News alerts table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS news_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id TEXT,
                symbol TEXT,
                alert_type TEXT,
                alert_priority TEXT,
                triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'NEW',
                user_action TEXT,
                FOREIGN KEY(news_id) REFERENCES news_articles(news_id)
            )
        """
        )

        # Watchlist table (symbols to monitor)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS news_watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE,
                alert_priority TEXT DEFAULT 'HIGH',
                keywords TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Sentiment history table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sentiment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                date DATE,
                positive_count INTEGER DEFAULT 0,
                negative_count INTEGER DEFAULT 0,
                neutral_count INTEGER DEFAULT 0,
                avg_sentiment_score REAL,
                total_articles INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date)
            )
        """
        )

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_news_published ON news_articles(published_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_news_symbols ON news_articles(symbols)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_news_sentiment ON news_articles(sentiment)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON news_alerts(symbol)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_sentiment_symbol ON sentiment_history(symbol)"
        )

        conn.commit()
        conn.close()
        logger.info("News database initialized")

    def _generate_news_id(self, headline: str, published_at: str) -> str:
        """Generate unique news ID from headline and timestamp."""
        unique_str = f"{headline}{published_at}"
        return hashlib.md5(unique_str.encode()).hexdigest()

    def _analyze_sentiment(self, text: str) -> tuple:
        """
        Analyze sentiment of text (basic keyword-based).

        Args:
            text: Text to analyze

        Returns:
            Tuple of (sentiment, score)
        """
        text_lower = text.lower()

        positive_count = sum(
            1 for keyword in self.positive_keywords if keyword in text_lower
        )
        negative_count = sum(
            1 for keyword in self.negative_keywords if keyword in text_lower
        )

        total = positive_count + negative_count

        if total == 0:
            return ("NEUTRAL", 0.0)

        score = (positive_count - negative_count) / total

        if score > 0.2:
            return ("POSITIVE", score)
        elif score < -0.2:
            return ("NEGATIVE", score)
        else:
            return ("NEUTRAL", score)

    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text (basic pattern matching)."""
        # Common NSE symbols pattern
        symbols = re.findall(r"\b[A-Z]{2,10}\b", text)

        # Filter common words that aren't symbols
        common_words = {
            "THE",
            "AND",
            "FOR",
            "ARE",
            "BUT",
            "NOT",
            "YOU",
            "ALL",
            "CAN",
            "HER",
            "WAS",
            "ONE",
            "OUR",
            "OUT",
            "DAY",
            "GET",
            "HAS",
            "HIM",
            "HIS",
            "HOW",
            "MAN",
            "NEW",
            "NOW",
            "OLD",
            "SEE",
            "TWO",
            "WAY",
            "WHO",
            "BOY",
            "DID",
            "ITS",
            "LET",
            "PUT",
            "SAY",
            "SHE",
            "TOO",
            "USE",
        }

        symbols = [s for s in symbols if s not in common_words and len(s) >= 3]

        return list(set(symbols))

    def _store_news(self, news: Dict[str, Any]):
        """Store news article in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        news_id = self._generate_news_id(
            news.get("headline", ""), news.get("published_at", str(datetime.now()))
        )

        # Analyze sentiment
        text_for_sentiment = f"{news.get('headline', '')} {news.get('summary', '')}"
        sentiment, sentiment_score = self._analyze_sentiment(text_for_sentiment)

        # Extract symbols
        symbols = self._extract_symbols(text_for_sentiment)
        symbols_str = ",".join(symbols)

        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO news_articles
                (news_id, headline, summary, content, source, author, published_at,
                 symbols, category, sentiment, sentiment_score, priority, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    news_id,
                    news.get("headline"),
                    news.get("summary"),
                    news.get("content"),
                    news.get("source"),
                    news.get("author"),
                    news.get("published_at"),
                    symbols_str,
                    news.get("category"),
                    sentiment,
                    sentiment_score,
                    news.get("priority", "MEDIUM"),
                    news.get("url"),
                ),
            )

            conn.commit()

            # Update sentiment history
            if symbols:
                for symbol in symbols:
                    self._update_sentiment_history(symbol, sentiment)

            logger.info(f"Stored news: {news.get('headline')[:50]}...")
            return news_id

        except sqlite3.IntegrityError:
            logger.debug(f"News already exists: {news.get('headline')[:50]}")
            return None
        finally:
            conn.close()

    def _update_sentiment_history(self, symbol: str, sentiment: str):
        """Update daily sentiment statistics for symbol."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = datetime.now().strftime("%Y-%m-%d")

        # Get current counts
        cursor.execute(
            """
            SELECT positive_count, negative_count, neutral_count, total_articles
            FROM sentiment_history
            WHERE symbol = ? AND date = ?
        """,
            (symbol, today),
        )

        result = cursor.fetchone()

        if result:
            pos, neg, neu, total = result

            if sentiment == "POSITIVE":
                pos += 1
            elif sentiment == "NEGATIVE":
                neg += 1
            else:
                neu += 1

            total += 1
            avg_score = (pos - neg) / total if total > 0 else 0.0

            cursor.execute(
                """
                UPDATE sentiment_history
                SET positive_count = ?, negative_count = ?, neutral_count = ?,
                    total_articles = ?, avg_sentiment_score = ?
                WHERE symbol = ? AND date = ?
            """,
                (pos, neg, neu, total, avg_score, symbol, today),
            )
        else:
            pos, neg, neu = (
                (1, 0, 0)
                if sentiment == "POSITIVE"
                else (0, 1, 0) if sentiment == "NEGATIVE" else (0, 0, 1)
            )
            total = 1
            avg_score = (
                1.0
                if sentiment == "POSITIVE"
                else -1.0 if sentiment == "NEGATIVE" else 0.0
            )

            cursor.execute(
                """
                INSERT INTO sentiment_history
                (symbol, date, positive_count, negative_count, neutral_count,
                 total_articles, avg_sentiment_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (symbol, today, pos, neg, neu, total, avg_score),
            )

        conn.commit()
        conn.close()

    def fetch_latest_news(
        self, symbol: Optional[str] = None, limit: int = 10, use_mock: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch latest news articles from NewsAPI.org or mock data.

        Args:
            symbol: Filter by symbol (optional)
            limit: Number of articles to return
            use_mock: Force mock data (for testing)

        Returns:
            List of news articles
        """
        # Try to fetch from NewsAPI.org
        if self.news_api_key and not use_mock:
            try:
                news_articles = self._fetch_from_newsapi(symbol, limit)
                logger.info(
                    f"Fetched {len(news_articles)} real news articles from NewsAPI.org"
                )
            except Exception as e:
                logger.warning(f"NewsAPI.org failed: {e}. Using mock data.")
                news_articles = self._generate_mock_news(symbol, limit)
        else:
            if not self.news_api_key:
                logger.warning(
                    "No NEWS_API_KEY found. Using mock data. Get free key: https://newsapi.org/register"
                )
            news_articles = self._generate_mock_news(symbol, limit)

        # Store in database with sentiment analysis
        for news in news_articles:
            # Analyze sentiment using FinBERT or keywords
            if "sentiment" not in news or not news["sentiment"]:
                text = f"{news.get('headline', '')} {news.get('summary', '')}"
                news["sentiment"] = self._analyze_sentiment_advanced(text)
                news["sentiment_score"] = news["sentiment"].get("score", 0)

            self._store_news(news)

        # Retrieve from database
        return self.get_news_from_db(symbol=symbol, limit=limit)

    def _generate_mock_news(
        self, symbol: Optional[str], count: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate mock news data for demonstration."""
        news_templates = [
            {
                "headline": "{symbol} reports strong Q3 earnings, beats estimates",
                "summary": "{symbol} posted Q3 profit of ₹1,250 crore, beating analyst estimates of ₹1,150 crore. Revenue grew 15% YoY.",
                "sentiment_bias": "POSITIVE",
            },
            {
                "headline": "Analysts upgrade {symbol} to BUY, raise target price",
                "summary": "Leading brokerage firms have upgraded {symbol} with increased price targets citing strong fundamentals.",
                "sentiment_bias": "POSITIVE",
            },
            {
                "headline": "{symbol} faces regulatory scrutiny over compliance issues",
                "summary": "Market regulator SEBI is investigating {symbol} for alleged compliance violations.",
                "sentiment_bias": "NEGATIVE",
            },
            {
                "headline": "{symbol} announces ₹15 per share dividend",
                "summary": "Board of {symbol} approved final dividend of ₹15 per share for FY2026.",
                "sentiment_bias": "POSITIVE",
            },
            {
                "headline": "{symbol} Q3 revenue misses expectations, stock falls",
                "summary": "{symbol} reported Q3 revenue below analyst expectations, leading to 3% decline in stock price.",
                "sentiment_bias": "NEGATIVE",
            },
        ]

        symbols_list = (
            [symbol] if symbol else ["INFY", "TCS", "RELIANCE", "HDFC", "ICICI"]
        )

        news_articles = []
        current_time = datetime.now()

        for i in range(count):
            template = news_templates[i % len(news_templates)]
            sym = symbols_list[i % len(symbols_list)]

            news = {
                "headline": template["headline"].format(symbol=sym),
                "summary": template["summary"].format(symbol=sym),
                "content": template["summary"].format(symbol=sym),
                "source": "Economic Times" if i % 2 == 0 else "Moneycontrol",
                "author": "Market Desk",
                "published_at": (current_time - timedelta(minutes=i * 15)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "category": (
                    "EARNINGS" if "earnings" in template["headline"] else "GENERAL"
                ),
                "priority": (
                    "HIGH" if template["sentiment_bias"] == "NEGATIVE" else "MEDIUM"
                ),
                "url": f"https://example.com/news/{i}",
            }

            news_articles.append(news)

        return news_articles

    def _fetch_from_newsapi(
        self, symbol: Optional[str], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch news from NewsAPI.org.

        Args:
            symbol: Stock symbol (e.g., 'INFY')
            limit: Number of articles

        Returns:
            List of news articles
        """
        # Map symbol to company name for better results
        company_names = {
            "INFY": "Infosys",
            "TCS": "Tata Consultancy Services",
            "RELIANCE": "Reliance Industries",
            "HDFCBANK": "HDFC Bank",
            "ICICIBANK": "ICICI Bank",
            "SBIN": "State Bank of India",
            "BHARTIARTL": "Bharti Airtel",
            "ITC": "ITC Limited",
            "HINDUNILVR": "Hindustan Unilever",
            "WIPRO": "Wipro",
        }

        company_name = company_names.get(symbol, symbol) if symbol else None

        # Build search query
        if company_name:
            query = f'"{company_name}" OR {symbol}'
        else:
            query = "India stock market OR BSE OR NSE OR Sensex OR Nifty"

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": min(limit, 100),  # NewsAPI max 100
            "apiKey": self.news_api_key,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            raise Exception(f"NewsAPI error: {data.get('message')}")

        articles = []
        for article in data.get("articles", []):
            # Extract symbol mentions from title/description
            text = f"{article.get('title', '')} {article.get('description', '')}"
            extracted_symbols = self._extract_symbols(text)

            if symbol and symbol not in extracted_symbols:
                extracted_symbols.append(symbol)

            news_item = {
                "headline": article.get("title", ""),
                "summary": article.get("description", ""),
                "content": article.get("content", article.get("description", "")),
                "source": article.get("source", {}).get("name", "Unknown"),
                "author": article.get("author", "Unknown"),
                "published_at": article.get("publishedAt", datetime.now().isoformat()),
                "category": self._categorize_news(article.get("title", "")),
                "priority": "HIGH",
                "url": article.get("url", ""),
                "symbols": extracted_symbols,
            }

            articles.append(news_item)

        return articles[:limit]

    def _analyze_sentiment_advanced(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using FinBERT (AI) or fallback to keywords.

        Args:
            text: Text to analyze

        Returns:
            Sentiment dictionary with label and score
        """
        if self.finbert_model and self.finbert_tokenizer:
            try:
                # Use FinBERT (AI-based)
                inputs = self.finbert_tokenizer(
                    text,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512,
                )
                with torch.no_grad():
                    outputs = self.finbert_model(**inputs)
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

                sentiment_idx = predictions.argmax().item()
                confidence = predictions.max().item()

                # FinBERT outputs: [positive, neutral, negative]
                labels = ["POSITIVE", "NEUTRAL", "NEGATIVE"]
                sentiment_label = labels[sentiment_idx]

                # Convert to score (-1 to 1)
                scores = [1, 0, -1]  # positive=1, neutral=0, negative=-1
                sentiment_score = scores[sentiment_idx] * confidence

                return {
                    "label": sentiment_label,
                    "score": sentiment_score,
                    "confidence": confidence,
                    "method": "FinBERT AI",
                }
            except Exception as e:
                logger.warning(f"FinBERT analysis failed: {e}. Using keyword method.")

        # Fallback to keyword-based sentiment
        return self._analyze_sentiment(text)

    def _categorize_news(self, title: str) -> str:
        """
        Categorize news article based on title.

        Args:
            title: News title

        Returns:
            Category string
        """
        title_lower = title.lower()

        if any(
            word in title_lower
            for word in ["earnings", "quarterly", "results", "profit", "revenue"]
        ):
            return "EARNINGS"
        elif any(word in title_lower for word in ["dividend", "payout"]):
            return "DIVIDEND"
        elif any(word in title_lower for word in ["merger", "acquisition", "deal"]):
            return "M&A"
        elif any(
            word in title_lower for word in ["regulation", "sebi", "rbi", "government"]
        ):
            return "REGULATORY"
        elif any(word in title_lower for word in ["launch", "product", "service"]):
            return "PRODUCT"
        else:
            return "GENERAL"

    def get_news_from_db(
        self, symbol: Optional[str] = None, days: int = 7, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get news from database.

        Args:
            symbol: Filter by symbol
            days: Days to look back
            limit: Maximum number of articles

        Returns:
            List of news articles
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        query = """
            SELECT * FROM news_articles
            WHERE published_at >= ?
        """

        params = [start_date]

        if symbol:
            query += " AND symbols LIKE ?"
            params.append(f"%{symbol}%")

        query += " ORDER BY published_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()

        return results

    def get_breaking_news(self, minutes: int = 30) -> List[Dict[str, Any]]:
        """
        Get breaking news from last N minutes.

        Args:
            minutes: Time window in minutes

        Returns:
            List of recent news articles
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        start_time = (datetime.now() - timedelta(minutes=minutes)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute(
            """
            SELECT * FROM news_articles
            WHERE published_at >= ?
            ORDER BY published_at DESC
        """,
            (start_time,),
        )

        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()

        # If no real news, fetch and generate
        if not results:
            self.fetch_latest_news(limit=5)
            return self.get_breaking_news(minutes=minutes)

        return results

    def search_news(
        self, keyword: str, days: int = 30, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search news by keyword.

        Args:
            keyword: Search keyword
            days: Days to search back
            limit: Maximum results

        Returns:
            List of matching news articles
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        cursor.execute(
            """
            SELECT * FROM news_articles
            WHERE (headline LIKE ? OR summary LIKE ? OR content LIKE ?)
            AND published_at >= ?
            ORDER BY published_at DESC
            LIMIT ?
        """,
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", start_date, limit),
        )

        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()

        return results

    def get_sentiment_analysis(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """
        Get sentiment analysis for symbol.

        Args:
            symbol: Trading symbol
            days: Days to analyze

        Returns:
            Sentiment statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # Get daily sentiment
        cursor.execute(
            """
            SELECT * FROM sentiment_history
            WHERE symbol = ? AND date >= ?
            ORDER BY date DESC
        """,
            (symbol, start_date),
        )

        columns = [desc[0] for desc in cursor.description]
        daily_sentiment = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Get overall statistics
        cursor.execute(
            """
            SELECT 
                SUM(positive_count) as total_positive,
                SUM(negative_count) as total_negative,
                SUM(neutral_count) as total_neutral,
                SUM(total_articles) as total_articles,
                AVG(avg_sentiment_score) as overall_sentiment
            FROM sentiment_history
            WHERE symbol = ? AND date >= ?
        """,
            (symbol, start_date),
        )

        overall = cursor.fetchone()

        conn.close()

        if overall and overall[3]:
            (
                total_positive,
                total_negative,
                total_neutral,
                total_articles,
                overall_sentiment,
            ) = overall

            return {
                "symbol": symbol,
                "period_days": days,
                "total_articles": total_articles,
                "positive_count": total_positive,
                "negative_count": total_negative,
                "neutral_count": total_neutral,
                "positive_pct": (
                    (total_positive / total_articles * 100) if total_articles else 0
                ),
                "negative_pct": (
                    (total_negative / total_articles * 100) if total_articles else 0
                ),
                "neutral_pct": (
                    (total_neutral / total_articles * 100) if total_articles else 0
                ),
                "overall_sentiment": overall_sentiment,
                "sentiment_rating": (
                    "BULLISH"
                    if overall_sentiment > 0.2
                    else "BEARISH" if overall_sentiment < -0.2 else "NEUTRAL"
                ),
                "daily_breakdown": daily_sentiment,
            }
        else:
            # No data, fetch some news first
            self.fetch_latest_news(symbol=symbol, limit=10)
            return self.get_sentiment_analysis(symbol, days)

    def add_to_watchlist(
        self, symbol: str, keywords: Optional[List[str]] = None, priority: str = "HIGH"
    ) -> bool:
        """Add symbol to news watchlist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        keywords_str = ",".join(keywords) if keywords else ""

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO news_watchlist
                (symbol, alert_priority, keywords)
                VALUES (?, ?, ?)
            """,
                (symbol, priority, keywords_str),
            )

            conn.commit()
            logger.info(f"Added {symbol} to watchlist")
            return True
        except Exception as e:
            logger.error(f"Failed to add to watchlist: {e}")
            return False
        finally:
            conn.close()

    def monitor_news(
        self,
        symbols: Optional[List[str]] = None,
        interval: int = 300,
        duration: Optional[int] = None,
    ):
        """
        Monitor news in real-time.

        Args:
            symbols: List of symbols to monitor
            interval: Check interval in seconds
            duration: Total duration in seconds
        """
        import time

        start_time = time.time()
        print(f"\n🔍 Monitoring news (checking every {interval}s)")
        if symbols:
            print(f"Watching: {', '.join(symbols)}")
        print("Press Ctrl+C to stop\n")

        last_check = datetime.now()

        try:
            while True:
                # Fetch latest news
                for symbol in symbols or [None]:
                    news = self.fetch_latest_news(symbol=symbol, limit=5)

                    # Check for new articles since last check
                    new_articles = [
                        n
                        for n in news
                        if n.get("published_at")
                        and datetime.strptime(n["published_at"], "%Y-%m-%d %H:%M:%S")
                        > last_check
                    ]

                    if new_articles:
                        print(f"\n🚨 NEW ARTICLES ({len(new_articles)})")
                        print("-" * 80)
                        for article in new_articles:
                            sentiment_emoji = (
                                "🟢"
                                if article["sentiment"] == "POSITIVE"
                                else (
                                    "🔴" if article["sentiment"] == "NEGATIVE" else "⚪"
                                )
                            )
                            print(
                                f"{sentiment_emoji} [{article.get('published_at')}] {article.get('headline')}"
                            )
                            print(f"   {article.get('summary', '')[:100]}...")
                        print()

                last_check = datetime.now()
                print(
                    f"✓ Checked at {last_check.strftime('%H:%M:%S')} - Next check in {interval}s"
                )

                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    print("\n✅ Monitoring duration completed")
                    break

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped by user")

    def display_news(self, news: List[Dict[str, Any]], title: str = "NEWS ARTICLES"):
        """Display news articles in formatted view."""
        if not news:
            print("\n❌ No news found")
            return

        print("\n" + "=" * 100)
        print(title)
        print("=" * 100)

        for i, article in enumerate(news, 1):
            sentiment = article.get("sentiment", "NEUTRAL")
            sentiment_emoji = (
                "🟢"
                if sentiment == "POSITIVE"
                else "🔴" if sentiment == "NEGATIVE" else "⚪"
            )

            print(f"\n{i}. {sentiment_emoji} {article.get('headline')}")
            print(
                f"   Published: {article.get('published_at')} | Source: {article.get('source')}"
            )
            if article.get("symbols"):
                print(f"   Symbols: {article.get('symbols')}")
            print(f"   {article.get('summary', '')[:150]}...")

        print("\n" + "=" * 100)
        print(f"Total articles: {len(news)}\n")

    def display_sentiment(self, sentiment_data: Dict[str, Any]):
        """Display sentiment analysis results."""
        print("\n" + "=" * 80)
        print(f"SENTIMENT ANALYSIS - {sentiment_data['symbol']}")
        print("=" * 80)
        print(f"Period: Last {sentiment_data['period_days']} days")
        print(f"Total Articles: {sentiment_data['total_articles']}")
        print()
        print(f"📊 SENTIMENT BREAKDOWN:")
        print(
            f"   🟢 Positive: {sentiment_data['positive_count']} ({sentiment_data['positive_pct']:.1f}%)"
        )
        print(
            f"   🔴 Negative: {sentiment_data['negative_count']} ({sentiment_data['negative_pct']:.1f}%)"
        )
        print(
            f"   ⚪ Neutral:  {sentiment_data['neutral_count']} ({sentiment_data['neutral_pct']:.1f}%)"
        )
        print()
        print(f"📈 OVERALL SENTIMENT:")
        print(f"   Score: {sentiment_data['overall_sentiment']:.2f}")
        print(f"   Rating: {sentiment_data['sentiment_rating']}")
        print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="News Alerts Manager - Real-time market news monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=[
            "latest",
            "breaking",
            "search",
            "sentiment",
            "monitor",
            "add-watchlist",
        ],
        help="Action to perform",
    )

    parser.add_argument("--symbol", type=str, help="Trading symbol")

    parser.add_argument("--symbols", type=str, help="Comma-separated symbols")

    parser.add_argument("--keyword", type=str, help="Search keyword")

    parser.add_argument(
        "--limit", type=int, default=10, help="Number of articles (default: 10)"
    )

    parser.add_argument(
        "--days", type=int, default=7, help="Days to look back (default: 7)"
    )

    parser.add_argument(
        "--minutes",
        type=int,
        default=30,
        help="Minutes for breaking news (default: 30)",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Monitoring interval in seconds (default: 300)",
    )

    parser.add_argument("--duration", type=int, help="Monitoring duration in seconds")

    parser.add_argument(
        "--priority",
        type=str,
        default="HIGH",
        choices=["HIGH", "MEDIUM", "LOW"],
        help="Alert priority (default: HIGH)",
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default="market_data.db",
        help="Database path (default: market_data.db)",
    )

    args = parser.parse_args()

    # Initialize manager
    manager = NewsAlertsManager(db_path=args.db_path)

    # Execute action
    if args.action == "latest":
        news = manager.fetch_latest_news(symbol=args.symbol, limit=args.limit)
        manager.display_news(
            news, title=f"LATEST NEWS - {args.symbol if args.symbol else 'ALL'}"
        )

    elif args.action == "breaking":
        news = manager.get_breaking_news(minutes=args.minutes)
        manager.display_news(news, title=f"BREAKING NEWS (Last {args.minutes} minutes)")

    elif args.action == "search":
        if not args.keyword:
            print("❌ Error: --keyword required for search")
            sys.exit(1)

        news = manager.search_news(
            keyword=args.keyword, days=args.days, limit=args.limit
        )
        manager.display_news(news, title=f"SEARCH RESULTS: '{args.keyword}'")

    elif args.action == "sentiment":
        if not args.symbol:
            print("❌ Error: --symbol required for sentiment analysis")
            sys.exit(1)

        sentiment = manager.get_sentiment_analysis(symbol=args.symbol, days=args.days)
        manager.display_sentiment(sentiment)

    elif args.action == "monitor":
        symbols = args.symbols.split(",") if args.symbols else None
        manager.monitor_news(
            symbols=symbols, interval=args.interval, duration=args.duration
        )

    elif args.action == "add-watchlist":
        if not args.symbol:
            print("❌ Error: --symbol required for add-watchlist")
            sys.exit(1)

        success = manager.add_to_watchlist(symbol=args.symbol, priority=args.priority)

        if success:
            print(f"✅ Added {args.symbol} to watchlist with {args.priority} priority")
        else:
            print(f"❌ Failed to add to watchlist")


if __name__ == "__main__":
    main()
