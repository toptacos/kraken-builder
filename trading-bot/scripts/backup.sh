#!/bin/bash

# Kraken Trading Bot - Backup Script
# This script creates comprehensive backups of the application data

set -e

# Configuration
BACKUP_DIR="/app/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="kraken_backup_${TIMESTAMP}"
RETENTION_DAYS=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Create backup directory
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log_info "Created backup directory: $BACKUP_DIR"
    fi
}

# Backup application logs
backup_logs() {
    log_info "Backing up application logs..."

    local logs_dir="/app/logs"
    local backup_logs_dir="$BACKUP_DIR/$BACKUP_NAME/logs"

    if [ -d "$logs_dir" ]; then
        mkdir -p "$backup_logs_dir"
        cp -r "$logs_dir"/* "$backup_logs_dir"/ 2>/dev/null || true
        log_success "Logs backup completed"
    else
        log_warning "Logs directory not found: $logs_dir"
    fi
}

# Backup configuration files
backup_config() {
    log_info "Backing up configuration files..."

    local backup_config_dir="$BACKUP_DIR/$BACKUP_NAME/config"
    mkdir -p "$backup_config_dir"

    # Backup environment files (excluding sensitive data)
    if [ -f "/app/.env" ]; then
        # Create a sanitized version of .env for backup
        grep -v "API_KEY\|API_SECRET\|PRIVATE_KEY" /app/.env > "$backup_config_dir/env_backup.txt" 2>/dev/null || true
        log_success "Configuration backup completed (sanitized)"
    fi

    # Backup docker-compose file
    if [ -f "/app/docker-compose.yml" ]; then
        cp "/app/docker-compose.yml" "$backup_config_dir/"
    fi
}

# Backup database (if using SQLite)
backup_database() {
    log_info "Backing up database..."

    local db_file="/app/laravel-backend/database/database.sqlite"
    local backup_db_dir="$BACKUP_DIR/$BACKUP_NAME/database"

    if [ -f "$db_file" ]; then
        mkdir -p "$backup_db_dir"
        cp "$db_file" "$backup_db_dir/database.sqlite.backup"
        log_success "Database backup completed"
    else
        log_warning "Database file not found: $db_file"
    fi
}

# Create backup archive
create_archive() {
    log_info "Creating backup archive..."

    local archive_path="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"

    cd "$BACKUP_DIR"
    tar -czf "$archive_path" "$BACKUP_NAME"

    # Verify archive
    if [ -f "$archive_path" ]; then
        local size=$(du -h "$archive_path" | cut -f1)
        log_success "Backup archive created: $archive_path (${size})"
    else
        log_error "Failed to create backup archive"
        exit 1
    fi
}

# Clean up old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (older than $RETENTION_DAYS days)..."

    local deleted_count=0

    # Remove old archives
    find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete -print | while read -r file; do
        log_info "Deleted old backup: $file"
        ((deleted_count++))
    done

    # Remove old directories
    find "$BACKUP_DIR" -name "kraken_backup_*" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \; -print | while read -r dir; do
        log_info "Deleted old backup directory: $dir"
        ((deleted_count++))
    done

    if [ $deleted_count -eq 0 ]; then
        log_info "No old backups to clean up"
    else
        log_success "Cleaned up $deleted_count old backup(s)"
    fi
}

# Generate backup report
generate_report() {
    log_info "Generating backup report..."

    local report_file="$BACKUP_DIR/${BACKUP_NAME}_report.txt"
    local archive_size=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" 2>/dev/null | cut -f1 || echo "N/A")

    cat > "$report_file" << EOF
Kraken Trading Bot - Backup Report
===================================

Backup Date: $(date)
Backup Name: $BACKUP_NAME
Archive Size: $archive_size

Contents:
$(tar -tzf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | head -20)

System Information:
- Hostname: $(hostname)
- OS: $(uname -s) $(uname -r)
- User: $(whoami)

Backup Status: SUCCESS
EOF

    log_success "Backup report generated: $report_file"
}

# Main backup function
main() {
    log_info "Starting Kraken Trading Bot backup process..."

    # Create backup directory
    create_backup_dir

    # Perform backups
    backup_logs
    backup_config
    backup_database

    # Create archive
    create_archive

    # Generate report
    generate_report

    # Clean up old backups
    cleanup_old_backups

    log_success "Backup process completed successfully!"
    log_info "Backup location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
}

# Error handling
trap 'log_error "Backup process failed with exit code $?"' ERR

# Run main function
main "$@"