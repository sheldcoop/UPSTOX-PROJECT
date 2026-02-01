#!/usr/bin/env python3
"""
Expiry Management Blueprint
Handles expiry rolling endpoints
"""

from flask import Blueprint, jsonify, g, request
from datetime import datetime
import logging

expiry_bp = Blueprint('expiry', __name__, url_prefix='/api/expiry')

logger = logging.getLogger(__name__)


@expiry_bp.route('/roll', methods=['POST'])
def roll_expiry():
    """Roll position to next expiry"""
    try:
        from multi_expiry_strategies import (
            MultiExpiryLeg, OptionType, ActionType, ExpiryRoller
        )
        
        data = request.json
        required = ['current_expiry', 'underlying_price', 'strike', 'option_type', 'action']
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        roller = ExpiryRoller()
        
        # Create current leg
        current_leg = MultiExpiryLeg(
            option_type=OptionType.CALL if data['option_type'] == 'CALL' else OptionType.PUT,
            action=ActionType.BUY if data['action'] == 'BUY' else ActionType.SELL,
            strike=data['strike'],
            expiry_date=data['current_expiry'],
            premium=data.get('premium', 100),
            qty=data.get('qty', 50)
        )
        
        # Get next expiry
        current_date = data.get('current_date', datetime.now().strftime('%Y-%m-%d'))
        next_expiry = roller.get_next_expiry(current_date, interval=data.get('interval', 'weekly'))
        
        # Roll position
        new_leg, roll_details = roller.roll_position(
            current_leg,
            next_expiry,
            data['underlying_price'],
            current_date
        )
        
        return jsonify({
            'roll_details': roll_details,
            'new_leg': {
                'option_type': new_leg.option_type.value,
                'action': new_leg.action.value,
                'strike': new_leg.strike,
                'expiry': new_leg.expiry_date,
                'premium': new_leg.premium,
                'qty': new_leg.qty
            },
            'recommendation': 'Roll successful' if roll_details['roll_cost'] < 0 else 'Roll at credit'
        })
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Expiry roll error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@expiry_bp.route('/next', methods=['GET'])
def get_next_expiry():
    """Get next expiry date"""
    try:
        from multi_expiry_strategies import ExpiryRoller
        
        current_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        interval = request.args.get('interval', 'weekly')  # weekly or monthly
        
        roller = ExpiryRoller()
        next_expiry = roller.get_next_expiry(current_date, interval)
        
        return jsonify({
            'current_date': current_date,
            'interval': interval,
            'next_expiry': next_expiry,
            'days_until': (datetime.strptime(next_expiry, '%Y-%m-%d') - 
                          datetime.strptime(current_date, '%Y-%m-%d')).days
        })
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Next expiry error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
