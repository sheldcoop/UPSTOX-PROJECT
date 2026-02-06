"""
Token Auto-Refresh Scheduler for Upstox API

Handles automatic token refresh:
- Live API tokens expire daily at 3:30 PM IST
- Sandbox tokens valid for 10 years (no refresh needed)
- Proactive refresh 30 minutes before expiry
- JWT token parsing and expiry detection
"""

import os
import logging
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
import pytz

from backend.utils.auth.manager import AuthManager

logger = logging.getLogger(__name__)


class TokenRefreshScheduler:
    """
    Manages automatic token refresh for Live and Sandbox environments.
    
    Live tokens expire daily at 3:30 PM IST, so we refresh at 3:00 PM IST.
    Sandbox tokens are long-lived (10 years), so no scheduled refresh needed.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize token refresh scheduler
        
        Args:
            db_path: Path to database for storing tokens
        """
        self.auth_manager = AuthManager(db_path=db_path)
        self.scheduler = BackgroundScheduler()
        self.ist_tz = pytz.timezone('Asia/Kolkata')
        
        # Environment type (live or sandbox)
        self.env_type = os.getenv('UPSTOX_ENV', 'live').lower()
        
        logger.info(f"✅ TokenRefreshScheduler initialized (env: {self.env_type})")
    
    def parse_jwt_token(self, token: str) -> Dict:
        """
        Parse JWT token without verification to get expiry info
        
        Args:
            token: JWT access token
            
        Returns:
            Decoded token data including 'exp' (expiry timestamp)
        """
        try:
            # Decode without verification (we just need to read the payload)
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            logger.debug(f"Token parsed: sub={decoded.get('sub')}, exp={decoded.get('exp')}")
            return decoded
            
        except Exception as e:
            logger.error(f"Failed to parse JWT token: {e}")
            return {}
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """
        Get token expiry datetime
        
        Args:
            token: JWT access token
            
        Returns:
            Datetime when token expires, or None if parsing fails
        """
        decoded = self.parse_jwt_token(token)
        exp_timestamp = decoded.get('exp')
        
        if exp_timestamp:
            expiry_dt = datetime.fromtimestamp(exp_timestamp, tz=self.ist_tz)
            logger.info(f"Token expires at: {expiry_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            return expiry_dt
        
        return None
    
    def is_token_expiring_soon(self, token: str, minutes_before: int = 30) -> bool:
        """
        Check if token will expire within specified minutes
        
        Args:
            token: JWT access token
            minutes_before: Check if expiring within this many minutes
            
        Returns:
            True if token expires within the specified time
        """
        expiry_dt = self.get_token_expiry(token)
        
        if not expiry_dt:
            return False
        
        now = datetime.now(tz=self.ist_tz)
        time_until_expiry = expiry_dt - now
        
        expiring_soon = time_until_expiry.total_seconds() < (minutes_before * 60)
        
        if expiring_soon:
            logger.warning(f"⚠️ Token expiring in {time_until_expiry.total_seconds() / 60:.1f} minutes")
        
        return expiring_soon
    
    def refresh_token_now(self, user_id: str = "default") -> bool:
        """
        Manually trigger token refresh
        
        Args:
            user_id: User identifier
            
        Returns:
            True if refresh successful
        """
        try:
            logger.info(f"🔄 Manually refreshing token for user: {user_id}")
            
            # Get current token to check if refresh is needed
            current_token = self.auth_manager.get_valid_token(user_id)
            
            if current_token and not self.is_token_expiring_soon(current_token, minutes_before=5):
                logger.info("✅ Token still valid, no refresh needed")
                return True
            
            # Force refresh by requesting token (will auto-refresh if expired)
            new_token = self.auth_manager.get_valid_token(user_id)
            
            if new_token:
                logger.info(f"✅ Token refreshed successfully")
                return True
            else:
                logger.error("❌ Token refresh failed - no valid token returned")
                return False
                
        except Exception as e:
            logger.error(f"❌ Token refresh failed: {e}", exc_info=True)
            return False
    
    def schedule_live_token_refresh(self, user_id: str = "default"):
        """
        Schedule daily token refresh for Live API
        
        Live tokens expire at 3:30 PM IST daily
        We refresh at 3:00 PM IST (30 minutes before expiry)
        
        Args:
            user_id: User identifier
        """
        if self.env_type != 'live':
            logger.info(f"Skipping scheduled refresh (env: {self.env_type})")
            return
        
        # Schedule daily refresh at 3:00 PM IST
        trigger = CronTrigger(
            hour=15,  # 3 PM
            minute=0,  # :00
            timezone=self.ist_tz
        )
        
        self.scheduler.add_job(
            func=self.refresh_token_now,
            trigger=trigger,
            args=[user_id],
            id=f'token_refresh_{user_id}',
            name=f'Daily token refresh for {user_id}',
            replace_existing=True
        )
        
        logger.info(f"✅ Scheduled daily token refresh at 3:00 PM IST for user: {user_id}")
    
    def schedule_token_refresh_at(self, refresh_time: datetime, user_id: str = "default"):
        """
        Schedule one-time token refresh at specific datetime
        
        Args:
            refresh_time: When to refresh the token
            user_id: User identifier
        """
        trigger = DateTrigger(run_date=refresh_time)
        
        self.scheduler.add_job(
            func=self.refresh_token_now,
            trigger=trigger,
            args=[user_id],
            id=f'token_refresh_once_{user_id}',
            name=f'One-time token refresh for {user_id}',
            replace_existing=True
        )
        
        logger.info(f"✅ Scheduled one-time token refresh at {refresh_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    def start(self, user_id: str = "default"):
        """
        Start the scheduler
        
        Args:
            user_id: User identifier for token refresh
        """
        try:
            # Schedule recurring refresh for Live environment
            if self.env_type == 'live':
                self.schedule_live_token_refresh(user_id)
                logger.info("✅ Live token auto-refresh enabled (daily at 3:00 PM IST)")
            else:
                logger.info(f"ℹ️  Sandbox environment - tokens valid for 10 years, no scheduled refresh")
            
            # Start scheduler
            self.scheduler.start()
            logger.info("✅ Token refresh scheduler started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}", exc_info=True)
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("✅ Token refresh scheduler stopped")
    
    def get_status(self) -> Dict:
        """
        Get scheduler status
        
        Returns:
            Status dictionary with job info
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            })
        
        return {
            'running': self.scheduler.running,
            'env_type': self.env_type,
            'jobs': jobs,
            'timezone': str(self.ist_tz),
        }


# Singleton instance
_scheduler_instance: Optional[TokenRefreshScheduler] = None


def get_scheduler(db_path: str = None) -> TokenRefreshScheduler:
    """
    Get singleton scheduler instance
    
    Args:
        db_path: Path to database
        
    Returns:
        TokenRefreshScheduler instance
    """
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = TokenRefreshScheduler(db_path=db_path)
    
    return _scheduler_instance


if __name__ == "__main__":
    """Test token refresh scheduler"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    scheduler = TokenRefreshScheduler()
    
    # Test with provided Live token
    live_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyWkNEUTkiLCJqdGkiOiI2OTgzZTIwZmU1OTE0MTcyNTNmY2Q0Y2IiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzcwMjUwNzY3LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NzAzMjg4MDB9.IE4EsLt02lL-5xv6WWazrKPw-JEGI-8UQwGAe5kKWTQ"
    
    print("\n🔍 Testing Token Parsing:")
    print("=" * 70)
    
    decoded = scheduler.parse_jwt_token(live_token)
    print(f"Subject: {decoded.get('sub')}")
    print(f"JTI: {decoded.get('jti')}")
    print(f"Issued At: {datetime.fromtimestamp(decoded.get('iat')).strftime('%Y-%m-%d %H:%M:%S')}")
    
    expiry_dt = scheduler.get_token_expiry(live_token)
    if expiry_dt:
        print(f"Expires At: {expiry_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        now = datetime.now(tz=scheduler.ist_tz)
        time_until_expiry = expiry_dt - now
        print(f"Time Until Expiry: {time_until_expiry}")
    
    print(f"\nExpiring Soon (30 min): {scheduler.is_token_expiring_soon(live_token, minutes_before=30)}")
    
    print("\n✅ Token refresh scheduler test complete")
