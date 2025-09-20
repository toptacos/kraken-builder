#!/bin/bash

# Kraken Trading Bot - Recovery Script
# This script restores the application from backups

set -e

# Configuration
BACKUP_DIR="/app/backups"
RECOVERY_DIR="/tmp/kraken_recovery"

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

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [BACKUP_FILE]"
    echo ""
    echo "Options:"
    echo "  -l, --list          List available backups"
    echo "  -h, --help          Show this help message"
    echo "  -d, --dry-run       Show what would be restored without actually doing it"
    echo ""
    echo "Examples:"
    echo "  $0 --list"
    echo "  $0 kraken_backup_20231201_120000.tar.gz"
    echo "  $0 --dry-run kraken_backup_20231201_120000.tar.gz"
}

# List available backups
list_backups() {
    log_info "Available backups in $BACKUP_DIR:"

    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "Backup directory not found: $BACKUP_DIR"
        exit 1
    fi

    local count=0
    echo ""
    echo "Archives:"
    echo "---------"
    for backup in "$BACKUP_DIR"/*.tar.gz; do
        if [ -f "$backup" ]; then
            local size=$(du -h "$backup" | cut -f1)
            local date=$(stat -c %y "$backup" 2>/dev/null | cut -d'.' -f1 || echo "Unknown")
            echo "  $(basename "$backup") (${size}) - ${date}"
            ((count++))
        fi
    done

    if [ $count -eq 0 ]; then
        log_warning "No backup archives found"
    fi

    echo ""
    echo "Directories:"
    echo "------------"
    count=0
    for backup in "$BACKUP_DIR"/kraken_backup_*; do
        if [ -d "$backup" ]; then
            local size=$(du -sh "$backup" | cut -f1)
            local date=$(stat -c %y "$backup" 2>/dev/null | cut -d'.' -f1 || echo "Unknown")
            echo "  $(basename "$backup") (${size}) - ${date}"
            ((count++))
        fi
    done

    if [ $count -eq 0 ]; then
        log_warning "No backup directories found"
    fi
}

# Validate backup file
validate_backup() {
    local backup_file="$1"

    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi

    # Check if it's a valid tar.gz file
    if ! tar -tzf "$backup_file" >/dev/null 2>&1; then
        log_error "Invalid or corrupted backup file: $backup_file"
        exit 1
    fi

    log_success "Backup file validation passed: $backup_file"
}

# Extract backup
extract_backup() {
    local backup_file="$1"
    local dry_run="$2"

    log_info "Extracting backup..."

    if [ "$dry_run" = "true" ]; then
        log_info "[DRY RUN] Would extract: $backup_file"
        tar -tzf "$backup_file" | head -20
        return
    fi

    # Create recovery directory
    rm -rf "$RECOVERY_DIR"
    mkdir -p "$RECOVERY_DIR"

    # Extract backup
    if tar -xzf "$backup_file" -C "$RECOVERY_DIR"; then
        log_success "Backup extracted to: $RECOVERY_DIR"
    else
        log_error "Failed to extract backup"
        exit 1
    fi
}

# Restore logs
restore_logs() {
    local dry_run="$1"
    local logs_source="$RECOVERY_DIR"/*/logs
    local logs_dest="/app/logs"

    if [ -d "$logs_source" ]; then
        if [ "$dry_run" = "true" ]; then
            log_info "[DRY RUN] Would restore logs from: $logs_source"
            find "$logs_source" -type f | head -10
        else
            log_info "Restoring logs..."
            mkdir -p "$logs_dest"
            cp -r "$logs_source"/* "$logs_dest"/ 2>/dev/null || true
            log_success "Logs restored"
        fi
    else
        log_warning "No logs found in backup"
    fi
}

# Restore configuration
restore_config() {
    local dry_run="$1"
    local config_source="$RECOVERY_DIR"/*/config
    local config_dest="/app"

    if [ -d "$config_source" ]; then
        if [ "$dry_run" = "true" ]; then
            log_info "[DRY RUN] Would restore configuration from: $config_source"
            find "$config_source" -type f | head -10
        else
            log_info "Restoring configuration..."
            # Only restore non-sensitive configuration
            find "$config_source" -name "*.yml" -o -name "*.yaml" -o -name "*.json" | while read -r file; do
                cp "$file" "$config_dest"/ 2>/dev/null || true
            done
            log_success "Configuration restored (non-sensitive files only)"
        fi
    else
        log_warning "No configuration found in backup"
    fi
}

# Restore database
restore_database() {
    local dry_run="$1"
    local db_source="$RECOVERY_DIR"/*/database/database.sqlite.backup
    local db_dest="/app/laravel-backend/database/database.sqlite"

    if [ -f "$db_source" ]; then
        if [ "$dry_run" = "true" ]; then
            log_info "[DRY RUN] Would restore database from: $db_source"
            ls -la "$db_source"
        else
            log_info "Restoring database..."
            mkdir -p "$(dirname "$db_dest")"
            cp "$db_source" "$db_dest"
            log_success "Database restored"
        fi
    else
        log_warning "No database found in backup"
    fi
}

# Show recovery summary
show_summary() {
    local backup_file="$1"
    local dry_run="$2"

    echo ""
    echo "=========================================="
    echo "RECOVERY SUMMARY"
    echo "=========================================="
    echo "Backup File: $(basename "$backup_file")"
    echo "Recovery Directory: $RECOVERY_DIR"
    echo "Dry Run: $dry_run"
    echo ""

    if [ "$dry_run" = "false" ]; then
        echo "✅ Recovery completed successfully!"
        echo ""
        echo "Next steps:"
        echo "1. Restart the application: docker-compose restart"
        echo "2. Verify application functionality"
        echo "3. Check logs for any issues"
        echo "4. Test trading bot operations"
    else
        echo "📋 This was a dry run - no actual changes were made"
        echo "Run without --dry-run to perform actual recovery"
    fi
    echo "=========================================="
}

# Main recovery function
main() {
    local backup_file=""
    local list_only=false
    local dry_run=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -l|--list)
                list_only=true
                shift
                ;;
            -d|--dry-run)
                dry_run=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                if [ -z "$backup_file" ]; then
                    backup_file="$1"
                else
                    log_error "Multiple backup files specified"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # Handle list request
    if [ "$list_only" = true ]; then
        list_backups
        exit 0
    fi

    # Validate backup file
    if [ -z "$backup_file" ]; then
        log_error "No backup file specified"
        show_usage
        exit 1
    fi

    # Convert relative path to absolute if needed
    if [[ "$backup_file" != /* ]]; then
        backup_file="$BACKUP_DIR/$backup_file"
    fi

    # Validate and extract backup
    validate_backup "$backup_file"
    extract_backup "$backup_file" "$dry_run"

    if [ "$dry_run" = "false" ]; then
        # Perform actual recovery
        restore_logs "$dry_run"
        restore_config "$dry_run"
        restore_database "$dry_run"

        # Clean up recovery directory
        rm -rf "$RECOVERY_DIR"
    fi

    # Show summary
    show_summary "$backup_file" "$dry_run"
}

# Error handling
trap 'log_error "Recovery process failed with exit code $?"' ERR

# Run main function
main "$@"