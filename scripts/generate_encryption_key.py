"""
Generate Fernet encryption key for token storage
Usage: python3 scripts/generate_encryption_key.py
"""

from cryptography.fernet import Fernet
import os

def generate_key():
    """Generate and save encryption key"""
    key = Fernet.generate_key()
    
    # Save to .env
    env_path = '.env'
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update ENCRYPTION_KEY line
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('ENCRYPTION_KEY='):
                lines[i] = f'ENCRYPTION_KEY={key.decode()}\n'
                updated = True
                break
        
        if not updated:
            lines.append(f'ENCRYPTION_KEY={key.decode()}\n')
        
        with open(env_path, 'w') as f:
            f.writelines(lines)
    else:
        with open(env_path, 'w') as f:
            f.write(f'ENCRYPTION_KEY={key.decode()}\n')
    
    print("✅ Encryption key generated and saved to .env")
    print(f"🔑 Key: {key.decode()}")
    print("\n⚠️  Keep this key secure - losing it means losing access to stored tokens!")

if __name__ == '__main__':
    generate_key()
