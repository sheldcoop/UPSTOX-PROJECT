#!/usr/bin/env python3
"""
Automated Strategy Runner
Connects backtest logic to live trading with signal generation and auto-execution.
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.risk_manager import RiskManager
from scripts.error_handler import with_retry, error_handler
from scripts.database_validator import DatabaseValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingSignal:
    """Represents a trading signal"""
    
    def __init__(self, symbol: str, action: str, price: float, 
                 quantity: int, confidence: float, strategy: str,
                 stop_loss: Optional[float] = None, 
                 take_profit: Optional[float] = None):
        self.symbol = symbol
        self.action = action  # 'BUY' or 'SELL'
        self.price = price
        self.quantity = quantity
        self.confidence = confidence  # 0.0 to 1.0
        self.strategy = strategy
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'action': self.action,
            'price': self.price,
            'quantity': self.quantity,
            'confidence': self.confidence,
            'strategy': self.strategy,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'timestamp': self.timestamp.isoformat()
        }


class StrategyRunner:
    """
    Automated trading strategy execution engine.
    
    Features:
    - Signal generation from technical indicators
    - Strategy backtesting integration
    - Live order execution with risk management
    - Strategy performance monitoring
    - Multi-strategy support
    """
    
    def __init__(self, db_path: str = "market_data.db", dry_run: bool = True):
        self.db_path = db_path
        self.dry_run = dry_run  # Paper trading mode
        self.risk_manager = RiskManager(db_path=db_path)
        self.validator = DatabaseValidator(db_path=db_path)
        self.active_strategies: Dict[str, bool] = {}
        self._init_strategy_db()
    
    def _init_strategy_db(self):
        """Initialize database tables for strategy tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Strategy configurations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                parameters TEXT,  -- JSON
                enabled BOOLEAN DEFAULT 1,
                max_positions INTEGER DEFAULT 3,
                risk_per_trade REAL DEFAULT 0.02,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trading signals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                confidence REAL,
                stop_loss REAL,
                take_profit REAL,
                signal_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                executed BOOLEAN DEFAULT 0,
                execution_time DATETIME,
                execution_price REAL,
                order_id TEXT,
                pnl REAL,
                FOREIGN KEY (strategy_name) REFERENCES strategies(name)
            )
        """)
        
        # Strategy performance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                metric_date DATE DEFAULT CURRENT_DATE,
                total_signals INTEGER DEFAULT 0,
                executed_signals INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                win_rate REAL,
                avg_win REAL,
                avg_loss REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                FOREIGN KEY (strategy_name) REFERENCES strategies(name)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def register_strategy(self, name: str, description: str, 
                         parameters: Dict[str, Any],
                         max_positions: int = 3,
                         risk_per_trade: float = 0.02) -> int:
        """Register a new trading strategy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO strategies
            (name, description, parameters, max_positions, risk_per_trade)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            description,
            json.dumps(parameters),
            max_positions,
            risk_per_trade
        ))
        
        strategy_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.active_strategies[name] = True
        logger.info(f"Strategy registered: {name}")
        
        return strategy_id
    
    def generate_rsi_signals(self, symbol: str, period: int = 14,
                            oversold: int = 30, overbought: int = 70) -> Optional[TradingSignal]:
        """
        Generate trading signals based on RSI indicator.
        
        Args:
            symbol: Trading symbol
            period: RSI period (default 14)
            oversold: Oversold threshold (default 30)
            overbought: Overbought threshold (default 70)
        
        Returns:
            TradingSignal or None
        """
        # Get recent price data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT close, timestamp
            FROM market_data
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (symbol, period + 1))
        
        prices = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if len(prices) < period + 1:
            logger.warning(f"Insufficient data for RSI calculation: {symbol}")
            return None
        
        # Calculate RSI
        rsi = self._calculate_rsi(prices, period)
        current_price = prices[0]
        
        # Generate signal
        if rsi < oversold:
            # Oversold - BUY signal
            confidence = (oversold - rsi) / oversold
            stop_loss = current_price * 0.95  # 5% stop-loss
            take_profit = current_price * 1.10  # 10% target
            
            # Calculate position size
            account_balance = 100000  # TODO: Get from account
            position_sizing = self.risk_manager.calculate_position_size(
                symbol, current_price, stop_loss, account_balance
            )
            
            return TradingSignal(
                symbol=symbol,
                action='BUY',
                price=current_price,
                quantity=position_sizing['quantity'],
                confidence=confidence,
                strategy='RSI_Mean_Reversion',
                stop_loss=stop_loss,
                take_profit=take_profit
            )
        
        elif rsi > overbought:
            # Overbought - SELL signal (for existing positions)
            confidence = (rsi - overbought) / (100 - overbought)
            
            return TradingSignal(
                symbol=symbol,
                action='SELL',
                price=current_price,
                quantity=0,  # Will be determined by existing position
                confidence=confidence,
                strategy='RSI_Mean_Reversion',
                stop_loss=None,
                take_profit=None
            )
        
        return None
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0
        
        # Calculate price changes
        changes = [prices[i] - prices[i + 1] for i in range(len(prices) - 1)]
        
        # Separate gains and losses
        gains = [max(c, 0) for c in changes[:period]]
        losses = [abs(min(c, 0)) for c in changes[:period]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_macd_signals(self, symbol: str, 
                             fast_period: int = 12,
                             slow_period: int = 26, 
                             signal_period: int = 9) -> Optional[TradingSignal]:
        """
        Generate trading signals based on MACD indicator.
        
        Returns:
            TradingSignal or None
        """
        # Get recent price data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT close
            FROM market_data
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (symbol, slow_period + signal_period))
        
        prices = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if len(prices) < slow_period + signal_period:
            logger.warning(f"Insufficient data for MACD calculation: {symbol}")
            return None
        
        # Calculate MACD
        macd_line, signal_line = self._calculate_macd(prices, fast_period, slow_period, signal_period)
        current_price = prices[0]
        
        # Generate signal on crossover
        if macd_line > signal_line:
            # Bullish crossover - BUY signal
            confidence = abs(macd_line - signal_line) / current_price
            stop_loss = current_price * 0.97  # 3% stop-loss
            take_profit = current_price * 1.06  # 6% target
            
            account_balance = 100000
            position_sizing = self.risk_manager.calculate_position_size(
                symbol, current_price, stop_loss, account_balance
            )
            
            return TradingSignal(
                symbol=symbol,
                action='BUY',
                price=current_price,
                quantity=position_sizing['quantity'],
                confidence=min(confidence, 1.0),
                strategy='MACD_Crossover',
                stop_loss=stop_loss,
                take_profit=take_profit
            )
        
        elif macd_line < signal_line:
            # Bearish crossover - SELL signal
            confidence = abs(macd_line - signal_line) / current_price
            
            return TradingSignal(
                symbol=symbol,
                action='SELL',
                price=current_price,
                quantity=0,
                confidence=min(confidence, 1.0),
                strategy='MACD_Crossover',
                stop_loss=None,
                take_profit=None
            )
        
        return None
    
    def _calculate_macd(self, prices: List[float], fast: int, slow: int, signal: int) -> Tuple[float, float]:
        """Calculate MACD line and signal line"""
        if len(prices) < slow:
            return 0.0, 0.0
        
        # Calculate EMAs
        fast_ema = self._calculate_ema(prices[:fast + 1], fast)
        slow_ema = self._calculate_ema(prices[:slow + 1], slow)
        
        # MACD line
        macd_line = fast_ema - slow_ema
        
        # Signal line (simplified - should be EMA of MACD)
        signal_line = macd_line * 0.9  # Approximation
        
        return macd_line, signal_line
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if not prices:
            return 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[-1]
        
        for price in reversed(prices[:-1]):
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def execute_signal(self, signal: TradingSignal) -> Dict[str, Any]:
        """
        Execute a trading signal.
        
        Returns:
            Execution result with order_id and status
        """
        # Validate signal
        if signal.confidence < 0.5:
            logger.info(f"Signal confidence too low ({signal.confidence:.2f}), skipping")
            return {'status': 'SKIPPED', 'reason': 'Low confidence'}
        
        # Check circuit breaker
        daily_loss_status = self.risk_manager.check_daily_loss()
        if daily_loss_status['circuit_breaker_active']:
            logger.warning("Circuit breaker active, skipping signal")
            return {'status': 'BLOCKED', 'reason': 'Circuit breaker active'}
        
        # Store signal
        signal_id = self._store_signal(signal)
        
        if self.dry_run:
            logger.info(
                f"[DRY RUN] Signal: {signal.action} {signal.quantity} {signal.symbol} "
                f"@ ₹{signal.price} (Strategy: {signal.strategy})"
            )
            return {
                'status': 'DRY_RUN',
                'signal_id': signal_id,
                'signal': signal.to_dict()
            }
        
        # Execute real order
        try:
            # TODO: Integrate with order_manager.py
            order_result = self._place_order(signal)
            
            # Update signal as executed
            self._mark_signal_executed(signal_id, order_result['order_id'], order_result['price'])
            
            # Set stop-loss if specified
            if signal.stop_loss and signal.action == 'BUY':
                self.risk_manager.set_stop_loss(
                    symbol=signal.symbol,
                    entry_price=order_result['price'],
                    stop_loss_price=signal.stop_loss,
                    quantity=signal.quantity,
                    order_id=order_result['order_id']
                )
            
            logger.info(
                f"Signal executed: {signal.action} {signal.quantity} {signal.symbol} "
                f"@ ₹{order_result['price']} (Order ID: {order_result['order_id']})"
            )
            
            return {
                'status': 'EXECUTED',
                'signal_id': signal_id,
                'order_id': order_result['order_id'],
                'price': order_result['price']
            }
        
        except Exception as e:
            logger.error(f"Failed to execute signal: {str(e)}")
            return {
                'status': 'FAILED',
                'signal_id': signal_id,
                'error': str(e)
            }
    
    def _store_signal(self, signal: TradingSignal) -> int:
        """Store trading signal in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trading_signals
            (strategy_name, symbol, action, price, quantity, confidence, 
             stop_loss, take_profit, signal_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal.strategy,
            signal.symbol,
            signal.action,
            signal.price,
            signal.quantity,
            signal.confidence,
            signal.stop_loss,
            signal.take_profit,
            signal.timestamp
        ))
        
        signal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return signal_id
    
    def _mark_signal_executed(self, signal_id: int, order_id: str, execution_price: float):
        """Mark a signal as executed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE trading_signals
            SET executed = 1,
                execution_time = CURRENT_TIMESTAMP,
                execution_price = ?,
                order_id = ?
            WHERE id = ?
        """, (execution_price, order_id, signal_id))
        
        conn.commit()
        conn.close()
    
    def _place_order(self, signal: TradingSignal) -> Dict[str, Any]:
        """
        Place an order based on signal.
        This should integrate with order_manager.py in production.
        """
        # Simulated order placement
        import uuid
        
        return {
            'order_id': f"ORD_{uuid.uuid4().hex[:8].upper()}",
            'status': 'COMPLETE',
            'price': signal.price,
            'quantity': signal.quantity
        }
    
    def run_strategy(self, strategy_name: str, symbols: List[str]) -> List[TradingSignal]:
        """
        Run a strategy on multiple symbols.
        
        Returns:
            List of generated signals
        """
        signals = []
        
        for symbol in symbols:
            if strategy_name == 'RSI_Mean_Reversion':
                signal = self.generate_rsi_signals(symbol)
            elif strategy_name == 'MACD_Crossover':
                signal = self.generate_macd_signals(symbol)
            else:
                logger.warning(f"Unknown strategy: {strategy_name}")
                continue
            
            if signal:
                signals.append(signal)
                logger.info(
                    f"Signal generated: {signal.action} {signal.symbol} "
                    f"@ ₹{signal.price:.2f} (Confidence: {signal.confidence:.2f})"
                )
        
        return signals
    
    def get_strategy_performance(self, strategy_name: str, days: int = 30) -> Dict[str, Any]:
        """Get performance metrics for a strategy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all executed signals
        cursor.execute("""
            SELECT action, price, execution_price, quantity, pnl
            FROM trading_signals
            WHERE strategy_name = ?
            AND executed = 1
            AND signal_time >= datetime('now', '-{} days')
        """.format(days), (strategy_name,))
        
        trades = cursor.fetchall()
        conn.close()
        
        if not trades:
            return {
                'strategy': strategy_name,
                'total_trades': 0,
                'message': 'No executed trades in this period'
            }
        
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t[4] and t[4] > 0)
        losing_trades = sum(1 for t in trades if t[4] and t[4] < 0)
        
        total_pnl = sum(t[4] for t in trades if t[4])
        
        wins = [t[4] for t in trades if t[4] and t[4] > 0]
        losses = [t[4] for t in trades if t[4] and t[4] < 0]
        
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'strategy': strategy_name,
            'period_days': days,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0
        }


def main():
    """Test strategy runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Strategy Runner")
    parser.add_argument('--action', 
                       choices=['register', 'run', 'performance', 'signals'],
                       default='signals',
                       help='Action to perform')
    parser.add_argument('--strategy', type=str, default='RSI_Mean_Reversion',
                       help='Strategy name')
    parser.add_argument('--symbols', type=str, default='INFY,TCS',
                       help='Comma-separated symbols')
    parser.add_argument('--live', action='store_true',
                       help='Run in live mode (default: dry run)')
    
    args = parser.parse_args()
    
    runner = StrategyRunner(dry_run=not args.live)
    
    if args.action == 'register':
        strategy_id = runner.register_strategy(
            name='RSI_Mean_Reversion',
            description='Mean reversion strategy using RSI',
            parameters={'period': 14, 'oversold': 30, 'overbought': 70},
            max_positions=3,
            risk_per_trade=0.02
        )
        print(f"Strategy registered: ID {strategy_id}")
    
    elif args.action == 'run':
        symbols = args.symbols.split(',')
        signals = runner.run_strategy(args.strategy, symbols)
        
        print(f"\n=== Strategy Run: {args.strategy} ===")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Signals Generated: {len(signals)}")
        
        for signal in signals:
            result = runner.execute_signal(signal)
            print(f"\n{signal.action} {signal.symbol}")
            print(f"  Price: ₹{signal.price:.2f}")
            print(f"  Quantity: {signal.quantity}")
            print(f"  Confidence: {signal.confidence:.2f}")
            print(f"  Status: {result['status']}")
    
    elif args.action == 'performance':
        perf = runner.get_strategy_performance(args.strategy, days=30)
        
        print(f"\n=== Strategy Performance: {perf['strategy']} ===")
        print(f"Period: {perf.get('period_days', 30)} days")
        print(f"Total Trades: {perf['total_trades']}")
        print(f"Win Rate: {perf.get('win_rate', 0):.1f}%")
        print(f"Total P&L: ₹{perf.get('total_pnl', 0):,.2f}")
        print(f"Avg Win: ₹{perf.get('avg_win', 0):,.2f}")
        print(f"Avg Loss: ₹{perf.get('avg_loss', 0):,.2f}")
    
    elif args.action == 'signals':
        symbols = args.symbols.split(',')
        signals = runner.run_strategy(args.strategy, symbols)
        
        print(f"\n=== Signals for {args.strategy} ===")
        if signals:
            for signal in signals:
                print(f"\n{signal.action} {signal.symbol} @ ₹{signal.price:.2f}")
                print(f"  Quantity: {signal.quantity}")
                print(f"  Confidence: {signal.confidence:.2f}")
                print(f"  Stop Loss: ₹{signal.stop_loss:.2f}" if signal.stop_loss else "  No SL")
        else:
            print("No signals generated")


if __name__ == "__main__":
    main()
