"""
Advanced Multi-Expiry Strategy Engine
Calendar spreads, diagonal spreads, expiry rolling, and complex multi-leg strategies
"""

import sys
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup basic logging (don't need full logger_config for this module)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('multi_expiry_strategies')


class OptionType(Enum):
    CALL = "CALL"
    PUT = "PUT"


class ActionType(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class MultiExpiryLeg:
    """Option leg with expiry date support"""
    option_type: OptionType
    action: ActionType
    strike: float
    expiry_date: str  # YYYY-MM-DD format
    premium: float
    qty: int = 1
    symbol: str = "NIFTY"
    
    def calculate_pnl(self, underlying_price: float, current_date: str) -> float:
        """Calculate P&L (handles early exit before expiry)"""
        # If before expiry, need option pricing model (simplified here)
        if current_date < self.expiry_date:
            # Use simple intrinsic + time value decay
            days_to_expiry = (datetime.strptime(self.expiry_date, '%Y-%m-%d') - 
                             datetime.strptime(current_date, '%Y-%m-%d')).days
            time_value_decay = self.premium * 0.3 * (days_to_expiry / 30)  # Simplified theta decay
        else:
            time_value_decay = 0
        
        # Intrinsic value
        if self.option_type == OptionType.CALL:
            intrinsic = max(0, underlying_price - self.strike)
        else:  # PUT
            intrinsic = max(0, self.strike - underlying_price)
        
        current_value = intrinsic + time_value_decay
        
        # P&L calculation
        if self.action == ActionType.BUY:
            return (current_value - self.premium) * self.qty
        else:  # SELL
            return (self.premium - current_value) * self.qty
    
    def get_greeks(self, underlying_price: float, volatility: float = 0.20, 
                   risk_free_rate: float = 0.06) -> Dict[str, float]:
        """Calculate option Greeks using Black-Scholes (simplified)"""
        try:
            from scipy.stats import norm
        except ImportError:
            logger.warning("scipy not installed, returning approximate Greeks")
            # Return simplified Greeks without scipy
            days_to_expiry = (datetime.strptime(self.expiry_date, '%Y-%m-%d') - datetime.now()).days
            T = max(days_to_expiry / 365.0, 0.001)
            S = underlying_price
            K = self.strike
            
            # Simplified delta (0.5 ATM, 1 ITM, 0 OTM)
            if self.option_type == OptionType.CALL:
                delta = 0.5 if abs(S - K) < 100 else (1.0 if S > K else 0.1)
            else:
                delta = -0.5 if abs(S - K) < 100 else (-1.0 if S < K else -0.1)
            
            multiplier = 1 if self.action == ActionType.BUY else -1
            
            return {
                'delta': delta * multiplier * self.qty,
                'gamma': 0.01 * multiplier * self.qty,  # Simplified
                'vega': 10 * multiplier * self.qty,      # Simplified
                'theta': -5 * multiplier * self.qty,     # Simplified decay
                'price': max(0, (S - K) if self.option_type == OptionType.CALL else (K - S))
            }
        
        days_to_expiry = (datetime.strptime(self.expiry_date, '%Y-%m-%d') - datetime.now()).days
        T = max(days_to_expiry / 365.0, 0.001)  # Time to expiry in years
        S = underlying_price
        K = self.strike
        sigma = volatility
        r = risk_free_rate
        
        # d1 and d2 for Black-Scholes
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if self.option_type == OptionType.CALL:
            delta = norm.cdf(d1)
            option_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:  # PUT
            delta = -norm.cdf(-d1)
            option_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        
        # Gamma (same for call and put)
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
        # Vega (same for call and put)
        vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # Per 1% change in volatility
        
        # Theta
        if self.option_type == OptionType.CALL:
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - 
                    r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
        else:
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + 
                    r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
        
        # Adjust for position (BUY vs SELL)
        multiplier = 1 if self.action == ActionType.BUY else -1
        
        return {
            'delta': delta * multiplier * self.qty,
            'gamma': gamma * multiplier * self.qty,
            'vega': vega * multiplier * self.qty,
            'theta': theta * multiplier * self.qty,
            'price': option_price
        }


class MultiExpiryStrategy:
    """Strategy with legs across multiple expiries"""
    
    def __init__(self, name: str, legs: List[MultiExpiryLeg], entry_price: float):
        self.name = name
        self.legs = legs
        self.entry_price = entry_price
        self.entry_date = None
    
    def calculate_pnl(self, underlying_price: float, current_date: str) -> float:
        """Calculate total strategy P&L"""
        total_pnl = sum(leg.calculate_pnl(underlying_price, current_date) for leg in self.legs)
        return total_pnl
    
    def get_portfolio_greeks(self, underlying_price: float) -> Dict[str, float]:
        """Aggregate Greeks across all legs"""
        total_greeks = {'delta': 0, 'gamma': 0, 'vega': 0, 'theta': 0}
        
        for leg in self.legs:
            leg_greeks = leg.get_greeks(underlying_price)
            for greek in total_greeks:
                total_greeks[greek] += leg_greeks[greek]
        
        return total_greeks
    
    def get_expiry_breakdown(self) -> Dict[str, List[MultiExpiryLeg]]:
        """Group legs by expiry date"""
        expiry_map = {}
        for leg in self.legs:
            if leg.expiry_date not in expiry_map:
                expiry_map[leg.expiry_date] = []
            expiry_map[leg.expiry_date].append(leg)
        return expiry_map
    
    def get_max_profit_loss(self, price_range: List[float]) -> Dict[str, float]:
        """Calculate max profit and loss across price range"""
        # Use latest expiry for calculation
        latest_expiry = max(leg.expiry_date for leg in self.legs)
        
        pnls = [self.calculate_pnl(price, latest_expiry) for price in price_range]
        
        return {
            'max_profit': max(pnls),
            'max_loss': min(pnls),
            'breakeven_points': self._find_breakevens(price_range, pnls)
        }
    
    def _find_breakevens(self, prices: List[float], pnls: List[float]) -> List[float]:
        """Find breakeven points where P&L crosses zero"""
        breakevens = []
        for i in range(len(pnls) - 1):
            if pnls[i] * pnls[i + 1] < 0:  # Sign change
                # Linear interpolation
                breakeven = prices[i] + (prices[i + 1] - prices[i]) * abs(pnls[i]) / abs(pnls[i + 1] - pnls[i])
                breakevens.append(breakeven)
        return breakevens


# ============================================================================
# MULTI-EXPIRY STRATEGY BUILDERS
# ============================================================================

def create_calendar_spread(
    underlying_price: float,
    strike: float,
    near_expiry: str,
    far_expiry: str,
    option_type: str = "CALL",
    qty: int = 50
) -> MultiExpiryStrategy:
    """
    Calendar Spread (Time Spread)
    - Sell near-term option
    - Buy far-term option
    - Same strike, different expiries
    - Profit from time decay differential
    """
    legs = [
        MultiExpiryLeg(
            option_type=OptionType.CALL if option_type == "CALL" else OptionType.PUT,
            action=ActionType.SELL,
            strike=strike,
            expiry_date=near_expiry,
            premium=80,  # Near-term premium (higher theta decay)
            qty=qty
        ),
        MultiExpiryLeg(
            option_type=OptionType.CALL if option_type == "CALL" else OptionType.PUT,
            action=ActionType.BUY,
            strike=strike,
            expiry_date=far_expiry,
            premium=120,  # Far-term premium (lower theta decay)
            qty=qty
        )
    ]
    
    return MultiExpiryStrategy(
        name=f"{option_type} Calendar Spread ({near_expiry}/{far_expiry})",
        legs=legs,
        entry_price=underlying_price
    )


def create_diagonal_spread(
    underlying_price: float,
    near_strike: float,
    far_strike: float,
    near_expiry: str,
    far_expiry: str,
    option_type: str = "CALL",
    qty: int = 50
) -> MultiExpiryStrategy:
    """
    Diagonal Spread
    - Different strikes AND different expiries
    - Combines calendar spread + vertical spread
    - More flexibility than pure calendar
    """
    legs = [
        MultiExpiryLeg(
            option_type=OptionType.CALL if option_type == "CALL" else OptionType.PUT,
            action=ActionType.SELL,
            strike=near_strike,
            expiry_date=near_expiry,
            premium=100,
            qty=qty
        ),
        MultiExpiryLeg(
            option_type=OptionType.CALL if option_type == "CALL" else OptionType.PUT,
            action=ActionType.BUY,
            strike=far_strike,
            expiry_date=far_expiry,
            premium=140,
            qty=qty
        )
    ]
    
    return MultiExpiryStrategy(
        name=f"{option_type} Diagonal Spread",
        legs=legs,
        entry_price=underlying_price
    )


def create_double_calendar(
    underlying_price: float,
    near_expiry: str,
    far_expiry: str,
    qty: int = 50
) -> MultiExpiryStrategy:
    """
    Double Calendar (Iron Butterfly Calendar)
    - Calendar spread on both calls and puts
    - ATM strikes
    - Profit from low volatility
    """
    atm_strike = round(underlying_price / 50) * 50  # Round to nearest 50
    
    legs = [
        # Put calendar
        MultiExpiryLeg(OptionType.PUT, ActionType.SELL, atm_strike, near_expiry, 75, qty),
        MultiExpiryLeg(OptionType.PUT, ActionType.BUY, atm_strike, far_expiry, 110, qty),
        # Call calendar
        MultiExpiryLeg(OptionType.CALL, ActionType.SELL, atm_strike, near_expiry, 75, qty),
        MultiExpiryLeg(OptionType.CALL, ActionType.BUY, atm_strike, far_expiry, 110, qty),
    ]
    
    return MultiExpiryStrategy(
        name=f"Double Calendar ({near_expiry}/{far_expiry})",
        legs=legs,
        entry_price=underlying_price
    )


# ============================================================================
# EXPIRY ROLLING MANAGER
# ============================================================================

class ExpiryRoller:
    """Manage expiry rolling strategies"""
    
    def __init__(self):
        self.active_positions = []
        self.roll_history = []
    
    def should_roll(self, leg: MultiExpiryLeg, current_date: str, days_before_expiry: int = 3) -> bool:
        """Check if position should be rolled"""
        expiry_dt = datetime.strptime(leg.expiry_date, '%Y-%m-%d')
        current_dt = datetime.strptime(current_date, '%Y-%m-%d')
        days_to_expiry = (expiry_dt - current_dt).days
        
        return days_to_expiry <= days_before_expiry
    
    def roll_position(
        self,
        current_leg: MultiExpiryLeg,
        next_expiry: str,
        underlying_price: float,
        current_date: str
    ) -> Tuple[MultiExpiryLeg, Dict]:
        """
        Roll position to next expiry
        Returns: (new_leg, roll_details)
        """
        # Close current position
        exit_pnl = current_leg.calculate_pnl(underlying_price, current_date)
        
        # Determine new strike (can use same or adjust)
        new_strike = current_leg.strike
        
        # Calculate new premium (simplified - should use option pricing)
        days_to_new_expiry = (datetime.strptime(next_expiry, '%Y-%m-%d') - 
                             datetime.strptime(current_date, '%Y-%m-%d')).days
        new_premium = current_leg.premium * (days_to_new_expiry / 7)  # Rough estimate
        
        # Create new leg
        new_leg = MultiExpiryLeg(
            option_type=current_leg.option_type,
            action=current_leg.action,
            strike=new_strike,
            expiry_date=next_expiry,
            premium=new_premium,
            qty=current_leg.qty
        )
        
        roll_details = {
            'roll_date': current_date,
            'old_expiry': current_leg.expiry_date,
            'new_expiry': next_expiry,
            'old_strike': current_leg.strike,
            'new_strike': new_strike,
            'exit_pnl': exit_pnl,
            'old_premium': current_leg.premium,
            'new_premium': new_premium,
            'roll_cost': new_premium - exit_pnl  # Net cost/credit
        }
        
        self.roll_history.append(roll_details)
        logger.info(f"Rolled position: {current_leg.expiry_date} → {next_expiry}, P&L: ₹{exit_pnl:.2f}")
        
        return new_leg, roll_details
    
    def get_next_expiry(self, current_date: str, interval: str = "weekly") -> str:
        """Get next expiry date based on interval"""
        current_dt = datetime.strptime(current_date, '%Y-%m-%d')
        
        if interval == "weekly":
            # Find next Thursday (NIFTY weekly expiry)
            days_ahead = (3 - current_dt.weekday()) % 7  # Thursday = 3
            if days_ahead == 0:
                days_ahead = 7  # Next week if today is Thursday
            next_expiry = current_dt + timedelta(days=days_ahead)
        elif interval == "monthly":
            # Last Thursday of next month
            next_month = current_dt.replace(day=28) + timedelta(days=4)
            next_month = next_month.replace(day=1)
            # Find last Thursday
            days_in_month = (next_month.replace(month=next_month.month % 12 + 1, day=1) - 
                           timedelta(days=1)).day
            for day in range(days_in_month, 0, -1):
                test_date = next_month.replace(day=day)
                if test_date.weekday() == 3:  # Thursday
                    next_expiry = test_date
                    break
        else:
            next_expiry = current_dt + timedelta(days=30)
        
        return next_expiry.strftime('%Y-%m-%d')


# ============================================================================
# ADVANCED STRATEGY BACKTESTER
# ============================================================================

class MultiExpiryBacktester:
    """Backtest multi-expiry strategies with rolling"""
    
    def __init__(self):
        self.roller = ExpiryRoller()
    
    def backtest_with_rolling(
        self,
        strategy: MultiExpiryStrategy,
        historical_data: pd.DataFrame,
        start_date: str,
        end_date: str,
        auto_roll: bool = True,
        roll_days_before: int = 3
    ) -> Dict:
        """
        Backtest strategy with automatic expiry rolling
        """
        results = []
        current_strategy = strategy
        
        # Filter historical data
        hist_filtered = historical_data[
            (historical_data['date'] >= start_date) & 
            (historical_data['date'] <= end_date)
        ].copy()
        
        for idx, row in hist_filtered.iterrows():
            current_date = row['date']
            underlying_price = row['close']
            
            # Check if any legs need rolling
            if auto_roll:
                rolled_legs = []
                for leg in current_strategy.legs:
                    if self.roller.should_roll(leg, current_date, roll_days_before):
                        next_expiry = self.roller.get_next_expiry(current_date)
                        new_leg, roll_info = self.roller.roll_position(
                            leg, next_expiry, underlying_price, current_date
                        )
                        rolled_legs.append(new_leg)
                    else:
                        rolled_legs.append(leg)
                
                # Update strategy with rolled legs
                current_strategy = MultiExpiryStrategy(
                    strategy.name,
                    rolled_legs,
                    underlying_price
                )
            
            # Calculate daily P&L
            pnl = current_strategy.calculate_pnl(underlying_price, current_date)
            greeks = current_strategy.get_portfolio_greeks(underlying_price)
            
            results.append({
                'date': current_date,
                'underlying_price': underlying_price,
                'pnl': pnl,
                'delta': greeks['delta'],
                'gamma': greeks['gamma'],
                'vega': greeks['vega'],
                'theta': greeks['theta']
            })
        
        # Calculate summary metrics
        pnls = [r['pnl'] for r in results]
        
        return {
            'daily_results': results,
            'roll_history': self.roller.roll_history,
            'summary': {
                'total_pnl': sum(pnls),
                'avg_daily_pnl': np.mean(pnls),
                'max_pnl': max(pnls),
                'min_pnl': min(pnls),
                'sharpe_ratio': np.mean(pnls) / np.std(pnls) * np.sqrt(252) if np.std(pnls) > 0 else 0,
                'num_rolls': len(self.roller.roll_history),
                'total_roll_cost': sum(r['roll_cost'] for r in self.roller.roll_history)
            }
        }


if __name__ == "__main__":
    print("Testing Multi-Expiry Strategy Engine...")
    
    # Test calendar spread
    calendar = create_calendar_spread(
        underlying_price=21800,
        strike=21800,
        near_expiry="2026-02-06",  # Next Thursday
        far_expiry="2026-02-27",   # Monthly expiry
        option_type="CALL",
        qty=50
    )
    
    print(f"\n✅ Created: {calendar.name}")
    print(f"   Legs: {len(calendar.legs)}")
    print(f"   Expiries: {list(calendar.get_expiry_breakdown().keys())}")
    
    # Calculate P&L at different prices
    prices = [21600, 21700, 21800, 21900, 22000]
    print(f"\n📊 P&L at different prices:")
    for price in prices:
        pnl = calendar.calculate_pnl(price, "2026-02-06")
        print(f"   @ {price}: ₹{pnl:,.2f}")
    
    # Calculate Greeks
    greeks = calendar.get_portfolio_greeks(21800)
    print(f"\n📈 Portfolio Greeks:")
    print(f"   Delta: {greeks['delta']:.2f}")
    print(f"   Gamma: {greeks['gamma']:.4f}")
    print(f"   Vega: {greeks['vega']:.2f}")
    print(f"   Theta: {greeks['theta']:.2f}")
    
    # Test diagonal spread
    diagonal = create_diagonal_spread(
        underlying_price=21800,
        near_strike=21800,
        far_strike=22000,
        near_expiry="2026-02-06",
        far_expiry="2026-02-27",
        option_type="CALL"
    )
    print(f"\n✅ Created: {diagonal.name}")
    
    print("\n🎯 Multi-Expiry Engine Ready!")
    print("   ✅ Calendar Spreads")
    print("   ✅ Diagonal Spreads")
    print("   ✅ Double Calendar")
    print("   ✅ Expiry Rolling")
    print("   ✅ Greeks Calculation")
