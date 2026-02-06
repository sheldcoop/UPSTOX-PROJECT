"""
Unit tests for Symbol Resolver
"""

import pytest
import sqlite3
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Fix import path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.utils.helpers.symbol_resolver import resolve_symbols

class TestSymbolResolver:
    
    @patch('backend.utils.helpers.symbol_resolver.sqlite3.connect')
    def test_resolve_direct_list(self, mock_connect):
        """Test returning provided list directly"""
        symbols = ['RELIANCE', 'TCS']
        result = resolve_symbols(symbols=symbols)
        assert result == symbols
        mock_connect.assert_not_called()

    @patch('backend.utils.helpers.symbol_resolver.sqlite3.connect')
    def test_resolve_by_segment(self, mock_connect):
        """Test resolving by segment"""
        mock_cursor = Mock()
        mock_connect.return_value.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value.fetchall.return_value = [('INFY',), ('WIPRO',)]
        
        result = resolve_symbols(segment='NSE_EQ')
        
        assert len(result) == 2
        assert 'INFY' in result
        
        # Verify query construction
        args = mock_cursor.execute.call_args
        query, params = args[0]
        assert "segment=?" in query
        assert params[0] == 'NSE_EQ'

    @patch('backend.utils.helpers.symbol_resolver.sqlite3.connect')
    def test_resolve_complex_criteria(self, mock_connect):
        """Test resolving with multiple criteria"""
        mock_cursor = Mock()
        mock_connect.return_value.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value.fetchall.return_value = [('SBIN',)]
        
        criteria = {
            'segment': 'NSE_EQ',
            'instrument_type': ['EQ'],
            'has_fno': 1
        }
        
        result = resolve_symbols(criteria=criteria)
        
        assert len(result) == 1
        assert result[0] == 'SBIN'
        
        args = mock_cursor.execute.call_args
        query, params = args[0]
        assert "segment=?" in query
        assert "instrument_type IN (?)" in query
        assert "has_fno=?" in query
