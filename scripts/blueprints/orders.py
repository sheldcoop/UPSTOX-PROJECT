#!/usr/bin/env python3
"""
Orders Blueprint
Handles orders and alerts endpoints
"""

from flask import Blueprint, jsonify, g, request
from datetime import datetime
import sqlite3
import logging

orders_bp = Blueprint('orders', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

DB_PATH = 'market_data.db'


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@orders_bp.route('/orders', methods=['GET'])
def get_orders():
    """Get order history"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                id, symbol, side, quantity, order_type, 
                price, status, created_at, executed_at
            FROM paper_orders
            ORDER BY created_at DESC
            LIMIT 50
        """
        
        rows = cursor.execute(query).fetchall()
        conn.close()
        
        orders = []
        for row in rows:
            orders.append({
                'id': row['id'],
                'symbol': row['symbol'],
                'side': row['side'],
                'quantity': row['quantity'],
                'order_type': row['order_type'],
                'price': row['price'],
                'status': row['status'],
                'created_at': row['created_at'],
                'executed_at': row['executed_at']
            })
        
        return jsonify(orders)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/orders', methods=['POST'])
def place_order():
    """Place a new order"""
    try:
        data = request.json
        
        # Validate required fields
        required = ['symbol', 'side', 'quantity', 'order_type']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Place order using paper trading system
        from paper_trading import PaperTradingSystem
        paper_system = PaperTradingSystem(db_path=DB_PATH)
        
        order = paper_system.place_order(
            symbol=data['symbol'],
            side=data['side'],
            quantity=data['quantity'],
            order_type=data['order_type'],
            price=data.get('price')
        )
        
        return jsonify(order), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/orders/<int:order_id>', methods=['DELETE'])
def cancel_order(order_id):
    """Cancel an order"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update order status to cancelled
        cursor.execute(
            "UPDATE paper_orders SET status = 'cancelled' WHERE id = ?",
            (order_id,)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Order cancelled successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                id, symbol, alert_type, threshold, priority,
                is_active, created_at, triggered_at
            FROM alert_rules
            WHERE is_active = 1
            ORDER BY priority DESC, created_at DESC
        """
        
        rows = cursor.execute(query).fetchall()
        conn.close()
        
        alerts = []
        for row in rows:
            alerts.append({
                'id': row['id'],
                'symbol': row['symbol'],
                'alert_type': row['alert_type'],
                'threshold': row['threshold'],
                'priority': row['priority'],
                'is_active': bool(row['is_active']),
                'created_at': row['created_at'],
                'triggered_at': row['triggered_at']
            })
        
        return jsonify(alerts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/alerts', methods=['POST'])
def create_alert():
    """Create new alert"""
    try:
        data = request.json
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO alert_rules 
            (symbol, alert_type, threshold, priority, is_active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
        """, (
            data['symbol'],
            data['alert_type'],
            data['threshold'],
            data.get('priority', 'MEDIUM'),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        alert_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'id': alert_id, 'message': 'Alert created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete alert"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM alert_rules WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Alert deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
