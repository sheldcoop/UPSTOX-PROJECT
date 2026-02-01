#!/usr/bin/env python3
"""
Multi-Expiry Strategies Blueprint
Handles advanced strategy endpoints
"""

from flask import Blueprint, jsonify, g, request
from datetime import datetime
import logging

strategies_bp = Blueprint('strategies', __name__, url_prefix='/api/strategies')

logger = logging.getLogger(__name__)


@strategies_bp.route('/calendar-spread', methods=['POST'])
def create_calendar_spread_strategy():
    """Create calendar spread strategy"""
    try:
        from multi_expiry_strategies import create_calendar_spread
        
        data = request.json
        required = ['underlying_price', 'strike', 'near_expiry', 'far_expiry']
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        strategy = create_calendar_spread(
            underlying_price=data['underlying_price'],
            strike=data['strike'],
            near_expiry=data['near_expiry'],
            far_expiry=data['far_expiry'],
            option_type=data.get('option_type', 'CALL'),
            qty=data.get('qty', 50)
        )
        
        # Calculate Greeks and P&L at different prices
        greeks = strategy.get_portfolio_greeks(data['underlying_price'])
        
        price_range = [
            data['underlying_price'] - 200,
            data['underlying_price'] - 100,
            data['underlying_price'],
            data['underlying_price'] + 100,
            data['underlying_price'] + 200
        ]
        
        pnl_curve = []
        for price in price_range:
            pnl = strategy.calculate_pnl(price, data['near_expiry'])
            pnl_curve.append({'price': price, 'pnl': pnl})
        
        return jsonify({
            'strategy_name': strategy.name,
            'legs': [
                {
                    'option_type': leg.option_type.value,
                    'action': leg.action.value,
                    'strike': leg.strike,
                    'expiry': leg.expiry_date,
                    'premium': leg.premium,
                    'qty': leg.qty
                }
                for leg in strategy.legs
            ],
            'greeks': greeks,
            'pnl_curve': pnl_curve,
            'expiries': list(strategy.get_expiry_breakdown().keys())
        })
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Calendar spread error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@strategies_bp.route('/diagonal-spread', methods=['POST'])
def create_diagonal_spread_strategy():
    """Create diagonal spread strategy"""
    try:
        from multi_expiry_strategies import create_diagonal_spread
        
        data = request.json
        required = ['underlying_price', 'near_strike', 'far_strike', 'near_expiry', 'far_expiry']
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        strategy = create_diagonal_spread(
            underlying_price=data['underlying_price'],
            near_strike=data['near_strike'],
            far_strike=data['far_strike'],
            near_expiry=data['near_expiry'],
            far_expiry=data['far_expiry'],
            option_type=data.get('option_type', 'CALL'),
            qty=data.get('qty', 50)
        )
        
        greeks = strategy.get_portfolio_greeks(data['underlying_price'])
        
        return jsonify({
            'strategy_name': strategy.name,
            'legs': [
                {
                    'option_type': leg.option_type.value,
                    'action': leg.action.value,
                    'strike': leg.strike,
                    'expiry': leg.expiry_date,
                    'premium': leg.premium,
                    'qty': leg.qty
                }
                for leg in strategy.legs
            ],
            'greeks': greeks,
            'expiries': list(strategy.get_expiry_breakdown().keys())
        })
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Diagonal spread error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@strategies_bp.route('/double-calendar', methods=['POST'])
def create_double_calendar_strategy():
    """Create double calendar (iron butterfly calendar) strategy"""
    try:
        from multi_expiry_strategies import create_double_calendar
        
        data = request.json
        required = ['underlying_price', 'near_expiry', 'far_expiry']
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        strategy = create_double_calendar(
            underlying_price=data['underlying_price'],
            near_expiry=data['near_expiry'],
            far_expiry=data['far_expiry'],
            qty=data.get('qty', 50)
        )
        
        greeks = strategy.get_portfolio_greeks(data['underlying_price'])
        
        return jsonify({
            'strategy_name': strategy.name,
            'legs': [
                {
                    'option_type': leg.option_type.value,
                    'action': leg.action.value,
                    'strike': leg.strike,
                    'expiry': leg.expiry_date,
                    'premium': leg.premium,
                    'qty': leg.qty
                }
                for leg in strategy.legs
            ],
            'greeks': greeks,
            'num_legs': len(strategy.legs),
            'expiries': list(strategy.get_expiry_breakdown().keys())
        })
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Double calendar error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@strategies_bp.route('/available', methods=['GET'])
def get_available_strategies():
    """Get all available multi-expiry strategies"""
    return jsonify({
        'strategies': [
            {
                'id': 'calendar_spread',
                'name': 'Calendar Spread',
                'description': 'Sell near-term, buy far-term. Same strike, different expiries. Profit from time decay.',
                'multi_expiry': True,
                'required_params': ['underlying_price', 'strike', 'near_expiry', 'far_expiry', 'option_type'],
                'max_profit': 'Limited (depends on volatility)',
                'max_loss': 'Net debit paid',
                'best_for': 'Low volatility, range-bound markets'
            },
            {
                'id': 'diagonal_spread',
                'name': 'Diagonal Spread',
                'description': 'Different strikes AND expiries. Combines calendar + vertical spread.',
                'multi_expiry': True,
                'required_params': ['underlying_price', 'near_strike', 'far_strike', 'near_expiry', 'far_expiry', 'option_type'],
                'max_profit': 'Higher than calendar (due to strike difference)',
                'max_loss': 'Net debit paid',
                'best_for': 'Directional bias with time decay advantage'
            },
            {
                'id': 'double_calendar',
                'name': 'Double Calendar (Iron Butterfly Calendar)',
                'description': 'Calendar spreads on both calls and puts at ATM. Profit from low volatility.',
                'multi_expiry': True,
                'required_params': ['underlying_price', 'near_expiry', 'far_expiry'],
                'max_profit': 'Double premium from both calendars',
                'max_loss': 'Double net debit',
                'best_for': 'Very low volatility, stable markets'
            },
            {
                'id': 'iron_condor',
                'name': 'Iron Condor',
                'description': 'Sell OTM put/call spreads. Single expiry. Profit from range-bound.',
                'multi_expiry': False,
                'max_profit': 'Net premium',
                'max_loss': 'Spread width - premium'
            },
            {
                'id': 'bull_call_spread',
                'name': 'Bull Call Spread',
                'description': 'Buy lower strike call, sell higher strike call. Single expiry.',
                'multi_expiry': False,
                'max_profit': 'Strike difference - premium',
                'max_loss': 'Net premium paid'
            }
        ]
    })
