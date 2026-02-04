#!/usr/bin/env python3
"""
Automated import path updater for codebase reorganization.
Updates all Python files to use new import paths.
"""

import os
import re
from pathlib import Path

# Define import path mappings (old_path -> new_path)
IMPORT_MAPPINGS = {
    # Backend core
    r'from scripts\.metrics\.performance_analytics': 'from backend.core.analytics.performance',
    r'from scripts\.metrics\.portfolio_analytics': 'from backend.core.analytics.portfolio',
    r'from scripts\.metrics\.risk_manager': 'from backend.core.risk.manager',
    r'from scripts\.legacy\.paper_trading': 'from backend.core.trading.paper_trading',
    r'from scripts\.legacy\.order_manager_v3': 'from backend.core.trading.order_manager',
    r'from scripts\.legacy\.multi_expiry_strategies': 'from backend.core.trading.multi_expiry_strategies',
    r'from scripts\.backtest_engine': 'from backend.core.analytics.backtest_engine',
    r'from scripts\.backtesting_engine': 'from backend.core.analytics.backtesting_engine',
    
    # Backend services
    r'from scripts\.services\.market_info_service': 'from backend.services.market_data.info',
    r'from scripts\.legacy\.market_quote_v3': 'from backend.services.market_data.quotes',
    r'from scripts\.legacy\.options_chain_service': 'from backend.services.market_data.options_chain',
    r'from scripts\.data_downloader': 'from backend.services.market_data.downloader',
    r'from scripts\.upstox_live_api': 'from backend.services.upstox.live_api',
    r'from scripts\.portfolio_services_v3': 'from backend.services.upstox.portfolio',
    r'from scripts\.gtt_orders_manager': 'from backend.services.upstox.gtt_orders',
    r'from scripts\.ai_service': 'from backend.services.ai.service',
    
    # Backend data
    r'from scripts\.db\.': 'from backend.data.database.',
    r'from scripts\.etl\.': 'from backend.data.etl.',
    r'from scripts\.candle_fetcher_v3': 'from backend.data.fetchers.candles',
    r'from scripts\.corporate_announcements_fetcher': 'from backend.data.fetchers.corporate_announcements',
    r'from scripts\.base_fetcher': 'from backend.data.fetchers.base',
    
    # Backend utils
    r'from scripts\.auth_manager': 'from backend.utils.auth.manager',
    r'from scripts\.auth_header_utils': 'from backend.utils.auth.headers',
    r'from scripts\.auth_headers_mixin': 'from backend.utils.auth.mixins',
    r'from scripts\.logger_config': 'from backend.utils.logging.config',
    r'from scripts\.error_handler': 'from backend.utils.logging.error_handler',
    r'from scripts\.config_loader': 'from backend.utils.helpers.config',
    r'from scripts\.symbol_resolver': 'from backend.utils.helpers.symbol_resolver',
    
    # Frontend
    r'from dashboard_ui\.': 'from frontend.',
    r'import dashboard_ui\.': 'import frontend.',
}

def update_file_imports(file_path):
    """Update import paths in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all replacements
        for old_pattern, new_path in IMPORT_MAPPINGS.items():
            content = re.sub(old_pattern, new_path, content)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """Update all Python files in the project."""
    root = Path('/Users/prince/Desktop/UPSTOX-PROJECT-Oracle')
    updated_files = []
    
    # Find all Python files in backend, frontend, and root
    for pattern in ['backend/**/*.py', 'frontend/**/*.py', '*.py', 'tests/**/*.py']:
        for py_file in root.glob(pattern):
            if '__pycache__' not in str(py_file):
                if update_file_imports(py_file):
                    updated_files.append(py_file)
    
    print(f"\nUpdated {len(updated_files)} files:")
    for f in updated_files:
        print(f"  ✓ {f.relative_to(root)}")

if __name__ == '__main__':
    main()
