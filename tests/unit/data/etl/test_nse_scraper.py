"""
Unit tests for NSE Index Scraper
"""

import pytest
import pandas as pd
import sqlite3
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
from io import StringIO

# Fix import path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.data.etl.nse_index_scraper import NSEIndexScraper

class TestNSEIndexScraper:
    
    @pytest.fixture
    def mock_db(self):
        """Mock Database Connection"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn, mock_cursor

    @pytest.fixture
    def scraper(self, mock_db):
        """Initialize Scraper with mocked DB"""
        mock_conn, _ = mock_db
        with patch('backend.data.etl.nse_index_scraper.sqlite3.connect', return_value=mock_conn):
            scraper = NSEIndexScraper(db_path=":memory:")
            return scraper

    def test_get_index_config(self, scraper):
        """Test fetching index config from DB"""
        scraper.cursor.fetchone.return_value = (
            "NIFTY 50", "Nifty 50", "Broad", 50, "http://csv", "http://html"
        )
        
        config = scraper.get_index_config("NIFTY 50")
        assert config['index_code'] == "NIFTY 50"
        assert config['expected_count'] == 50
        scraper.cursor.execute.assert_called_once()

    @patch('backend.data.etl.nse_index_scraper.requests.Session')
    def test_download_csv_success(self, mock_session_cls, scraper):
        """Test successful CSV download and parsing"""
        csv_content = """Symbol,Company Name,Industry,ISIN Code
        RELIANCE,Reliance Industries Ltd.,Oil & Gas,INE002A01018
        TCS,Tata Consultancy Services Ltd.,IT,INE467B01029
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = csv_content
        
        mock_session = mock_session_cls.return_value
        mock_session.get.return_value = mock_response
        scraper.session = mock_session # Inject mock session
        
        df = scraper.download_csv("NIFTY 50", "http://url")
        
        assert df is not None
        assert len(df) == 2
        assert "symbol" in df.columns
        assert df.iloc[0]['symbol'] == "RELIANCE"
        assert df.iloc[0]['industry'] == "Oil & Gas"

    @patch('backend.data.etl.nse_index_scraper.requests.Session')
    def test_download_csv_failure(self, mock_session_cls, scraper):
        """Test CSV download failure handling"""
        mock_session = mock_session_cls.return_value
        mock_session.get.side_effect = Exception("Network Error")
        scraper.session = mock_session
        
        df = scraper.download_csv("NIFTY 50", "http://url")
        
        assert df is None
        # Verify error logged to DB
        scraper.cursor.execute.assert_called()
        args = scraper.cursor.execute.call_args[0]
        assert "INSERT INTO nse_index_scrape_log" in args[0]
        assert "FAILED" in args[0] or "FAILED" in str(args)

    def test_merge_csv_html_data(self, scraper):
        """Test merging CSV and HTML dataframes"""
        csv_data = pd.DataFrame({
            'symbol': ['RELIANCE', 'TCS'],
            'company_name': ['Reliance', 'TCS'],
            'industry_csv': ['Oil', 'IT'] # Raw CSV usually produces 'industry' but function handles renaming?
            # actually function expects 'industry' in both and renames them during merge?
            # Logic: "merged = csv_df.merge(html_df...)"
            # csv_df has: symbol, company_name, industry, isin
            # html_df has: symbol, sector, industry, weight
        })
        # Let's match the output of download_csv
        csv_df = pd.DataFrame({
            'symbol': ['RELIANCE', 'TCS'],
            'company_name': ['Reliance', 'TCS'],
            'industry': ['Oil_Generic', 'IT_Generic'],
            'isin': ['A', 'B']
        })
        
        html_df = pd.DataFrame({
            'symbol': ['RELIANCE', 'TCS'],
            'sector': ['Energy', 'Technology'],
            'industry': ['Refining', 'Services'],
            'weight': [10, 5]
        })
        
        merged = scraper.merge_csv_html_data(csv_df, html_df)
        
        # Should prefer HTML industry
        assert merged.iloc[0]['industry'] == "Refining"
        assert merged.iloc[0]['sector'] == "Energy"
        assert 'sector' in merged.columns
