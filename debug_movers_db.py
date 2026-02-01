import sqlite3
from pathlib import Path

db_path = "market_data.db"

def check_category(name, segment, types):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        placeholders = ','.join(['?'] * len(types))
        query = f"SELECT COUNT(*) FROM instruments WHERE segment_id='{segment}' AND type_code IN ({placeholders})"
        cursor.execute(query, types)
        count = cursor.fetchone()[0]
        
        print(f"Category: {name}")
        print(f"  Query: segment_id='{segment}' AND type_code IN {types}")
        print(f"  Count: {count}")
        
        # Sample few
        query_sample = f"SELECT symbol, type_code FROM instruments WHERE segment_id='{segment}' AND type_code IN ({placeholders}) LIMIT 5"
        cursor.execute(query_sample, types)
        print(f"  Sample: {cursor.fetchall()}")
        conn.close()
    except Exception as e:
        print(f"Error checking {name}: {e}")

def check_symbol(symbol):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, segment_id, type_code FROM instruments WHERE symbol=?", (symbol,))
        print(f"Symbol {symbol}: {cursor.fetchall()}")
        conn.close()
    except Exception as e:
        print(f"Error checking {symbol}: {e}")

print("--- DB Counts ---")
check_category('NSE_MAIN', 'NSE_EQ', ('EQ', 'BE'))
check_category('NSE_SME', 'NSE_EQ', ('SM', 'ST'))
check_category('BSE_MAIN', 'BSE_EQ', ('A', 'B'))
check_category('BSE_SME', 'BSE_EQ', ('M', 'MT'))

print("\n--- Specific Symbols ---")
check_symbol('SILGO-RE1')
check_symbol('SERVOTECH') 
check_symbol('RELIANCE')
