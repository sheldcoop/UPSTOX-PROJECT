#!/usr/bin/env python3
"""
Performance Analytics Dashboard
Comprehensive trading performance analysis with metrics, equity curve, and trade journal.
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceAnalytics:
    """
    Trading performance analytics and reporting.
    
    Features:
    - Win rate and profit factor
    - Sharpe ratio and Sortino ratio
    - Maximum drawdown analysis
    - Equity curve generation
    - Trade journal with detailed metrics
    - Monthly/yearly performance breakdown
    """
    
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self._init_analytics_db()
    
    def _init_analytics_db(self):
        """Initialize analytics database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trade journal
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_date DATE NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                entry_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                exit_time DATETIME,
                pnl REAL,
                pnl_percentage REAL,
                strategy TEXT,
                notes TEXT,
                commission REAL DEFAULT 0,
                status TEXT DEFAULT 'OPEN',
                UNIQUE(symbol, entry_time)
            )
        """)
        
        # Daily performance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                performance_date DATE UNIQUE NOT NULL,
                starting_balance REAL,
                ending_balance REAL,
                pnl REAL,
                pnl_percentage REAL,
                trades_count INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_commission REAL DEFAULT 0
            )
        """)
        
        # Monthly performance summary
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                starting_balance REAL,
                ending_balance REAL,
                pnl REAL,
                pnl_percentage REAL,
                trades_count INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                win_rate REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                UNIQUE(year, month)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_trade(self, symbol: str, action: str, quantity: int,
                    entry_price: float, exit_price: Optional[float] = None,
                    strategy: Optional[str] = None, notes: Optional[str] = None,
                    commission: float = 0) -> int:
        """
        Record a trade in the journal.
        
        Returns:
            Trade ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        pnl = None
        pnl_percentage = None
        status = 'OPEN'
        
        if exit_price is not None:
            if action == 'BUY':
                pnl = (exit_price - entry_price) * quantity - commission
            else:  # SELL
                pnl = (entry_price - exit_price) * quantity - commission
            
            pnl_percentage = (pnl / (entry_price * quantity)) * 100
            status = 'CLOSED'
        
        cursor.execute("""
            INSERT INTO trade_journal
            (trade_date, symbol, action, quantity, entry_price, exit_price,
             pnl, pnl_percentage, strategy, notes, commission, status)
            VALUES (DATE('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol, action, quantity, entry_price, exit_price,
            pnl, pnl_percentage, strategy, notes, commission, status
        ))
        
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Trade recorded: {action} {quantity} {symbol} @ ₹{entry_price}")
        
        return trade_id
    
    def close_trade(self, trade_id: int, exit_price: float) -> Dict[str, Any]:
        """Close an open trade and calculate P&L"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get trade details
        cursor.execute("""
            SELECT symbol, action, quantity, entry_price, commission
            FROM trade_journal
            WHERE id = ? AND status = 'OPEN'
        """, (trade_id,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return {'error': 'Trade not found or already closed'}
        
        symbol, action, quantity, entry_price, commission = result
        
        # Calculate P&L
        if action == 'BUY':
            pnl = (exit_price - entry_price) * quantity - commission
        else:
            pnl = (entry_price - exit_price) * quantity - commission
        
        pnl_percentage = (pnl / (entry_price * quantity)) * 100
        
        # Update trade
        cursor.execute("""
            UPDATE trade_journal
            SET exit_price = ?,
                exit_time = CURRENT_TIMESTAMP,
                pnl = ?,
                pnl_percentage = ?,
                status = 'CLOSED'
            WHERE id = ?
        """, (exit_price, pnl, pnl_percentage, trade_id))
        
        conn.commit()
        conn.close()
        
        return {
            'trade_id': trade_id,
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_percentage': pnl_percentage
        }
    
    def get_win_rate(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Calculate win rate and related metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(CASE WHEN pnl = 0 THEN 1 ELSE 0 END) as breakeven_trades
            FROM trade_journal
            WHERE status = 'CLOSED'
        """
        
        if days:
            query += f" AND trade_date >= DATE('now', '-{days} days')"
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        total_trades = result[0] or 0
        winning_trades = result[1] or 0
        losing_trades = result[2] or 0
        breakeven_trades = result[3] or 0
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        conn.close()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'breakeven_trades': breakeven_trades,
            'win_rate': win_rate
        }
    
    def get_profit_factor(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Calculate profit factor and average win/loss"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT pnl
            FROM trade_journal
            WHERE status = 'CLOSED' AND pnl IS NOT NULL
        """
        
        if days:
            query += f" AND trade_date >= DATE('now', '-{days} days')"
        
        cursor.execute(query)
        
        pnls = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not pnls:
            return {
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'total_pnl': 0
            }
        
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        total_wins = sum(wins)
        total_losses = abs(sum(losses))
        
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0
        
        return {
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_pnl': sum(pnls),
            'total_wins': total_wins,
            'total_losses': total_losses
        }
    
    def calculate_sharpe_ratio(self, days: int = 30, risk_free_rate: float = 0.05) -> float:
        """Calculate Sharpe ratio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pnl
            FROM trade_journal
            WHERE status = 'CLOSED'
            AND trade_date >= DATE('now', '-{} days')
            ORDER BY trade_date
        """.format(days))
        
        pnls = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if len(pnls) < 2:
            return 0.0
        
        # Calculate returns (simplified - assumes constant capital)
        starting_capital = 100000
        returns = [pnl / starting_capital for pnl in pnls]
        
        # Daily risk-free rate
        daily_rf = risk_free_rate / 252
        
        # Excess returns
        excess_returns = [r - daily_rf for r in returns]
        
        # Mean and std dev
        mean_excess = sum(excess_returns) / len(excess_returns)
        
        variance = sum((r - mean_excess) ** 2 for r in excess_returns) / (len(excess_returns) - 1)
        std_dev = math.sqrt(variance)
        
        if std_dev == 0:
            return 0.0
        
        # Annualized Sharpe ratio
        sharpe = (mean_excess / std_dev) * math.sqrt(252)
        
        return sharpe
    
    def calculate_sortino_ratio(self, days: int = 30, risk_free_rate: float = 0.05) -> float:
        """Calculate Sortino ratio (uses only downside deviation)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pnl
            FROM trade_journal
            WHERE status = 'CLOSED'
            AND trade_date >= DATE('now', '-{} days')
            ORDER BY trade_date
        """.format(days))
        
        pnls = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if len(pnls) < 2:
            return 0.0
        
        starting_capital = 100000
        returns = [pnl / starting_capital for pnl in pnls]
        
        daily_rf = risk_free_rate / 252
        excess_returns = [r - daily_rf for r in returns]
        
        mean_excess = sum(excess_returns) / len(excess_returns)
        
        # Only consider negative returns for downside deviation
        downside_returns = [min(r - daily_rf, 0) for r in returns]
        downside_variance = sum(r ** 2 for r in downside_returns) / len(downside_returns)
        downside_std = math.sqrt(downside_variance)
        
        if downside_std == 0:
            return 0.0
        
        sortino = (mean_excess / downside_std) * math.sqrt(252)
        
        return sortino
    
    def get_equity_curve(self, days: int = 30) -> List[Dict[str, Any]]:
        """Generate equity curve data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT trade_date, SUM(pnl) as daily_pnl
            FROM trade_journal
            WHERE status = 'CLOSED'
            AND trade_date >= DATE('now', '-{} days')
            GROUP BY trade_date
            ORDER BY trade_date
        """.format(days))
        
        daily_results = cursor.fetchall()
        conn.close()
        
        starting_capital = 100000
        equity_curve = []
        current_equity = starting_capital
        
        for trade_date, daily_pnl in daily_results:
            current_equity += daily_pnl or 0
            
            equity_curve.append({
                'date': trade_date,
                'equity': current_equity,
                'pnl': daily_pnl,
                'return_pct': ((current_equity - starting_capital) / starting_capital) * 100
            })
        
        return equity_curve
    
    def get_max_drawdown(self, days: int = 30) -> Dict[str, Any]:
        """Calculate maximum drawdown"""
        equity_curve = self.get_equity_curve(days)
        
        if not equity_curve:
            return {
                'max_drawdown': 0,
                'max_drawdown_pct': 0
            }
        
        equities = [point['equity'] for point in equity_curve]
        
        max_dd = 0
        max_dd_pct = 0
        peak = equities[0]
        peak_idx = 0
        trough_idx = 0
        
        for i, equity in enumerate(equities):
            if equity > peak:
                peak = equity
                peak_idx = i
            
            dd = peak - equity
            dd_pct = (dd / peak * 100) if peak > 0 else 0
            
            if dd_pct > max_dd_pct:
                max_dd = dd
                max_dd_pct = dd_pct
                trough_idx = i
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd_pct,
            'peak_date': equity_curve[peak_idx]['date'] if equity_curve else None,
            'trough_date': equity_curve[trough_idx]['date'] if equity_curve else None
        }
    
    def get_comprehensive_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        win_rate_data = self.get_win_rate(days)
        profit_factor_data = self.get_profit_factor(days)
        sharpe = self.calculate_sharpe_ratio(days)
        sortino = self.calculate_sortino_ratio(days)
        max_dd = self.get_max_drawdown(days)
        
        return {
            'period_days': days,
            'total_trades': win_rate_data['total_trades'],
            'winning_trades': win_rate_data['winning_trades'],
            'losing_trades': win_rate_data['losing_trades'],
            'win_rate': win_rate_data['win_rate'],
            'profit_factor': profit_factor_data['profit_factor'],
            'avg_win': profit_factor_data['avg_win'],
            'avg_loss': profit_factor_data['avg_loss'],
            'total_pnl': profit_factor_data['total_pnl'],
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown': max_dd['max_drawdown'],
            'max_drawdown_pct': max_dd['max_drawdown_pct']
        }
    
    def get_trade_distribution(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Analyze trade distribution"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT pnl
            FROM trade_journal
            WHERE status = 'CLOSED' AND pnl IS NOT NULL
        """
        
        if days:
            query += f" AND trade_date >= DATE('now', '-{days} days')"
        
        cursor.execute(query)
        
        pnls = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not pnls:
            return {}
        
        # Distribution bins
        bins = {
            'large_wins': sum(1 for p in pnls if p > 5000),
            'medium_wins': sum(1 for p in pnls if 1000 < p <= 5000),
            'small_wins': sum(1 for p in pnls if 0 < p <= 1000),
            'small_losses': sum(1 for p in pnls if -1000 <= p < 0),
            'medium_losses': sum(1 for p in pnls if -5000 <= p < -1000),
            'large_losses': sum(1 for p in pnls if p < -5000)
        }
        
        return bins
    
    def get_monthly_summary(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get monthly performance summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT year, month, ending_balance, pnl, pnl_percentage,
                   trades_count, win_rate, sharpe_ratio, max_drawdown
            FROM monthly_performance
        """
        
        if year:
            query += f" WHERE year = {year}"
        
        query += " ORDER BY year DESC, month DESC"
        
        cursor.execute(query)
        
        months = []
        for row in cursor.fetchall():
            months.append({
                'year': row[0],
                'month': row[1],
                'ending_balance': row[2],
                'pnl': row[3],
                'pnl_percentage': row[4],
                'trades_count': row[5],
                'win_rate': row[6],
                'sharpe_ratio': row[7],
                'max_drawdown': row[8]
            })
        
        conn.close()
        
        return months


def main():
    """Test performance analytics"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Analytics")
    parser.add_argument('--action',
                       choices=['report', 'equity', 'trade', 'distribution'],
                       default='report',
                       help='Action to perform')
    parser.add_argument('--days', type=int, default=30,
                       help='Days to analyze')
    
    args = parser.parse_args()
    
    analytics = PerformanceAnalytics()
    
    if args.action == 'report':
        report = analytics.get_comprehensive_report(days=args.days)
        
        print(f"\n=== Performance Report ({args.days} Days) ===")
        print(f"\nTrading Activity:")
        print(f"  Total Trades: {report['total_trades']}")
        print(f"  Winning Trades: {report['winning_trades']}")
        print(f"  Losing Trades: {report['losing_trades']}")
        print(f"  Win Rate: {report['win_rate']:.1f}%")
        
        print(f"\nProfitability:")
        print(f"  Total P&L: ₹{report['total_pnl']:,.2f}")
        print(f"  Avg Win: ₹{report['avg_win']:,.2f}")
        print(f"  Avg Loss: ₹{report['avg_loss']:,.2f}")
        print(f"  Profit Factor: {report['profit_factor']:.2f}")
        
        print(f"\nRisk Metrics:")
        print(f"  Sharpe Ratio: {report['sharpe_ratio']:.2f}")
        print(f"  Sortino Ratio: {report['sortino_ratio']:.2f}")
        print(f"  Max Drawdown: {report['max_drawdown_pct']:.2f}%")
    
    elif args.action == 'equity':
        curve = analytics.get_equity_curve(days=args.days)
        
        print(f"\n=== Equity Curve ({len(curve)} days) ===")
        for point in curve[-10:]:  # Last 10 days
            print(f"{point['date']}: ₹{point['equity']:,.2f} "
                  f"(P&L: ₹{point['pnl']:,.2f}, Return: {point['return_pct']:.2f}%)")
    
    elif args.action == 'trade':
        # Record a sample trade
        trade_id = analytics.record_trade(
            symbol='INFY',
            action='BUY',
            quantity=10,
            entry_price=1450.50,
            strategy='RSI_Mean_Reversion'
        )
        
        print(f"Trade recorded: ID {trade_id}")
        
        # Close it
        result = analytics.close_trade(trade_id, exit_price=1475.00)
        
        print(f"\nTrade closed:")
        print(f"  Entry: ₹{result['entry_price']}")
        print(f"  Exit: ₹{result['exit_price']}")
        print(f"  P&L: ₹{result['pnl']:.2f} ({result['pnl_percentage']:.2f}%)")
    
    elif args.action == 'distribution':
        dist = analytics.get_trade_distribution(days=args.days)
        
        print(f"\n=== Trade Distribution ({args.days} Days) ===")
        print(f"Large Wins (>₹5000): {dist.get('large_wins', 0)}")
        print(f"Medium Wins (₹1000-5000): {dist.get('medium_wins', 0)}")
        print(f"Small Wins (₹0-1000): {dist.get('small_wins', 0)}")
        print(f"Small Losses (₹0 to -₹1000): {dist.get('small_losses', 0)}")
        print(f"Medium Losses (-₹1000 to -₹5000): {dist.get('medium_losses', 0)}")
        print(f"Large Losses (<-₹5000): {dist.get('large_losses', 0)}")


if __name__ == "__main__":
    main()
