import sqlite3

token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyWkNEUTkiLCJqdGkiOiI2OTdlOTViYzFhY2FiMjBhNzE3ZTQ4NTAiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2OTkwMzU0OCwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY5OTgzMjAwfQ.y5xey_vjMP7kjTScnGSRdQcF1VZmod7M0DTrS17JhO0"
expires_at = 1769983200

conn = sqlite3.connect('market_data.db')
cursor = conn.cursor()

# Insert into auth_tokens table
cursor.execute("DELETE FROM auth_tokens")
cursor.execute("""
    INSERT INTO auth_tokens (token_type, access_token, expires_at, user_id)
    VALUES ('bearer', ?, ?, '2ZCDQ9')
""", (token, expires_at))

# Also insert into oauth_tokens if it exists
cursor.execute("DELETE FROM oauth_tokens")
cursor.execute("""
    INSERT INTO oauth_tokens (client_id, access_token, refresh_token, expires_at)
    VALUES ('upstox', ?, '', ?)
""", (token, expires_at))

conn.commit()

print("Token stored successfully!")
print("\nauth_tokens:")
cursor.execute("SELECT token_type, substr(access_token, 1, 50), expires_at FROM auth_tokens")
for row in cursor.fetchall():
    print(f"  {row}")

print("\noauth_tokens:")
cursor.execute("SELECT client_id, substr(access_token, 1, 50), expires_at FROM oauth_tokens")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
