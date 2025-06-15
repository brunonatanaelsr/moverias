#!/bin/bash
# Move Marias - Automated Backup Script
# Comprehensive backup solution for production environment

set -e

# Configuration
BACKUP_DIR="/var/backups/movemarias"
PROJECT_DIR="/var/www/movemarias"
DB_NAME="movemarias_prod"
DAYS_TO_KEEP=30
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$BACKUP_DIR/backup.log"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$BACKUP_DIR/backup.log"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$BACKUP_DIR/backup.log"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"/{database,files,logs}

log "🔄 Starting Move Marias backup process..."

# 1. Database Backup
log "📊 Backing up database..."
if command -v pg_dump >/dev/null 2>&1; then
    pg_dump "$DB_NAME" | gzip > "$BACKUP_DIR/database/db_${TIMESTAMP}.sql.gz"
    if [ $? -eq 0 ]; then
        log "✅ Database backup completed: db_${TIMESTAMP}.sql.gz"
    else
        error "❌ Database backup failed"
        exit 1
    fi
else
    # SQLite backup
    if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
        cp "$PROJECT_DIR/db.sqlite3" "$BACKUP_DIR/database/db_${TIMESTAMP}.sqlite3"
        gzip "$BACKUP_DIR/database/db_${TIMESTAMP}.sqlite3"
        log "✅ SQLite backup completed: db_${TIMESTAMP}.sqlite3.gz"
    else
        warning "⚠️  No database file found"
    fi
fi

# 2. Media Files Backup
log "📁 Backing up media files..."
if [ -d "$PROJECT_DIR/media" ] && [ "$(ls -A $PROJECT_DIR/media)" ]; then
    tar -czf "$BACKUP_DIR/files/media_${TIMESTAMP}.tar.gz" -C "$PROJECT_DIR" media
    log "✅ Media files backup completed: media_${TIMESTAMP}.tar.gz"
else
    log "ℹ️  No media files to backup"
fi

# 3. Static Files Backup
log "🎨 Backing up static files..."
if [ -d "$PROJECT_DIR/staticfiles" ] && [ "$(ls -A $PROJECT_DIR/staticfiles)" ]; then
    tar -czf "$BACKUP_DIR/files/static_${TIMESTAMP}.tar.gz" -C "$PROJECT_DIR" staticfiles
    log "✅ Static files backup completed: static_${TIMESTAMP}.tar.gz"
else
    log "ℹ️  No static files to backup"
fi

# 4. Configuration Backup
log "⚙️  Backing up configuration files..."
tar -czf "$BACKUP_DIR/files/config_${TIMESTAMP}.tar.gz" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='media' \
    --exclude='staticfiles' \
    -C "$(dirname $PROJECT_DIR)" "$(basename $PROJECT_DIR)"
log "✅ Configuration backup completed: config_${TIMESTAMP}.tar.gz"

# 5. Logs Backup
log "📝 Backing up log files..."
if [ -d "/var/log/movemarias" ] && [ "$(ls -A /var/log/movemarias)" ]; then
    tar -czf "$BACKUP_DIR/logs/logs_${TIMESTAMP}.tar.gz" -C /var/log movemarias
    log "✅ Logs backup completed: logs_${TIMESTAMP}.tar.gz"
else
    log "ℹ️  No log files to backup"
fi

# 6. Create backup manifest
log "📋 Creating backup manifest..."
cat > "$BACKUP_DIR/manifest_${TIMESTAMP}.txt" << EOF
Move Marias Backup Manifest
===========================
Date: $(date)
Timestamp: $TIMESTAMP
Server: $(hostname)
Django Version: $(cd $PROJECT_DIR && python manage.py --version 2>/dev/null || echo "Unknown")

Files in this backup:
EOF

find "$BACKUP_DIR" -name "*${TIMESTAMP}*" -type f -exec ls -lh {} \; >> "$BACKUP_DIR/manifest_${TIMESTAMP}.txt"

# 7. Verify backups
log "🔍 Verifying backup integrity..."
BACKUP_ERRORS=0

# Check if backup files exist and are not empty
for backup_file in "$BACKUP_DIR"/*/"*${TIMESTAMP}*"; do
    if [ -f "$backup_file" ]; then
        if [ -s "$backup_file" ]; then
            log "✓ $backup_file - OK"
        else
            error "✗ $backup_file - Empty file"
            BACKUP_ERRORS=$((BACKUP_ERRORS + 1))
        fi
    fi
done

# Test database backup integrity
if [ -f "$BACKUP_DIR/database/db_${TIMESTAMP}.sql.gz" ]; then
    if gzip -t "$BACKUP_DIR/database/db_${TIMESTAMP}.sql.gz"; then
        log "✓ Database backup integrity - OK"
    else
        error "✗ Database backup corruption detected"
        BACKUP_ERRORS=$((BACKUP_ERRORS + 1))
    fi
fi

# 8. Cleanup old backups
log "🧹 Cleaning up old backups (keeping last $DAYS_TO_KEEP days)..."
find "$BACKUP_DIR" -type f -name "*.gz" -mtime +$DAYS_TO_KEEP -delete
find "$BACKUP_DIR" -type f -name "*.txt" -mtime +$DAYS_TO_KEEP -delete
find "$BACKUP_DIR" -type f -name "*.sqlite3" -mtime +$DAYS_TO_KEEP -delete

# Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -type f -name "*.gz" | wc -l)
log "📊 Total backups retained: $BACKUP_COUNT"

# 9. Calculate backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "💾 Total backup size: $TOTAL_SIZE"

# 10. Send notification if configured
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    if [ $BACKUP_ERRORS -eq 0 ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"✅ Move Marias backup completed successfully\nTimestamp: $TIMESTAMP\nSize: $TOTAL_SIZE\"}" \
            "$SLACK_WEBHOOK_URL" >/dev/null 2>&1
    else
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"❌ Move Marias backup completed with $BACKUP_ERRORS errors\nTimestamp: $TIMESTAMP\nCheck logs for details.\"}" \
            "$SLACK_WEBHOOK_URL" >/dev/null 2>&1
    fi
fi

# 11. Final status
if [ $BACKUP_ERRORS -eq 0 ]; then
    log "🎉 Backup process completed successfully!"
    log "📁 Backup location: $BACKUP_DIR"
    log "🏷️  Backup timestamp: $TIMESTAMP"
    exit 0
else
    error "❌ Backup process completed with $BACKUP_ERRORS errors"
    exit 1
fi
