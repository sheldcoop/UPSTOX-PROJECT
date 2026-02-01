#!/usr/bin/env python3
"""
Paper Trading System
Virtual portfolio with realistic order matching, slippage, and commission simulation.
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import uuid

from scripts.risk_manager import RiskManager
from scripts.performance_analytics import PerformanceAnalytics
from scripts.database_validator import DatabaseValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderStatus:
    """Order status constants"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class PaperTradingSystem:
    """
    Paper trading system with realistic simulation.
    
    Features:
    - Virtual portfolio management
    - Realistic order matching (limit/market orders)
    - Slippage simulation
    - Commission calculation
    - Real-time P&L tracking
    - Complete order book
    - Trade history
    """
    
    def __init__(self, db_path: str = "market_data.db",
                 starting_capital: float = 100000,
                 commission_per_trade: float = 20,
                 commission_percentage: float = 0.0003,
                 slippage: float = 0.0005):
        
        self.db_path = db_path
        self.starting_capital = starting_capital
        self.commission_per_trade = commission_per_trade
        self.commission_percentage = commission_percentage
        self.slippage = slippage
        
        self.risk_manager = RiskManager(db_path=db_path)
        self.analytics = PerformanceAnalytics(db_path=db_path)
        self.validator = DatabaseValidator(db_path=db_path)
        
        self._init_paper_trading_db()
        self._init_portfolio()
    
    def _init_paper_trading_db(self):
        """Initialize paper trading database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Paper trading portfolio
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cash_balance REAL NOT NULL,
                total_value REAL,
                unrealized_pnl REAL DEFAULT 0,
                realized_pnl REAL DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Paper trading positions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                quantity INTEGER NOT NULL,
                average_price REAL NOT NULL,
                current_price REAL,
                unrealized_pnl REAL,
                unrealized_pnl_pct REAL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Paper trading orders
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                order_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL,
                stop_price REAL,
                filled_quantity INTEGER DEFAULT 0,
                average_fill_price REAL,
                status TEXT DEFAULT 'PENDING',
                commission REAL DEFAULT 0,
                slippage REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                filled_at DATETIME
            )
        """)
        
        # Paper trading executions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                commission REAL DEFAULT 0,
                execution_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES paper_orders(order_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _init_portfolio(self):
        """Initialize portfolio if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM paper_portfolio")
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute("""
                INSERT INTO paper_portfolio (cash_balance, total_value)
                VALUES (?, ?)
            """, (self.starting_capital, self.starting_capital))
            
            conn.commit()
            logger.info(f"Paper trading portfolio initialized: ₹{self.starting_capital:,.2f}")
        
        conn.close()
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get portfolio
        cursor.execute("""
            SELECT cash_balance, total_value, unrealized_pnl, realized_pnl, total_pnl
            FROM paper_portfolio
            ORDER BY id DESC
            LIMIT 1
        """)
        
        portfolio = cursor.fetchone()
        
        # Get positions
        cursor.execute("""
            SELECT symbol, quantity, average_price, current_price, unrealized_pnl
            FROM paper_positions
            WHERE quantity > 0
        """)
        
        positions = []
        total_position_value = 0
        
        for row in cursor.fetchall():
            symbol, quantity, avg_price, current_price, unrealized_pnl = row
            position_value = quantity * (current_price or avg_price)
            total_position_value += position_value
            
            positions.append({
                'symbol': symbol,
                'quantity': quantity,
                'average_price': avg_price,
                'current_price': current_price,
                'position_value': position_value,
                'unrealized_pnl': unrealized_pnl
            })
        
        conn.close()
        
        cash_balance = portfolio[0] if portfolio else self.starting_capital
        total_value = cash_balance + total_position_value
        
        return {
            'cash_balance': cash_balance,
            'total_value': total_value,
            'position_value': total_position_value,
            'unrealized_pnl': portfolio[2] if portfolio else 0,
            'realized_pnl': portfolio[3] if portfolio else 0,
            'total_pnl': portfolio[4] if portfolio else 0,
            'return_pct': ((total_value - self.starting_capital) / self.starting_capital) * 100,
            'positions': positions
        }
    
    def place_order(self, symbol: str, transaction_type: str, order_type: str,
                   quantity: int, price: Optional[float] = None,
                   stop_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Place a paper trading order.
        
        Args:
            symbol: Trading symbol
            transaction_type: 'BUY' or 'SELL'
            order_type: 'MARKET' or 'LIMIT' or 'SL' or 'SL-M'
            quantity: Order quantity
            price: Limit price (for LIMIT/SL orders)
            stop_price: Stop price (for SL/SL-M orders)
        
        Returns:
            Order details
        """
        # Validate order
        order_data = {
            'symbol': symbol,
            'quantity': quantity,
            'price': price or 0,
            'transaction_type': transaction_type
        }
        
        is_valid, error = self.validator.validate_order(order_data)
        
        if not is_valid:
            return {
                'status': 'REJECTED',
                'error': error
            }
        
        # Check if we have sufficient funds/shares
        portfolio = self.get_portfolio_summary()
        
        if transaction_type == 'BUY':
            # Get current market price
            current_price = self._get_current_price(symbol)
            
            if order_type == 'MARKET':
                required_funds = quantity * current_price * (1 + self.slippage)
            else:
                required_funds = quantity * price
            
            # Add commission
            commission = self._calculate_commission(required_funds)
            required_funds += commission
            
            if required_funds > portfolio['cash_balance']:
                return {
                    'status': 'REJECTED',
                    'error': f'Insufficient funds. Required: ₹{required_funds:,.2f}, Available: ₹{portfolio["cash_balance"]:,.2f}'
                }
        
        elif transaction_type == 'SELL':
            # Check if we have the shares
            position = self._get_position(symbol)
            
            if not position or position['quantity'] < quantity:
                available = position['quantity'] if position else 0
                return {
                    'status': 'REJECTED',
                    'error': f'Insufficient shares. Required: {quantity}, Available: {available}'
                }
        
        # Generate order ID
        order_id = f"PO_{uuid.uuid4().hex[:8].upper()}"
        
        # Store order
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO paper_orders
            (order_id, symbol, transaction_type, order_type, quantity, price, stop_price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_id, symbol, transaction_type, order_type, quantity, price, stop_price, 'PENDING'))
        
        conn.commit()
        conn.close()
        
        # Execute market orders immediately
        if order_type == 'MARKET':
            self._execute_order(order_id)
        
        logger.info(f"Paper order placed: {order_id} - {transaction_type} {quantity} {symbol}")
        
        return {
            'status': 'SUCCESS',
            'order_id': order_id,
            'symbol': symbol,
            'transaction_type': transaction_type,
            'quantity': quantity,
            'order_type': order_type
        }
    
    def _execute_order(self, order_id: str) -> bool:
        """Execute a pending order"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get order details
        cursor.execute("""
            SELECT symbol, transaction_type, order_type, quantity, price
            FROM paper_orders
            WHERE order_id = ? AND status = 'PENDING'
        """, (order_id,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False
        
        symbol, transaction_type, order_type, quantity, limit_price = result
        
        # Get current market price
        current_price = self._get_current_price(symbol)
        
        # Apply slippage for market orders
        if order_type == 'MARKET':
            if transaction_type == 'BUY':
                execution_price = current_price * (1 + self.slippage)
            else:
                execution_price = current_price * (1 - self.slippage)
        else:
            execution_price = limit_price
        
        # Calculate commission
        trade_value = quantity * execution_price
        commission = self._calculate_commission(trade_value)
        total_cost = trade_value + commission
        
        # Update portfolio
        cursor.execute("""
            SELECT cash_balance FROM paper_portfolio
            ORDER BY id DESC LIMIT 1
        """)
        
        cash_balance = cursor.fetchone()[0]
        
        if transaction_type == 'BUY':
            # Deduct cash
            new_cash = cash_balance - total_cost
            
            # Update or create position
            self._update_position(symbol, quantity, execution_price, 'BUY')
            
        else:  # SELL
            # Add cash (minus commission)
            new_cash = cash_balance + trade_value - commission
            
            # Update position
            self._update_position(symbol, quantity, execution_price, 'SELL')
        
        # Update cash balance
        cursor.execute("""
            UPDATE paper_portfolio
            SET cash_balance = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT MAX(id) FROM paper_portfolio)
        """, (new_cash,))
        
        # Update order status
        cursor.execute("""
            UPDATE paper_orders
            SET status = 'COMPLETE',
                filled_quantity = ?,
                average_fill_price = ?,
                commission = ?,
                slippage = ?,
                filled_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ?
        """, (quantity, execution_price, commission, abs(execution_price - current_price), order_id))
        
        # Record execution
        cursor.execute("""
            INSERT INTO paper_executions
            (order_id, symbol, quantity, price, commission)
            VALUES (?, ?, ?, ?, ?)
        """, (order_id, symbol, quantity, execution_price, commission))
        
        # Record trade in analytics
        self.analytics.record_trade(
            symbol=symbol,
            action=transaction_type,
            quantity=quantity,
            entry_price=execution_price,
            commission=commission
        )
        
        conn.commit()
        conn.close()
        
        logger.info(
            f"Order executed: {order_id} - {transaction_type} {quantity} {symbol} "
            f"@ ₹{execution_price:.2f} (Commission: ₹{commission:.2f})"
        )
        
        return True
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT close
            FROM market_data
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (symbol,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            # Fallback to a default price (should not happen in production)
            logger.warning(f"No market data for {symbol}, using default price")
            return 1000.0
    
    def _calculate_commission(self, trade_value: float) -> float:
        """Calculate trading commission"""
        percentage_commission = trade_value * self.commission_percentage
        total_commission = self.commission_per_trade + percentage_commission
        return total_commission
    
    def _get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current position for a symbol"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT quantity, average_price
            FROM paper_positions
            WHERE symbol = ?
        """, (symbol,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'symbol': symbol,
                'quantity': result[0],
                'average_price': result[1]
            }
        
        return None
    
    def _update_position(self, symbol: str, quantity: int, price: float, action: str):
        """Update position after trade execution"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current position
        cursor.execute("""
            SELECT quantity, average_price
            FROM paper_positions
            WHERE symbol = ?
        """, (symbol,))
        
        result = cursor.fetchone()
        
        if action == 'BUY':
            if result:
                current_qty, current_avg = result
                new_qty = current_qty + quantity
                new_avg = ((current_qty * current_avg) + (quantity * price)) / new_qty
                
                cursor.execute("""
                    UPDATE paper_positions
                    SET quantity = ?,
                        average_price = ?,
                        current_price = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE symbol = ?
                """, (new_qty, new_avg, price, symbol))
            else:
                cursor.execute("""
                    INSERT INTO paper_positions
                    (symbol, quantity, average_price, current_price)
                    VALUES (?, ?, ?, ?)
                """, (symbol, quantity, price, price))
        
        else:  # SELL
            if result:
                current_qty, current_avg = result
                new_qty = current_qty - quantity
                
                if new_qty > 0:
                    cursor.execute("""
                        UPDATE paper_positions
                        SET quantity = ?,
                            current_price = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE symbol = ?
                    """, (new_qty, price, symbol))
                else:
                    # Close position
                    cursor.execute("DELETE FROM paper_positions WHERE symbol = ?", (symbol,))
        
        conn.commit()
        conn.close()
    
    def update_portfolio_values(self):
        """Update current portfolio values with latest prices"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all positions
        cursor.execute("""
            SELECT symbol, quantity, average_price
            FROM paper_positions
            WHERE quantity > 0
        """)
        
        positions = cursor.fetchall()
        
        total_unrealized_pnl = 0
        
        for symbol, quantity, avg_price in positions:
            current_price = self._get_current_price(symbol)
            unrealized_pnl = (current_price - avg_price) * quantity
            unrealized_pnl_pct = ((current_price - avg_price) / avg_price) * 100
            
            total_unrealized_pnl += unrealized_pnl
            
            # Update position
            cursor.execute("""
                UPDATE paper_positions
                SET current_price = ?,
                    unrealized_pnl = ?,
                    unrealized_pnl_pct = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE symbol = ?
            """, (current_price, unrealized_pnl, unrealized_pnl_pct, symbol))
        
        # Update portfolio
        cursor.execute("""
            UPDATE paper_portfolio
            SET unrealized_pnl = ?,
                total_pnl = realized_pnl + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT MAX(id) FROM paper_portfolio)
        """, (total_unrealized_pnl, total_unrealized_pnl))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Portfolio values updated. Unrealized P&L: ₹{total_unrealized_pnl:,.2f}")
    
    def get_order_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get order history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT order_id, symbol, transaction_type, order_type, quantity,
                   price, filled_quantity, average_fill_price, status,
                   commission, created_at, filled_at
            FROM paper_orders
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'order_id': row[0],
                'symbol': row[1],
                'transaction_type': row[2],
                'order_type': row[3],
                'quantity': row[4],
                'price': row[5],
                'filled_quantity': row[6],
                'average_fill_price': row[7],
                'status': row[8],
                'commission': row[9],
                'created_at': row[10],
                'filled_at': row[11]
            })
        
        conn.close()
        
        return orders
    
    def reset_portfolio(self):
        """Reset paper trading portfolio to starting capital"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM paper_portfolio")
        cursor.execute("DELETE FROM paper_positions")
        cursor.execute("DELETE FROM paper_orders")
        cursor.execute("DELETE FROM paper_executions")
        
        cursor.execute("""
            INSERT INTO paper_portfolio (cash_balance, total_value)
            VALUES (?, ?)
        """, (self.starting_capital, self.starting_capital))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Paper trading portfolio reset to ₹{self.starting_capital:,.2f}")


def main():
    """Test paper trading system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Paper Trading System")
    parser.add_argument('--action',
                       choices=['portfolio', 'order', 'history', 'reset'],
                       default='portfolio',
                       help='Action to perform')
    parser.add_argument('--symbol', type=str, help='Trading symbol')
    parser.add_argument('--type', type=str, choices=['BUY', 'SELL'], help='Transaction type')
    parser.add_argument('--quantity', type=int, help='Order quantity')
    
    args = parser.parse_args()
    
    paper = PaperTradingSystem()
    
    if args.action == 'portfolio':
        paper.update_portfolio_values()
        summary = paper.get_portfolio_summary()
        
        print("\n=== Paper Trading Portfolio ===")
        print(f"Cash Balance: ₹{summary['cash_balance']:,.2f}")
        print(f"Position Value: ₹{summary['position_value']:,.2f}")
        print(f"Total Value: ₹{summary['total_value']:,.2f}")
        print(f"\nUnrealized P&L: ₹{summary['unrealized_pnl']:,.2f}")
        print(f"Realized P&L: ₹{summary['realized_pnl']:,.2f}")
        print(f"Total P&L: ₹{summary['total_pnl']:,.2f}")
        print(f"Return: {summary['return_pct']:.2f}%")
        
        if summary['positions']:
            print("\n--- Positions ---")
            for pos in summary['positions']:
                print(f"\n{pos['symbol']}")
                print(f"  Quantity: {pos['quantity']}")
                print(f"  Avg Price: ₹{pos['average_price']:.2f}")
                print(f"  Current: ₹{pos['current_price']:.2f}")
                print(f"  Value: ₹{pos['position_value']:,.2f}")
                print(f"  P&L: ₹{pos['unrealized_pnl']:,.2f}")
    
    elif args.action == 'order':
        if not all([args.symbol, args.type, args.quantity]):
            print("Error: --symbol, --type, and --quantity required")
            return
        
        result = paper.place_order(
            symbol=args.symbol,
            transaction_type=args.type,
            order_type='MARKET',
            quantity=args.quantity
        )
        
        print(f"\n=== Order Result ===")
        print(f"Status: {result['status']}")
        if 'order_id' in result:
            print(f"Order ID: {result['order_id']}")
            print(f"{result['transaction_type']} {result['quantity']} {result['symbol']}")
        elif 'error' in result:
            print(f"Error: {result['error']}")
    
    elif args.action == 'history':
        orders = paper.get_order_history(limit=10)
        
        print(f"\n=== Order History ({len(orders)} orders) ===")
        for order in orders:
            print(f"\n{order['order_id']}")
            print(f"  {order['transaction_type']} {order['quantity']} {order['symbol']}")
            print(f"  Type: {order['order_type']}")
            print(f"  Status: {order['status']}")
            if order['average_fill_price']:
                print(f"  Fill Price: ₹{order['average_fill_price']:.2f}")
                print(f"  Commission: ₹{order['commission']:.2f}")
            print(f"  Created: {order['created_at']}")
    
    elif args.action == 'reset':
        confirm = input("Reset paper trading portfolio? This will delete all positions and orders. (yes/no): ")
        if confirm.lower() == 'yes':
            paper.reset_portfolio()
            print("Portfolio reset successfully!")
        else:
            print("Reset cancelled.")


if __name__ == "__main__":
    main()
