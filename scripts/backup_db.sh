#!/bin/bash
#
# Database Backup Script
# Automatically backs up SQLite database with timestamp
#

set -e

# Configuration
DB_NAME="market_data.db"
BACKUP_DIR="/home/opc/upstox-trading-platform/backups"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/market_data_$TIMESTAMP.db"

# Perform backup
echo "Starting database backup..."
sqlite3 "$DB_NAME" ".backup '$BACKUP_FILE'"

# Compress backup
echo "Compressing backup..."
gzip "$BACKUP_FILE"

# Calculate size
SIZE=$(du -h "$BACKUP_FILE.gz" | cut -f1)
echo "✅ Backup complete: $BACKUP_FILE.gz ($SIZE)"

# Clean up old backups
echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "market_data_*.db.gz" -mtime +$RETENTION_DAYS -delete

# Count remaining backups
COUNT=$(find "$BACKUP_DIR" -name "market_data_*.db.gz" | wc -l)
echo "✅ Backup retention: $COUNT backup(s) kept"

# Log backup
echo "$(date): Backup created: $BACKUP_FILE.gz" >> "$BACKUP_DIR/backup.log"
