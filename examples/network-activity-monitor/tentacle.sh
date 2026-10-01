#!/bin/bash

set -euo pipefail  # Best practice: Exit on error, undefined vars, pipe failures

# DISCLAIMER: This script is intended for legal and ethical use only, such as parental monitoring on your own home network with explicit consent. Using it to intercept or monitor network traffic without authorization may violate privacy laws (e.g., wiretapping statutes, GDPR, COPPA) and could lead to legal consequences. It is provided as a proof of concept for educational purposes. The author disclaims all liability for misuse. Always obtain consent and consult local laws before use. This script requires proper network configuration (e.g., port mirroring on your modem/router to the machine's interface to see all traffic) and may not work on all setups, including iOS devices without jailbreaking (use apps instead for iPhone). For portability, run on Linux/macOS/WSL; configure modem entrypoint via router settings to mirror traffic.

# Modular and efficient proof-of-concept bash script to capture live traffic for a configurable duration
# on specified ports (default all), save to a temporary pcap file, then extract top unique domains accessed by devices on the network, ignoring known extensions like Grammarly, Spotify, etc.
# Uses tshark (Wireshark CLI) as a capture service model (not source of truth; can be swapped with tcpdump or other tools, e.g., tcpdump -i any -w file.pcap).
# Default behavior: Captures on all available active interfaces, avoids local device traffic unless --include-local is specified, runs in a continuous loop for monitoring during the day.
# Usage: sudo ./script.sh [--select] [--num N] [--duration S] [--include-local] [--log-path PATH] [--ports PORT1,PORT2,...] [--no-loop] [--parse-logs] [--view] [--realtime]
# - --select: Displays a menu to select a single interface.
# - --num N: Number of top domains to extract (default 50).
# - --duration S: Capture duration in seconds (default 30); also used as sleep interval in loop.
# - --include-local: Include traffic from the local device (default: exclude).
# - --log-path PATH: Override default log file path.
# - --ports PORT1,PORT2,...: Comma-separated list of ports to capture (default: all ports).
# - --no-loop: Run once instead of in a continuous loop.
# - --parse-logs: Parse all available log files and output in a human-readable format.
# - --view: Open browser tabs instead of displaying in terminal.
# - --dashboard: Enable simplified dashboard view with comprehensive traffic analysis.
# Assumptions and notes:
# - Requires Wireshark/tshark installed; dynamically locates tshark.
# - Must run with sudo for capture permissions.
# - Outputs pretty-printed JSON to stdout each cycle; exports to JSON/CSV/HTML for data export, opens HTML in default browser for top domains if --view.
# - For portability: Works on Linux and macOS; for Windows, use WSL with tshark; not supported on iOS without jailbreak (use apps instead).
# - To run in tmux: tmux new -s monitor ./script.sh
# - Network-wide monitoring: Assumes interfaces are in promiscuous/monitor mode for Wi-Fi (setup required, e.g., airmon-ng on Linux) or port mirroring on modem/router.
# - Log file: Defaults to script_dir/storage/logs_YYYYMMDD.log; timestamped per day; logs everything in text format for easy parsing.
# - Pretty print: Uses jq if available for JSON; generates HTML with JavaScript filter for timelines, domains, and decrypted requests, opens in default browser if --view.
# - Ignore known extensions: Filters out domains like *.grammarly.com, *.spotify.com, etc.
# - Group by domain: Groups requests by domain, shows top by frequency, with counts; includes subrequests (subdomains) underneath main domains if detected.
# - Data export: Exports to cycle.json, cycle.csv, cycle.html each cycle; logs for deeper digging.
# - Enhanced real-time monitoring: Live display with comprehensive device statistics, bandwidth monitoring, protocol analysis, and activity tracking.
# - Fixed: Syntax errors, mislogs, truncated code, invalid options (avoided associative arrays for portability), grouped by domain, ignore extensions, pretty print, data export, browser open, all ports default, log rename with timestamp, flag for log override, get_local_addrs command not found by ensuring definition before use, sed issue by switching to text log format, etc.
# - Updated: Storage directory in script's directory for logs, checked for creation; refresh current log file contents (append properly); includes --parse-logs flag to parse all log files (outputs to console in readable format); all ports default with --ports flag for specific; spider all devices with arp -a at start; --out refactored to --view; fixed grep -oP issue by using cross-platform awk; fixed jq parse error by sanitizing data with tr -d '[\000-\037]'.

# Constants (configurable)
DEFAULT_NUM_SITES=50
DEFAULT_CAPTURE_DURATION=30  # seconds
STORAGE_DIR="$(dirname "$0")/storage"
TEST_DURATION=1  # seconds for interface test
IGNORED_DOMAINS=("grammarly.com" "spotify.com" "doubleclick.net" "google-analytics.com" "example.com")  # Add more to ignore

# Create storage directory if not exists
mkdir -p "$STORAGE_DIR" || { echo "Error: Failed to create $STORAGE_DIR" >&2; exit 1; }

# Set log file to text per day
SCRIPT_NAME=$(basename "$0" .sh)
DAY_TIMESTAMP=$(date +%Y%m%d)
LOG_FILE="$STORAGE_DIR/logs_${DAY_TIMESTAMP}.log"

# Logging function: Append timestamped message to log file
log_verbose() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S') || return
    echo "[$timestamp] $*" >> "$LOG_FILE" || echo "Warning: Failed to log" >&2
}

# Parse all log files
parse_logs() {
    local storage_dir="$1"
    echo "Parsing all log files in $storage_dir:"
    for log in "$storage_dir"/logs_*.log; do
        if [ -f "$log" ]; then
            echo "Log file: $log"
            cat "$log"
            echo ""
        fi
    done
}

# Display cool taco logo ASCII art
display_logo() {
    log_verbose "Displaying logo"
    cat <<EOF
┈┈┈┈╭╯╭╯╭╯┈┈┈┈┈
┈┈┈╱▔▔▔▔▔╲▔╲┈┈┈
┈┈╱┈╭╮┈╭╮┈╲╮╲┈┈
┈┈▏┈▂▂▂▂▂┈▕╮▕┈┈
┈┈▏┈╲▂▂▂╱┈▕╮▕┈┈
┈┈╲▂▂▂▂▂▂▂▂╲╱┈┈
EOF
}

# Locate packet capture tool (tshark preferred, tcpdump fallback)
locate_capture_tool() {
    log_verbose "Locating packet capture tool"

    # Try tshark first (Wireshark CLI)
    local capture_tool=$(command -v tshark)
    if [ -n "$capture_tool" ]; then
        log_verbose "tshark found at: $capture_tool"
        echo "$capture_tool"
        return
    fi

    # Try alternative tshark locations
    local possible_tshark_paths=(
        "/Applications/Wireshark.app/Contents/MacOS/tshark"
        "/usr/local/bin/tshark"
        "/usr/sbin/tshark"
        "/usr/bin/tshark"
        "/opt/local/bin/tshark"
    )
    for path in "${possible_tshark_paths[@]}"; do
        if [ -x "$path" ]; then
            log_verbose "tshark found at: $path"
            echo "$path"
            return
        fi
    done

    # Fallback to tcpdump
    local tcpdump_tool=$(command -v tcpdump)
    if [ -n "$tcpdump_tool" ]; then
        log_verbose "tshark not found, using tcpdump at: $tcpdump_tool"
        echo "$tcpdump_tool"
        return
    fi

    # Try alternative tcpdump locations
    local possible_tcpdump_paths=(
        "/usr/sbin/tcpdump"
        "/usr/bin/tcpdump"
        "/usr/local/sbin/tcpdump"
        "/usr/local/bin/tcpdump"
    )
    for path in "${possible_tcpdump_paths[@]}"; do
        if [ -x "$path" ]; then
            log_verbose "tshark not found, using tcpdump at: $path"
            echo "$path"
            return
        fi
    done

    log_verbose "Error: No packet capture tool found"
    echo "Error: Neither tshark nor tcpdump found." >&2
    echo "Please install one of the following:" >&2
    echo "  - Wireshark (includes tshark): brew install wireshark" >&2
    echo "  - tcpdump: brew install tcpdump" >&2
    echo "  - Or install via your system package manager" >&2
    exit 1
}

# Get active network interfaces from system (source of truth)
get_active_interfaces() {
    log_verbose "Getting active interfaces"
    local os=$(uname -s)
    local interfaces
    case "$os" in
        Linux)
            interfaces=$(ip -o link show up 2>/dev/null | awk -F': ' '{print $2}' | sed 's/@.*//' | grep -v '^lo$')
            ;;
        Darwin)
            interfaces=$(ifconfig 2>/dev/null | grep -E '^[a-z0-9]+:' | cut -d: -f1 | grep -v '^lo0$')
            ;;
        *)
            log_verbose "Error: Unsupported OS"
            echo "Error: Unsupported OS for interface detection." >&2
            exit 1
            ;;
    esac
    log_verbose "Active interfaces: $interfaces"
    echo "$interfaces"
}

# Get human-readable description for an interface
get_interface_description() {
    local intf="$1"
    local os="$2"
    local desc="Unknown"
    case "$os" in
        Linux)
            if [ -d "/sys/class/net/$intf/wireless" ]; then
                desc="Wi-Fi"
            else
                desc="Ethernet"
            fi
            ;;
        Darwin)
            desc=$(networksetup -listallhardwareports 2>/dev/null | awk '
                /^Hardware Port:/ { hp = substr($0, index($0,$3)) }
                /^Device:/ { if (hp) { desc[$2] = hp; hp = "" } }
                END { print desc["'"$intf"'"] ? desc["'"$intf"'"] : "Unknown" }
            ')
            ;;
    esac
    echo "$desc"
}

# Resolve hostname for an IP address
resolve_hostname() {
    local ip="$1"
    local hostname=""
    # Try to resolve hostname using various methods
    if command -v nslookup &> /dev/null; then
        hostname=$(nslookup "$ip" 2>/dev/null | awk '/name =/ {print $4}' | head -1)
    elif command -v dig &> /dev/null; then
        hostname=$(dig +short -x "$ip" 2>/dev/null | head -1)
    elif command -v host &> /dev/null; then
        hostname=$(host "$ip" 2>/dev/null | awk '/domain name pointer/ {print $5}' | head -1)
    fi
    # Remove trailing dot if present
    hostname="${hostname%.}"
    echo "${hostname:-$ip}"
}

# Load custom device names from configuration file
load_custom_names() {
    local config_file="$STORAGE_DIR/device_names.conf"
    local custom_names_str=""
    if [ -f "$config_file" ]; then
        log_verbose "Loading custom device names from $config_file"
        while IFS='=' read -r ip name; do
            # Skip comments and empty lines
            [[ $ip =~ ^[[:space:]]*# ]] && continue
            [[ -z "$ip" ]] && continue
            # Trim whitespace
            ip=$(echo "$ip" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            name=$(echo "$name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            if [ -n "$ip" ] && [ -n "$name" ]; then
                custom_names_str="${custom_names_str}${ip}=${name}\n"
                log_verbose "Loaded custom name: $ip -> $name"
            fi
        done < "$config_file"
    fi
    echo "$custom_names_str"
}

# Load parental controls configuration
load_parental_controls() {
    local config_file="$STORAGE_DIR/parental_controls.conf"
    local controls=""

    if [ -f "$config_file" ]; then
        log_verbose "Loading parental controls from $config_file"

        # Read all settings
        ENABLE_PARENTAL_CONTROLS=$(grep "^ENABLE_PARENTAL_CONTROLS=" "$config_file" | cut -d'=' -f2)
        ALERT_LEVEL=$(grep "^ALERT_LEVEL=" "$config_file" | cut -d'=' -f2)
        BLOCKED_CATEGORIES=$(grep "^BLOCKED_CATEGORIES=" "$config_file" | cut -d'=' -f2)
        LOG_CONCERNING_ACTIVITY=$(grep "^LOG_CONCERNING_ACTIVITY=" "$config_file" | cut -d'=' -f2)
        LOG_SAFE_ACTIVITY=$(grep "^LOG_SAFE_ACTIVITY=" "$config_file" | cut -d'=' -f2)
        ALERT_TO_SYSTEM_LOG=$(grep "^ALERT_TO_SYSTEM_LOG=" "$config_file" | cut -d'=' -f2)

        # Load allowed sites
        local allowed_sites=""
        while IFS= read -r site; do
            if [ -n "$site" ]; then
                allowed_sites="${allowed_sites}${site}\n"
            fi
        done < <(grep "^ALLOWED_SITES=" "$config_file" | cut -d'=' -f2)

        # Load custom blocked domains
        local custom_blocked=""
        while IFS= read -r site; do
            if [ -n "$site" ]; then
                custom_blocked="${custom_blocked}${site}\n"
            fi
        done < <(grep "^CUSTOM_BLOCKED=" "$config_file" | cut -d'=' -f2)

        # Load concerning keywords
        local concerning_keywords=""
        while IFS= read -r keyword; do
            if [ -n "$keyword" ]; then
                concerning_keywords="${concerning_keywords}${keyword}\n"
            fi
        done < <(grep "^CONCERNING_KEYWORDS=" "$config_file" | cut -d'=' -f2)

        controls="enabled:${ENABLE_PARENTAL_CONTROLS:-true}:alert_level:${ALERT_LEVEL:-medium}:blocked:${BLOCKED_CATEGORIES:-adult_content}:allowed:${allowed_sites}:custom_blocked:${custom_blocked}:keywords:${concerning_keywords}:log_concerning:${LOG_CONCERNING_ACTIVITY:-true}:log_safe:${LOG_SAFE_ACTIVITY:-false}:system_log:${ALERT_TO_SYSTEM_LOG:-true}"
    else
        # Default settings if no config file
        controls="enabled:true:alert_level:medium:blocked:adult_content:allowed::custom_blocked::keywords::log_concerning:true:log_safe:false:system_log:true"
    fi

    echo "$controls"
}

# Check if site is allowed
is_site_allowed() {
    local domain="$1"
    local allowed_sites="$2"

    if [ -n "$allowed_sites" ]; then
        echo "$allowed_sites" | grep -q "^${domain}$"
        return $?
    fi
    return 1
}

# Check if site is custom blocked
is_site_custom_blocked() {
    local domain="$1"
    local custom_blocked="$2"

    if [ -n "$custom_blocked" ]; then
        echo "$custom_blocked" | grep -q "^${domain}$"
        return $?
    fi
    return 1
}

# Check for concerning keywords
has_concerning_keywords() {
    local domain="$1"
    local keywords="$2"

    if [ -n "$keywords" ]; then
        while IFS= read -r keyword; do
            if [ -n "$keyword" ]; then
                if echo "$domain" | grep -qi "$keyword"; then
                    return 0
                fi
            fi
        done <<< "$keywords"
    fi
    return 1
}

# Get friendly name for a device
get_friendly_name() {
    local ip="$1"
    local vendor="$2"
    local custom_names_str="$3"

    # Try to get custom name first
    local custom_name=$(echo "$custom_names_str" | grep "^$ip=" | cut -d'=' -f2 || true)
    if [ -n "$custom_name" ]; then
        echo "$custom_name"
        return
    fi

    # Try to resolve hostname
    local hostname=$(resolve_hostname "$ip")
    if [ "$hostname" != "$ip" ]; then
        echo "$hostname"
        return
    fi

    # Fall back to IP with vendor info
    echo "$ip ($vendor)"
}

# Categorize website content for parental controls
categorize_website() {
    local domain="$1"
    local controls="$2"
    local category="unknown"
    local risk_level="low"

    # Extract settings from controls string
    local blocked_categories=$(echo "$controls" | sed -n 's/.*blocked:\([^:]*\).*/\1/p')
    local allowed_sites=$(echo "$controls" | sed -n 's/.*allowed:\([^:]*\).*/\1/p')
    local custom_blocked=$(echo "$controls" | sed -n 's/.*custom_blocked:\([^:]*\).*/\1/p')
    local concerning_keywords=$(echo "$controls" | sed -n 's/.*keywords:\([^:]*\).*/\1/p')

    # Check if site is explicitly allowed
    if is_site_allowed "$domain" "$allowed_sites"; then
        category="allowed"
        risk_level="low"
        echo "$category:$risk_level"
        return
    fi

    # Check if site is custom blocked
    if is_site_custom_blocked "$domain" "$custom_blocked"; then
        category="custom_blocked"
        risk_level="high"
        echo "$category:$risk_level"
        return
    fi

    # Check for concerning keywords
    if has_concerning_keywords "$domain" "$concerning_keywords"; then
        category="concerning_keywords"
        risk_level="high"
        echo "$category:$risk_level"
        return
    fi

    # Adult content sites
    if echo "$domain" | grep -qiE '\b(porn|sex|adult|xxx|hentai|erotic|cam|livejasmin|chaturbate|onlyfans|playboy|penthouse)\b'; then
        category="adult_content"
        risk_level="high"
    # Social media
    elif echo "$domain" | grep -qiE '\b(tiktok|instagram|snapchat|facebook|twitter|x\.com|reddit|tumblr|pinterest|linkedin)\b'; then
        category="social_media"
        risk_level="medium"
    # Gaming sites
    elif echo "$domain" | grep -qiE '\b(roblox|minecraft|fortnite|steam|epicgames|twitch|gaming|leagueoflegends|valorant|apexlegends)\b'; then
        category="gaming"
        risk_level="medium"
    # Video streaming
    elif echo "$domain" | grep -qiE '\b(youtube|netflix|disney|amazon.*video|hulu|twitch|hbomax|peacock|paramount)\b'; then
        category="video_streaming"
        risk_level="low"
    # Educational sites
    elif echo "$domain" | grep -qiE '\b(khanacademy|duolingo|codecademy|coursera|edx|educational|school|college|university)\b'; then
        category="educational"
        risk_level="low"
    # Shopping sites
    elif echo "$domain" | grep -qiE '\b(amazon|ebay|walmart|target|shopping|store|bestbuy|costco|etsy)\b'; then
        category="shopping"
        risk_level="low"
    # News sites
    elif echo "$domain" | grep -qiE '\b(cnn|bbc|foxnews|news|reuters|apnews|nbcnews|cbsnews|abcnews|usatoday)\b'; then
        category="news"
        risk_level="low"
    # Search engines
    elif echo "$domain" | grep -qiE '\b(google|yahoo|bing|duckduckgo|search|ecosia|startpage)\b'; then
        category="search_engine"
        risk_level="low"
    # File sharing
    elif echo "$domain" | grep -qiE '\b(dropbox|googledrive|onedrive|mega|fileshare|upload|mediafire|box|icloud)\b'; then
        category="file_sharing"
        risk_level="medium"
    # VPN/Proxy sites
    elif echo "$domain" | grep -qiE '\b(vpn|proxy|tor|anonymizer|hideip|unblock|unblocked|proxy-site)\b'; then
        category="vpn_proxy"
        risk_level="high"
    # Gambling sites
    elif echo "$domain" | grep -qiE '\b(casino|gambling|poker|betting|lottery|slots|bingo)\b'; then
        category="gambling"
        risk_level="high"
    # Dating sites
    elif echo "$domain" | grep -qiE '\b(dating|match|love|romance|singles|personals)\b'; then
        category="dating"
        risk_level="high"
    # File sharing/torrent sites
    elif echo "$domain" | grep -qiE '\b(torrent|pirate|thepiratebay|rarbg|1337x|kickass|yts)\b'; then
        category="torrent_piracy"
        risk_level="high"
    fi

    echo "$category:$risk_level"
}

# Check if site should trigger alert
should_alert() {
    local category="$1"
    local risk_level="$2"

    # High risk sites always alert
    if [ "$risk_level" = "high" ]; then
        return 0
    fi

    # Check for specific blocked categories
    case "$category" in
        adult_content|vpn_proxy)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Log concerning activity immediately
log_concerning_activity() {
    local device="$1"
    local ip="$2"
    local domain="$3"
    local category="$4"
    local risk_level="$5"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "🚨 CONCERNING ACTIVITY DETECTED: $timestamp" >> "$LOG_FILE"
    echo "   Device: $device ($ip)" >> "$LOG_FILE"
    echo "   Site: $domain" >> "$LOG_FILE"
    echo "   Category: $category" >> "$LOG_FILE"
    echo "   Risk Level: $risk_level" >> "$LOG_FILE"
    echo "   Action: PARENTAL ALERT TRIGGERED" >> "$LOG_FILE"
    echo "---" >> "$LOG_FILE"

    # Also log to system log if possible
    if command -v logger &> /dev/null; then
        logger -t "NetworkMonitor" "CONCERNING ACTIVITY: $device accessed $domain ($category - $risk_level)"
    fi
}

# Detect VPN usage and bypass attempts
detect_vpn_activity() {
    local data="$1"
    local device="$2"
    local ip="$3"

    # Check for common VPN indicators
    local vpn_detected=0
    local vpn_type=""

    # Check for VPN protocols
    if echo "$data" | grep -qi "openvpn\|pptp\|l2tp\|ipsec\|wireguard\|sstp"; then
        vpn_detected=1
        vpn_type="VPN Protocol"
    fi

    # Check for VPN server IPs (common VPN providers)
    if echo "$data" | grep -qE '198\.100\.|162\.159\.|104\.16\.|104\.17\.|104\.18\.|104\.19\.|104\.20\.|104\.21\.'; then
        vpn_detected=1
        vpn_type="VPN Provider"
    fi

    # Check for DNS leaks (using external DNS while on VPN)
    if echo "$data" | grep -qE '8\.8\.8\.8|8\.8\.4\.4|1\.1\.1\.1|1\.0\.0\.1|208\.67\.222\.222|208\.67\.220\.220'; then
        vpn_detected=1
        vpn_type="DNS Leak"
    fi

    # Check for VPN-specific ports
    if echo "$data" | grep -qE '1194|1723|1701|500|4500|51820'; then
        vpn_detected=1
        vpn_type="VPN Port"
    fi

    # Check for obfuscated traffic patterns
    if echo "$data" | grep -q "obfs4\|obfs3\|scramblesuit\|meek"; then
        vpn_detected=1
        vpn_type="Obfuscated VPN"
    fi

    if [ $vpn_detected -eq 1 ]; then
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "🔒 VPN ACTIVITY DETECTED: $timestamp" >> "$LOG_FILE"
        echo "   Device: $device ($ip)" >> "$LOG_FILE"
        echo "   VPN Type: $vpn_type" >> "$LOG_FILE"
        echo "   Status: VPN BYPASS ATTEMPT DETECTED" >> "$LOG_FILE"
        echo "   Action: MONITORING ENHANCED" >> "$LOG_FILE"
        echo "---" >> "$LOG_FILE"

        if command -v logger &> /dev/null; then
            logger -t "NetworkMonitor" "VPN DETECTED: $device using $vpn_type - BYPASS ATTEMPT"
        fi

        return 0
    fi

    return 1
}

# Track public IP addresses and external connections
track_public_ips() {
    local data="$1"
    local device="$2"
    local local_ip="$3"

    # Extract all destination IPs
    echo "$data" | awk -F $'\t' '$5 != "" && $5 !~ /^192\.168\.|^10\.|^172\.(1[6-9]|2[0-9]|3[0-1])\./ {print $5}' | sort -u | while IFS= read -r public_ip; do
        if [ -n "$public_ip" ] && [ "$public_ip" != "$local_ip" ]; then
            local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            echo "🌐 PUBLIC IP CONNECTION: $timestamp" >> "$LOG_FILE"
            echo "   Device: $device ($local_ip)" >> "$LOG_FILE"
            echo "   Public IP: $public_ip" >> "$LOG_FILE"
            echo "   Connection: External traffic detected" >> "$LOG_FILE"
            echo "---" >> "$LOG_FILE"
        fi
    done || true
}

# Enhanced traffic analysis for all protocols
analyze_all_traffic() {
    local data="$1"
    local device="$2"
    local ip="$3"

    # Detect VPN activity
    detect_vpn_activity "$data" "$device" "$ip"

    # Track public IP connections
    track_public_ips "$data" "$device" "$ip"

    # Analyze traffic patterns
    local http_count=$(echo "$data" | grep -c "http" || true)
    local https_count=$(echo "$data" | grep -c "tls" || true)
    local dns_count=$(echo "$data" | grep -c "dns" || true)
    local udp_count=$(echo "$data" | grep -c "udp" || true)
    local tcp_count=$(echo "$data" | grep -c "tcp" || true)
    local icmp_count=$(echo "$data" | grep -c "icmp" || true)

    # Calculate total traffic
    local total_bytes=$(echo "$data" | awk -F $'\t' '{sum += $2} END {print sum}')
    local total_packets=$(echo "$data" | wc -l)

    # Log comprehensive traffic summary
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "📊 TRAFFIC ANALYSIS: $timestamp" >> "$LOG_FILE"
    echo "   Device: $device ($ip)" >> "$LOG_FILE"
    echo "   Total Packets: $total_packets" >> "$LOG_FILE"
    echo "   Total Bytes: $total_bytes" >> "$LOG_FILE"
    echo "   Protocol Breakdown:" >> "$LOG_FILE"
    echo "     HTTP: $http_count requests" >> "$LOG_FILE"
    echo "     HTTPS: $https_count connections" >> "$LOG_FILE"
    echo "     DNS: $dns_count queries" >> "$LOG_FILE"
    echo "     TCP: $tcp_count packets" >> "$LOG_FILE"
    echo "     UDP: $udp_count packets" >> "$LOG_FILE"
    echo "     ICMP: $icmp_count packets" >> "$LOG_FILE"
    echo "---" >> "$LOG_FILE"
}

# Clear screen and display real-time header
display_realtime_header() {
    local cycle="$1"
    local duration="$2"
    clear
    display_logo
    echo "=== REAL-TIME NETWORK MONITORING ==="
    echo "Cycle: $cycle | Duration: ${duration}s | Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "====================================="
    echo ""
}

# Analyze comprehensive device data
analyze_device_data() {
    local data="$1"
    local num_sites="$2"
    log_verbose "Analyzing comprehensive device data"

    # Process data with enhanced fields
    echo "$data" | awk -F $'\t' -v ignore_list="$(IFS=','; echo "${IGNORED_DOMAINS[*]}")" '
    BEGIN {
        split(ignore_list, ignores, ",")
        # Initialize counters
        device_count = 0
        total_packets = 0
        total_bytes = 0
    }
    {
        # Extract source IP (field 4)
        src_ip = $4
        if (src_ip == "") next

        # Skip ignored domains
        host = ($10 != "" ? $10 : $14)
        if (host != "") {
            ignore = 0
            for (i in ignores) {
                if (host ~ ignores[i]) { ignore = 1; break }
            }
            if (ignore == 1) next
        }

        # Count packets and bytes
        packets[src_ip]++
        bytes[src_ip] += $2
        total_packets++
        total_bytes += $2

        # Track protocols
        protocols[src_ip] = protocols[src_ip] $3 " "

        # Track ports and services
        if ($6 != "") ports[src_ip] = ports[src_ip] $6 " "
        if ($7 != "") ports[src_ip] = ports[src_ip] $7 " "
        if ($8 != "") ports[src_ip] = ports[src_ip] $8 " "
        if ($9 != "") ports[src_ip] = ports[src_ip] $9 " "

        # Track HTTP methods and status codes
        if ($12 != "") http_methods[src_ip] = http_methods[src_ip] $12 " "
        if ($13 != "") http_status[src_ip] = http_status[src_ip] $13 " "

        # Track DNS queries
        if ($15 != "") dns_queries[src_ip] = dns_queries[src_ip] $15 " "

        # Track connection states
        if ($18 != "") conn_flags[src_ip] = conn_flags[src_ip] $18 " "

        # Track TTL for device identification
        if ($17 != "") ttl_values[src_ip] = ttl_values[src_ip] $17 " "

        # Track domains
        if (host != "") {
            domains[src_ip] = domains[src_ip] host " "
        }

        # Mark device as active
        active[src_ip] = 1
    }
    END {
        # Output device statistics
        for (ip in active) {
            # Calculate unique domains
            split(domains[ip], domain_list, " ")
            unique_domains = 0
            domain_count = ""
            for (i in domain_list) {
                if (domain_list[i] != "" && !seen_domain[ip, domain_list[i]]++) {
                    unique_domains++
                    domain_count = domain_count domain_list[i] " "
                }
            }

            # Get top domains by frequency
            delete freq
            for (i in domain_list) {
                if (domain_list[i] != "") freq[domain_list[i]]++
            }
            top_domains = ""
            for (domain in freq) {
                if (top_domains == "") {
                    top_domains = domain " (" freq[domain] ")"
                } else {
                    top_domains = top_domains ", " domain " (" freq[domain] ")"
                }
            }

            # Get unique ports
            split(ports[ip], port_list, " ")
            unique_ports = ""
            for (i in port_list) {
                if (port_list[i] != "" && !seen_port[ip, port_list[i]]++) {
                    if (unique_ports == "") {
                        unique_ports = port_list[i]
                    } else {
                        unique_ports = unique_ports "," port_list[i]
                    }
                }
            }

            # Get protocol breakdown
            split(protocols[ip], proto_list, " ")
            proto_count = ""
            delete proto_freq
            for (i in proto_list) {
                if (proto_list[i] != "") proto_freq[proto_list[i]]++
            }
            for (proto in proto_freq) {
                if (proto_count == "") {
                    proto_count = proto " (" proto_freq[proto] ")"
                } else {
                    proto_count = proto_count ", " proto " (" proto_freq[proto] ")"
                }
            }

            print ip "\t" packets[ip] "\t" bytes[ip] "\t" unique_domains "\t" top_domains "\t" unique_ports "\t" proto_count
        }
    }' | sort -k2,2 -nr
}

# Display simplified dashboard view for easy traffic monitoring
display_simple_dashboard() {
    local json="$1"
    local cycle="$2"
    local duration="$3"
    local parental_controls="$4"

    clear
    display_logo
    echo "🌐 NETWORK TRAFFIC DASHBOARD"
    echo "══════════════════════════════════════════════════════════"
    echo "Cycle: $cycle | Duration: ${duration}s | Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "══════════════════════════════════════════════════════════"
    echo ""

    # Check for VPN activity and concerning content
    local has_vpn_activity=0
    local has_concerning_activity=0

    while IFS=$'\t' read -r device ip requests packets bytes protocols websites; do
        if [ -n "$websites" ]; then
            while IFS='()' read -r domain_info; do
                domain_info=$(echo "$domain_info" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                if [ -n "$domain_info" ]; then
                    if echo "$domain_info" | grep -q "🚨 CONCERNING:"; then
                        has_concerning_activity=1
                    fi
                fi
            done <<< "$(echo "$websites" | tr ',' '\n')"
        fi
    done < <(echo "$json" | jq -r '.devices[] | "\(.device)\t\(.ip)\t\(.stats.total_requests)\t\(.stats.packets)\t\(.stats.bytes)\t\(.protocols)\t\(.websites)"')

    # Show alerts if any concerning activity detected
    if [ "$has_concerning_activity" -eq 1 ]; then
        echo "🚨🚨🚨 CRITICAL ALERTS 🚨🚨🚨"
        echo "══════════════════════════════════"
        echo "⚠️  CONCERNING ACTIVITY DETECTED!"
        echo "══════════════════════════════════"
        echo ""
    fi

    # Show VPN detection alerts
    while IFS=$'\t' read -r device ip protocols; do
        if echo "$protocols" | grep -qi "vpn\|openvpn\|wireguard\|ipsec"; then
            has_vpn_activity=1
        fi
    done < <(echo "$json" | jq -r '.devices[] | "\(.device)\t\(.ip)\t\(.protocols)"')

    if [ "$has_vpn_activity" -eq 1 ]; then
        echo "🔒🔒🔒 VPN DETECTION 🚨🔒🔒🔒"
        echo "══════════════════════════════════"
        echo "⚠️  VPN/BYPASS ACTIVITY DETECTED!"
        echo "══════════════════════════════════"
        echo ""
    fi

    echo "📊 DEVICE TRAFFIC SUMMARY"
    echo "══════════════════════════════════"
    echo "Device Name              │ Local IP      │ Requests │ Packets │ Bytes     │ Status"
    echo "─────────────────────────┼───────────────┼──────────┼─────────┼───────────┼────────"

    local activity_status="🟢 ACTIVE"
    local packet_rate=0
    echo "$json" | jq -r '.devices[] | "\(.device)\t\(.ip)\t\(.stats.total_requests)\t\(.stats.packets)\t\(.stats.bytes)"' | while IFS=$'\t' read -r device ip requests packets bytes; do
        # Calculate activity level
        activity_status="🟢 ACTIVE"
        if [ "$duration" -gt 0 ]; then
            packet_rate=$((packets / duration))
        else
            packet_rate=0
        fi

        if [ $packet_rate -gt 1000 ]; then
            activity_status="🟡 BUSY"
        fi
        if [ $packet_rate -gt 5000 ]; then
            activity_status="🔴 HEAVY"
        fi

        # Format device name to fixed width
        device=$(printf "%-23s" "$device")

        # Format numbers with commas
        requests=$(printf "%8s" $(echo "$requests" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta'))
        packets=$(printf "%7s" $(echo "$packets" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta'))
        bytes=$(printf "%9s" $(echo "$bytes" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta'))

        printf "%s │ %s │ %s │ %s │ %s │ %s\n" \
            "$device" "$ip" "$requests" "$packets" "$bytes" "$activity_status"
    done || true

    echo ""
    echo "🌐 CURRENT WEB ACTIVITY"
    echo "══════════════════════════════════"
    echo "Device Name              │ Domain                    │ Category      │ Status"
    echo "─────────────────────────┼───────────────────────────┼───────────────┼────────"

    echo "$json" | jq -r '.devices[] | "\(.device)\t\(.ip)\t\(.websites)"' | while IFS=$'\t' read -r device ip websites; do
        if [ -n "$websites" ]; then
            echo "$websites" | tr ',' '\n' | while IFS='()' read -r domain_info; do
                domain_info=$(echo "$domain_info" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                if [ -n "$domain_info" ]; then
                    if echo "$domain_info" | grep -q "🚨 CONCERNING:"; then
                        local concerning_part=$(echo "$domain_info" | sed 's/🚨 CONCERNING: //')
                        echo "$concerning_part" | tr ',' '\n' | while IFS='()' read -r domain count category; do
                            domain=$(echo "$domain" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                            category=$(echo "$category" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                            if [ -n "$domain" ]; then
                                device=$(printf "%-23s" "$device")
                                domain=$(printf "%-25s" "$domain")
                                category=$(printf "%-13s" "$category")
                                printf "%s │ %s │ %s │ 🚨 BLOCKED\n" \
                                    "$device" "$domain" "$category"
                            fi
                        done
                    elif echo "$domain_info" | grep -q "✅ SAFE:"; then
                        local safe_part=$(echo "$domain_info" | sed 's/✅ SAFE: //')
                        echo "$safe_part" | tr ',' '\n' | while IFS='()' read -r domain count category; do
                            domain=$(echo "$domain" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                            category=$(echo "$category" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                            if [ -n "$domain" ]; then
                                device=$(printf "%-23s" "$device")
                                domain=$(printf "%-25s" "$domain")
                                category=$(printf "%-13s" "$category")
                                printf "%s │ %s │ %s │ ✅ ALLOWED\n" \
                                    "$device" "$domain" "$category"
                            fi
                        done
                    fi
                fi
            done
        fi
    done || true

    echo ""
    echo "🔍 PROTOCOL ANALYSIS"
    echo "══════════════════════════════════"
    echo "Device Name              │ Protocol Breakdown"
    echo "─────────────────────────┼───────────────────────────"

    echo "$json" | jq -r '.devices[] | "\(.device)\t\(.protocols)"' | while IFS=$'\t' read -r device protocols; do
        if [ -n "$protocols" ]; then
            device=$(printf "%-23s" "$device")
            printf "%s │ %s\n" "$device" "$protocols"
        fi
    done || true

    echo ""
    echo "📈 NETWORK HEALTH"
    echo "══════════════════════════════════"
    echo "Total Devices Active: $(echo "$json" | jq '.devices | length')"
    echo "Total Packets: $(echo "$json" | jq '[.devices[].stats.packets] | add // 0')"
    echo "Total Bytes: $(echo "$json" | jq '[.devices[].stats.bytes] | add // 0')"
    echo "VPN Activity: $(if [ "$has_vpn_activity" -eq 1 ]; then echo "🚨 DETECTED"; else echo "✅ NONE"; fi)"
    echo "Concerning Content: $(if [ "$has_concerning_activity" -eq 1 ]; then echo "🚨 DETECTED"; else echo "✅ NONE"; fi)"

    if [ "$has_concerning_activity" -eq 1 ] || [ "$has_vpn_activity" -eq 1 ]; then
        echo ""
        echo "🚨 REMINDER: Check $LOG_FILE for detailed activity logs"
        echo "   All concerning activity has been logged with timestamps"
    fi

    echo ""
    echo "Press Ctrl+C to stop monitoring..."
    echo ""
}

# Display real-time device statistics with parental controls
display_realtime_stats() {
    local json="$1"
    local cycle="$2"
    local duration="$3"
    local parental_controls="$4"

    display_realtime_header "$cycle" "$duration"

    # Check for concerning activity first
    local has_concerning_activity=0
    while IFS=$'\t' read -r device websites; do
        if [ -n "$websites" ]; then
            while IFS='()' read -r domain count subdomains; do
                domain=$(echo "$domain" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                if [ -n "$domain" ]; then
                    local category_info=$(categorize_website "$domain" "$parental_controls")
                    local category=$(echo "$category_info" | cut -d':' -f1)
                    local risk_level=$(echo "$category_info" | cut -d':' -f2)

                    if should_alert "$category" "$risk_level"; then
                        has_concerning_activity=1
                        break 2
                    fi
                fi
            done <<< "$(echo "$websites" | tr ',' '\n')"
        fi
    done < <(echo "$json" | jq -r '.devices[] | "\(.device)\t\(.websites)"')

    # Show alerts if concerning activity detected
    if [ "$has_concerning_activity" -eq 1 ]; then
        echo "🚨🚨🚨 PARENTAL ALERT! 🚨🚨🚨"
        echo "══════════════════════════════════"
        echo "⚠️  CONCERNING WEBSITE ACTIVITY DETECTED!"
        echo "══════════════════════════════════"
        echo ""
    fi

    echo "📊 CURRENT WEB ACTIVITY"
    echo "═══════════════════════════════"

    # Display concerning sites first
    echo "$json" | jq -r '.devices[] | "\(.device)\t\(.ip)\t\(.websites)"' | while IFS=$'\t' read -r device ip websites; do
        if [ -n "$websites" ]; then
            echo "$websites" | tr ',' '\n' | while IFS='()' read -r domain count subdomains; do
                domain=$(echo "$domain" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                if [ -n "$domain" ]; then
                    local category_info=$(categorize_website "$domain" "$parental_controls")
                    local category=$(echo "$category_info" | cut -d':' -f1)
                    local risk_level=$(echo "$category_info" | cut -d':' -f2)

                    if should_alert "$category" "$risk_level"; then
                        local alert_icon="🚨"
                        local alert_color="🔴"

                        # Log the concerning activity
                        log_concerning_activity "$device" "$ip" "$domain" "$category" "$risk_level"

                        printf "%s %s %-20s │ 🌐 %s │ ⚠️  %s (%s)\n" \
                            "$alert_icon" "$alert_color" "$device" "$domain" "$category" "$risk_level"
                    fi
                fi
            done
        fi
    done || true

    echo ""
    echo "✅ SAFE WEB ACTIVITY"
    echo "═══════════════════════════════"

    # Display safe sites
    echo "$json" | jq -r '.devices[] | "\(.device)\t\(.ip)\t\(.websites)"' | while IFS=$'\t' read -r device ip websites; do
        if [ -n "$websites" ]; then
            echo "$websites" | tr ',' '\n' | while IFS='()' read -r domain count subdomains; do
                domain=$(echo "$domain" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                if [ -n "$domain" ]; then
                    local category_info=$(categorize_website "$domain" "$parental_controls")
                    local category=$(echo "$category_info" | cut -d':' -f1)
                    local risk_level=$(echo "$category_info" | cut -d':' -f2)

                    if ! should_alert "$category" "$risk_level"; then
                        local safe_icon="✅"
                        local category_icon=""

                        case "$category" in
                            educational) category_icon="📚" ;;
                            gaming) category_icon="🎮" ;;
                            social_media) category_icon="📱" ;;
                            video_streaming) category_icon="🎬" ;;
                            shopping) category_icon="🛒" ;;
                            news) category_icon="📰" ;;
                            search_engine) category_icon="🔍" ;;
                            file_sharing) category_icon="📁" ;;
                            *) category_icon="🌐" ;;
                        esac

                        printf "%s %s %-20s │ %s %s │ %s\n" \
                            "$safe_icon" "$category_icon" "$device" "$domain" "$category"
                    fi
                fi
            done
        fi
    done || true

    echo ""
    echo "📈 ACTIVITY SUMMARY"
    echo "═══════════════════════════════"

    # Show device statistics
    echo "$json" | jq -r '.devices[] | "\(.device)\t\(.stats.total_requests)\t\(.stats.packets)\t\(.stats.bytes)"' | while IFS=$'\t' read -r device requests packets bytes; do
        local activity_level="🟢"
        if [ "$packets" -gt 1000 ]; then
            activity_level="🟡"
        fi
        if [ "$packets" -gt 5000 ]; then
            activity_level="🔴"
        fi

        printf "%s %-20s │ 📊 %4s req │ 📦 %6s pkts │ 💾 %8s bytes\n" \
            "$activity_level" "$device" "$requests" "$packets" "$bytes"
    done || true

    if [ "$has_concerning_activity" -eq 1 ]; then
        echo ""
        echo "🚨 REMINDER: Concerning activity has been logged to $LOG_FILE"
        echo "   Check the log file for detailed information about blocked sites."
    fi

    echo ""
    echo "Press Ctrl+C to stop monitoring..."
    echo ""
}

# Get local IPs and MACs to exclude (cross-platform without -P)
get_local_addrs() {
    local os=$(uname -s)
    local local_ips=""
    local local_macs=""
    case "$os" in
        Linux)
            local_ips=$(ip -4 addr show | awk '/inet / {print $2}' | cut -d/ -f1 | tr '\n' ' ')
            local_macs=$(ip link show | awk '/ether/ {print $2}' | tr '\n' ' ')
            ;;
        Darwin)
            local_ips=$(ifconfig | awk '/inet / {print $2}' | tr '\n' ' ')
            local_macs=$(ifconfig | awk '/ether/ {print $2}' | tr '\n' ' ')
            ;;
    esac
    echo "$local_ips"
    echo "$local_macs"
}

# Test if capture is possible on an interface (1-second test capture)
test_interface_capture() {
    local capture_tool="$1"
    local intf="$2"
    local test_pcap="/tmp/test_capture_$(date +%s).pcap"
    local err_log="/tmp/capture_test_err_$(date +%s).log"
    log_verbose "Testing capture on interface: $intf"

    # Check if tool is tshark or tcpdump
    if echo "$capture_tool" | grep -q "tshark"; then
        "$capture_tool" -i "$intf" -a duration:$TEST_DURATION -w "$test_pcap" -f "tcp" 2>"$err_log"
    else
        # tcpdump syntax
        "$capture_tool" -i "$intf" -w "$test_pcap" -G $TEST_DURATION -W 1 tcp 2>"$err_log"
    fi

    local exit_code=$?
    if [ $exit_code -eq 0 ] && [ -f "$test_pcap" ]; then
        rm -f "$test_pcap" "$err_log"
        log_verbose "Test capture successful on $intf"
        return 0
    else
        local err_msg=$(cat "$err_log" 2>/dev/null)
        log_verbose "Test capture failed on $intf: $err_msg (exit: $exit_code)"
        rm -f "$test_pcap" "$err_log"
        return 1
    fi
}

# Get valid capturable interfaces
get_valid_interfaces() {
    local capture_tool="$1"
    local interfaces="$2"
    local valid=""
    for intf in $interfaces; do
        if test_interface_capture "$capture_tool" "$intf"; then
            valid="$valid $intf"
        else
            log_verbose "Skipping invalid interface: $intf"
        fi
    done
    valid="${valid#" "}"  # Trim leading space
    log_verbose "Valid interfaces: $valid"
    echo "$valid"
}

# Get default interface from routes
get_default_interface() {
    log_verbose "Getting default interface"
    local os=$(uname -s)
    local default_iface=""
    case "$os" in
        Linux)
            default_iface=$(ip route show default 2>/dev/null | awk '/default/ {print $5; exit}')
            ;;
        Darwin)
            default_iface=$(netstat -rn 2>/dev/null | grep '^default' | awk '{print $6; exit}')
            ;;
    esac
    log_verbose "Default interface: $default_iface"
    echo "$default_iface"
}

# Display routing table
display_routes() {
    log_verbose "Displaying routes"
    echo "Parsing available routes for network detection:"
    local os=$(uname -s)
    local routes
    case "$os" in
        Linux)
            routes=$(ip route show 2>/dev/null)
            ;;
        Darwin)
            routes=$(netstat -rn 2>/dev/null)
            ;;
        *)
            routes="Route parsing not supported on this OS."
            ;;
    esac
    echo "$routes"
    log_verbose "Routes: $routes"
    echo ""
}

# Select single interface via menu (using readable names)
select_interface() {
    local valid_interfaces="$1"
    local os="$2"
    local default_iface="$3"
    log_verbose "Selecting interface"
    echo "Available active interfaces (default route: ${default_iface:-none}):"
    local options=()
    for intf in $valid_interfaces; do
        local desc=$(get_interface_description "$intf" "$os")
        options+=("$desc ($intf)")
    done
    select option in "${options[@]}"; do
        if [ -n "$option" ]; then
            local selected_intf="${option##* (}"
            selected_intf="${selected_intf%)}"
            if [ -n "$selected_intf" ]; then
                log_verbose "Selected interface: $selected_intf"
                echo "$selected_intf"
                return 0
            else
                echo "Invalid parsing of selection." >&2
                log_verbose "Invalid parsing"
            fi
        else
            echo "Invalid selection. Please choose a number." >&2
            log_verbose "Invalid selection"
        fi
    done
}

# Prepare capture options using valid interfaces
prepare_capture_opts() {
    local os="$1"
    local valid_interfaces="$2"
    local select_mode="$3"
    local capture_tool="$4"
    log_verbose "Preparing capture options"
    local capture_opts=""
    if [ "$select_mode" -eq 1 ]; then
        local default_iface=$(get_default_interface)
        local selected=$(select_interface "$valid_interfaces" "$os" "$default_iface")
        capture_opts="-i $selected"
    else
        if [ "$os" = "Linux" ] && echo "$capture_tool" | grep -q "tshark" && "$capture_tool" -D 2>/dev/null | grep -q '^any '; then
            capture_opts="-i any"
        else
            for intf in $valid_interfaces; do
                capture_opts="$capture_opts -i $intf"
            done
        fi
    fi
    if [ -z "$capture_opts" ]; then
        log_verbose "Error: No valid interfaces available"
        echo "Error: No valid interfaces available for capture." >&2
        handle_capture_error
        exit 1
    fi
    log_verbose "Capture options: $capture_opts"
    echo "$capture_opts"
}

# Build exclude local filter
build_exclude_local_filter() {
    local local_ips="$1"
    local local_macs="$2"
    local exclude_filter=""
    for ip in $local_ips; do
        if [ -n "$exclude_filter" ]; then exclude_filter="$exclude_filter or "; fi
        exclude_filter="${exclude_filter}ip.src == $ip"
    done
    for mac in $local_macs; do
        if [ -n "$exclude_filter" ]; then exclude_filter="$exclude_filter or "; fi
        exclude_filter="${exclude_filter}eth.src == $mac"
    done
    if [ -n "$exclude_filter" ]; then
        exclude_filter="not ($exclude_filter)"
    fi
    echo "$exclude_filter"
}

# Capture traffic using packet capture tool
capture_traffic() {
    local capture_tool="$1"
    local capture_opts="$2"
    local duration="$3"
    local pcap_file="$4"
    local capture_filter="$5"
    log_verbose "Starting capture with tool: $capture_tool, opts: $capture_opts, duration: $duration, file: $pcap_file, filter: $capture_filter"
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    local time_msg=""
    if [ $minutes -gt 0 ]; then
        time_msg="${minutes} minute(s)"
    fi
    if [ $seconds -gt 0 ]; then
        if [ -n "$time_msg" ]; then time_msg="$time_msg and "; fi
        time_msg="${time_msg}${seconds} second(s)"
    fi
    if [ -z "$time_msg" ]; then time_msg="0 seconds"; fi
    echo "Capturing traffic for $time_msg..."
    local err_log="/tmp/capture_err_$(date +%s).log"

    # Check if tool is tshark or tcpdump
    if echo "$capture_tool" | grep -q "tshark"; then
        "$capture_tool" $capture_opts -a duration:"$duration" -w "$pcap_file" ${capture_filter:+-f "$capture_filter"} 2>"$err_log"
    else
        # tcpdump syntax - capture for specific duration
        local tcpdump_filter="tcp"
        if [ -n "$capture_filter" ]; then
            tcpdump_filter="$capture_filter"
        fi
        "$capture_tool" $capture_opts -w "$pcap_file" -G $duration -W 1 "$tcpdump_filter" 2>"$err_log"
    fi

    local exit_code=$?
    log_verbose "Capture exit code: $exit_code"
    if [ $exit_code -ne 0 ] || [ ! -f "$pcap_file" ]; then
        local err_msg=$(cat "$err_log" 2>/dev/null)
        log_verbose "Capture error: $err_msg"
        echo "Error: Capture failed or no file created." >&2
        echo "$err_msg" >&2
        rm -f "$err_log"
        handle_capture_error
        exit 1
    fi
    rm -f "$err_log"
    log_verbose "Capture successful"
}

# Handle capture errors with OS-specific advice
handle_capture_error() {
    log_verbose "Handling capture error"
    local os=$(uname -s)
    echo "Possible reasons and fixes:" >&2
    echo "- Ensure running with sudo." >&2
    echo "- Check interface availability and permissions." >&2
    echo "- For Wi-Fi monitoring, enable monitor mode (e.g., airmon-ng on Linux)." >&2
    if [ "$os" = "Darwin" ]; then
        echo "- On macOS, ensure Wireshark has capture permissions:" >&2
        echo "  - Install ChmodBPF from Wireshark installer." >&2
        echo "  - Or run: sudo chown $USER:admin /dev/bpf*" >&2
        echo "  - May need to add user to 'access_bpf' group: sudo dseditgroup -o edit -a $USER -t user access_bpf" >&2
    fi
    echo "- Verify tshark installation and version." >&2
    echo "- No traffic during capture." >&2
}

# Analyze captured data with comprehensive fields for all traffic types
analyze_capture() {
    local capture_tool="$1"
    local pcap_file="$2"
    local display_filter="$3"
    log_verbose "Analyzing capture file: $pcap_file with display filter: $display_filter"

    # Check if tool is tshark or tcpdump
    if echo "$capture_tool" | grep -q "tshark"; then
        # Use tshark for analysis - capture all network traffic including VPN and encrypted traffic
        "$capture_tool" -N mn -r "$pcap_file" \
            -Y "$display_filter" \
            -T fields \
            -e frame.time_epoch \
            -e frame.len \
            -e frame.protocols \
            -e ip.src_host \
            -e ip.dst_host \
            -e tcp.srcport \
            -e tcp.dstport \
            -e udp.srcport \
            -e udp.dstport \
            -e http.host \
            -e http.request.method \
            -e http.response.code \
            -e http.user_agent \
            -e tls.handshake.extensions_server_name \
            -e tls.handshake.cipher_suite \
            -e tls.handshake.version \
            -e dns.qry.name \
            -e dns.qry.type \
            -e dns.resp.name \
            -e dns.resp.addr \
            -e eth.src_resolved \
            -e eth.dst_resolved \
            -e ip.ttl \
            -e tcp.flags \
            -e tcp.connection.syn \
            -e tcp.connection.fin \
            -e tcp.connection.rst \
            -e ip.id \
            -e ip.checksum \
            -e tcp.seq \
            -e tcp.ack \
            -e tcp.window_size \
            -e tcp.urgent_pointer \
            -e udp.length \
            -e udp.checksum \
            -e icmp.type \
            -e icmp.code \
            -e arp.opcode \
            -e arp.src.hw_mac \
            -e arp.src.proto_ipv4 \
            -e arp.dst.hw_mac \
            -e arp.dst.proto_ipv4 \
            -e ipv6.src \
            -e ipv6.dst \
            -e sctp.srcport \
            -e sctp.dstport \
            -e quic.long.packet_type \
            -e http2.header.name \
            -e http2.header.value \
            -E separator=$'\t' \
            -E quote=n 2>/dev/null | tr -d '\000\012\015'
    else
        # Use tcpdump for analysis - convert tshark-style filter to tcpdump-style
        local tcpdump_filter="$display_filter"
        # Basic conversion for common filters
        tcpdump_filter=$(echo "$tcpdump_filter" | sed 's/http and/http \&\&/g; s/dns and/dns \&\&/g; s/tcp and/tcp \&\&/g; s/tls and/tls \&\&/g')

        # Use tcpdump to read the pcap file with appropriate filters
        "$capture_tool" -r "$pcap_file" -l "$tcpdump_filter" 2>/dev/null | tr -d '\000\012\015'
    fi
}

# Test encoding/decoding of data
test_encoding() {
    local data="$1"
    log_verbose "Testing encoding/decoding"
    local encoded=$(printf '%s' "$data" | base64)
    log_verbose "Encoded data: $encoded"
    local decoded=$(echo "$encoded" | base64 -d)
    if [ "$data" != "$decoded" ]; then
        log_verbose "Encoding test failed"
        echo "Error: Encoding/decoding test failed." >&2
        exit 1
    fi
    log_verbose "Encoding test successful"
}

# Process data to get top N domains with frequency, grouped by domain, and include subrequests underneath (list subdomains)
process_data() {
    local data="$1"
    local num_sites="$2"
    log_verbose "Processing data"
    echo "$data" | awk -F $'\t' -v ignore_list="$(IFS=','; echo "${IGNORED_DOMAINS[*]}")" '
    BEGIN { split(ignore_list, ignores, ",") }
    {
        host = ($10 != "" ? $10 : $14);
        if (host != "") {
            ignore = 0;
            for (i in ignores) {
                if (host ~ ignores[i]) { ignore = 1; break; }
            }
            if (ignore == 0) {
                domain = host; sub(/^www\./, "", domain)
                main_domain = domain; gsub(/.*\./, "", main_domain)
                sub_domain = host; sub(main_domain "$", "", sub_domain)
                freq[domain]++;
                if (sub_domain != "") {
                    subs[domain] = subs[domain] sub_domain " "
                }
            }
        }
    }
    END {
        for (d in freq) {
            print freq[d] "\t" d "\t" subs[d];
        }
    }' | sort -r -n -k1 | head -n "$num_sites"
}

# Export to files and open HTML in browser
export_data() {
    local json="$1"
    local cycle_time=$(date +%Y%m%d_%H%M%S)
    local json_file="$STORAGE_DIR/cycle_${cycle_time}.json"
    local csv_file="$STORAGE_DIR/cycle_${cycle_time}.csv"
    local html_file="$STORAGE_DIR/cycle_${cycle_time}.html"

    echo "$json" > "$json_file"
    log_verbose "Exported JSON to $json_file"

    # Pretty print JSON if jq available
    if command -v jq &> /dev/null; then
        jq . "$json_file" || log_verbose "jq pretty print failed"
    else
        echo "$json"
    fi

    # Export to CSV
    echo "Device,IP Address,Vendor,Total Requests,Unique Domains,Packets,Bytes,Protocols,Ports,Top Domains (Count Domain Subrequests)" > "$csv_file"
    echo "$json" | jq -r '.devices[] | "\(.device),\(.ip),\(.vendor),\(.stats.total_requests),\(.stats.unique_domains),\(.stats.packets),\(.stats.bytes),\(.protocols),\(.ports),\(.websites | join(", "))"' >> "$csv_file"
    log_verbose "Exported CSV to $csv_file"

    # Generate HTML with JavaScript filter for timelines, domains, and decrypted requests
    cat <<HTML > "$html_file"
<!DOCTYPE html>
<html>
<head>
<title>Top Domains - $cycle_time</title>
<style>
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid black; padding: 8px; text-align: left; }
th { background-color: #f2f2f2; }
#filter { margin-bottom: 10px; }
</style>
</head>
<body>
<h1>Top Domains Accessed - $cycle_time</h1>
<input type="text" id="filter" onkeyup="filterTable()" placeholder="Search for domains or timelines..">
<table id="dataTable">
<tr><th>Device</th><th>IP Address</th><th>Vendor</th><th>Total Requests</th><th>Unique Domains</th><th>Packets</th><th>Bytes</th><th>Protocols</th><th>Ports</th><th>Top Domains (Count Domain Subrequests)</th></tr>
$(echo "$json" | jq -r '.devices[] | "<tr><td>\(.device)</td><td>\(.ip)</td><td>\(.vendor)</td><td>\(.stats.total_requests)</td><td>\(.stats.unique_domains)</td><td>\(.stats.packets)</td><td>\(.stats.bytes)</td><td>\(.protocols)</td><td>\(.ports)</td><td>\(.websites | join("<br>"))</td></tr>"')
</table>
<script>
function filterTable() {
  var input = document.getElementById("filter").value.toUpperCase();
  var table = document.getElementById("dataTable");
  var tr = table.getElementsByTagName("tr");
  for (var i = 1; i < tr.length; i++) {
    var td = tr[i].getElementsByTagName("td");
    var found = false;
    for (var j = 0; j < td.length; j++) {
      if (td[j].innerHTML.toUpperCase().indexOf(input) > -1) {
        found = true;
        break;
      }
    }
    tr[i].style.display = found ? "" : "none";
  }
}
</script>
</body>
</html>
HTML
    log_verbose "Exported HTML to $html_file"

    # Open in default browser
    if command -v xdg-open &> /dev/null; then
        xdg-open "$html_file" &
    elif command -v open &> /dev/null; then
        open "$html_file" &
    else
        log_verbose "No browser opener found; open $html_file manually"
    fi
}

# Main execution
main() {
    log_verbose "Script started with args: $*"
    display_logo

    # Parse arguments
    local select_mode=0
    local num_sites=$DEFAULT_NUM_SITES
    local duration=$DEFAULT_CAPTURE_DURATION
    local include_local=0
    local ports=""
    local loop=1
    local parse_logs=0
    local view_flag=0
    local simple_dashboard=0
    while [[ $# -gt 0 ]]; do
        case $1 in
            --select) select_mode=1; shift ;;
            --num) num_sites="$2"; shift 2 ;;
            --duration) duration="$2"; shift 2 ;;
            --include-local) include_local=1; shift ;;
            --log-path) LOG_FILE="$2"; shift 2 ;;
            --ports) ports="$2"; shift 2 ;;
            --no-loop) loop=0; shift ;;
            --parse-logs) parse_logs=1; shift ;;
            --view) view_flag=1; shift ;;
            --dashboard) simple_dashboard=1; shift ;;
            *) echo "Unknown option: $1" >&2; echo "Usage: sudo $0 [--select] [--num N] [--duration S] [--include-local] [--log-path PATH] [--ports PORT1,PORT2,...] [--no-loop] [--parse-logs] [--view] [--dashboard]" >&2; exit 1 ;;
        esac
    done
    log_verbose "Parsed args: select_mode=$select_mode, num_sites=$num_sites, duration=$duration, include_local=$include_local, log_file=$LOG_FILE, ports=$ports, loop=$loop, parse_logs=$parse_logs, view_flag=$view_flag"

    if [ $parse_logs -eq 1 ]; then
        parse_logs "$STORAGE_DIR"
        exit 0
    fi

    local capture_tool=$(locate_capture_tool)
    local os=$(uname -s)
    display_routes
    local active_interfaces=$(get_active_interfaces)
    if [ -z "$active_interfaces" ]; then
        log_verbose "Error: No active interfaces"
        echo "Error: No active network interfaces found." >&2
        echo "Please ensure you have network interfaces available." >&2
        exit 1
    fi

    # Log descriptions
    for intf in $active_interfaces; do
        local desc=$(get_interface_description "$intf" "$os")
        log_verbose "Interface $intf description: $desc"
    done

    local valid_interfaces=$(get_valid_interfaces "$capture_tool" "$active_interfaces")
    if [ -z "$valid_interfaces" ]; then
        log_verbose "Error: No valid capturable interfaces"
        echo "Error: No interfaces available for capture after testing." >&2
        handle_capture_error
        exit 1
    fi
    local capture_opts=$(prepare_capture_opts "$os" "$valid_interfaces" "$select_mode" "$capture_tool")

    # Build capture filter for ports
    local capture_filter=""
    if [ -n "$ports" ]; then
        capture_filter="tcp dst port $(echo "$ports" | sed 's/,/ or tcp dst port /g')"
    fi

    # Get local addrs if excluding
    local display_filter="(http.request and !(http contains \"X-Requested-With: XMLHttpRequest\")) or (tls.handshake.type == 1)"
    if [ $include_local -eq 0 ]; then
        local local_addrs=$(get_local_addrs)
        local local_ips=$(echo "$local_addrs" | head -1)
        local local_macs=$(echo "$local_addrs" | tail -1)
        local temp_exclude=$(build_exclude_local_filter "$local_ips" "$local_macs")
        if [ -n "$temp_exclude" ]; then
            display_filter="$display_filter and $temp_exclude"
        fi
    fi

    # Spider devices on network using arp
    local network_devices=$(arp -a 2>/dev/null | awk '{
        ip = $2; gsub(/[()]/, "", ip);
        mac = $4;
        if (ip != "" && mac != "") print ip " " mac
    }' | sort -u)
    log_verbose "Network devices discovered: $network_devices"

    # Load custom device names
    local custom_names_str=$(load_custom_names)

    # Load parental controls
    local parental_controls=$(load_parental_controls)

    local cycle=0
    while true; do
        cycle=$((cycle + 1))
        local pcap_file="/tmp/capture_$(date +%s).pcap"
        log_verbose "PCAP file: $pcap_file"

        capture_traffic "$capture_tool" "$capture_opts" "$duration" "$pcap_file" "$capture_filter"

        local data=$(analyze_capture "$capture_tool" "$pcap_file" "$display_filter")
        log_verbose "Raw data: $data"
        rm -f "$pcap_file"
        log_verbose "PCAP file cleaned up"

        if [ -z "$data" ]; then
            log_verbose "No data found"
            if [ $view_flag -eq 0 ]; then
                display_realtime_header "$cycle" "$duration"
                echo "No network activity detected in the last $duration seconds."
                echo ""
                echo "Press Ctrl+C to stop monitoring..."
                echo ""
            fi
        else
            test_encoding "$data"

            # Get unique sources from data
            local unique_sources=$(echo "$data" | awk -F $'\t' '{print $4 " " $5}' | sort -u)
            local escaped_network_devices=$(printf '%s' "$network_devices" | jq -Rs .)
            local json='{"network_devices": '"$escaped_network_devices"', "cycle": '"$cycle"', "timestamp": "'$(date -u '+%Y-%m-%dT%H:%M:%SZ')'", "devices": ['
            local first=1
            while IFS=' ' read -r source_ip source_vendor; do
                if [ $first -eq 0 ]; then json="$json,"; fi
                first=0
                local friendly_name=$(get_friendly_name "$source_ip" "$source_vendor" "$custom_names_str")
                local subdata=$(echo "$data" | awk -F $'\t' -v ip="$source_ip" '$4 == ip {print}')
                local total_requests=$(echo "$subdata" | wc -l | tr -d ' ')
                local unique_domains=$(echo "$subdata" | awk -F $'\t' '{host=($10!=""?$10:$14); if(host!="") print host}' | sort -u | wc -l | tr -d ' ')
                local top_domains=$(process_data "$subdata" "$num_sites")

                # Enhanced analysis for real-time data
                local device_stats=$(analyze_device_data "$subdata" "$num_sites")
                local escaped_ip=$(echo "$source_ip" | sed 's/\./\\./g')
                local device_info=$(echo "$device_stats" | grep "^$escaped_ip" | head -1 || true)

                if [ -n "$device_info" ]; then
                    local packets=$(echo "$device_info" | cut -f2)
                    local bytes=$(echo "$device_info" | cut -f3)
                    local unique_ports=$(echo "$device_info" | cut -f6)
                    local protocols=$(echo "$device_info" | cut -f7)
                else
                    local packets="$total_requests"
                    local bytes="0"
                    local unique_ports="N/A"
                    local protocols="N/A"
                fi

                # Comprehensive traffic analysis
                analyze_all_traffic "$subdata" "$friendly_name" "$source_ip"

                # Process domains for categorization and alerts
                local categorized_domains=""
                local concerning_domains=""

                while IFS=$'\t' read -r count domain subdomains; do
                    if [ -n "$domain" ]; then
                        local category_info=$(categorize_website "$domain" "$parental_controls")
                        local category=$(echo "$category_info" | cut -d':' -f1)
                        local risk_level=$(echo "$category_info" | cut -d':' -f2)

                        if should_alert "$category" "$risk_level"; then
                            concerning_domains="${concerning_domains}${domain} (${count}, ${category})"
                            # Log concerning activity immediately
                            log_concerning_activity "$friendly_name" "$source_ip" "$domain" "$category" "$risk_level"
                        else
                            categorized_domains="${categorized_domains}${domain} (${count}, ${category})"
                        fi
                    fi
                done <<< "$top_domains"

                # Remove trailing commas
                categorized_domains="${categorized_domains%,}"
                concerning_domains="${concerning_domains%,}"

                local websites_json
                if [ -n "$concerning_domains" ]; then
                    # Put concerning domains first in JSON
                    websites_json="[\"🚨 CONCERNING: ${concerning_domains}\", \"✅ SAFE: ${categorized_domains}\"]"
                else
                    websites_json=$(echo "$top_domains" | awk 'BEGIN { printf "[\"✅ SAFE: "; sep = "" } { printf "%s%s (%s, categorized)", sep, $2, $1; sep = " " } END { print "\"]" }')
                fi

                # Ensure numeric values for JSON
                total_requests=${total_requests:-0}
                unique_domains=${unique_domains:-0}
                packets=${packets:-0}
                bytes=${bytes:-0}
                # Validate numeric values
                [[ "$total_requests" =~ ^[0-9]+$ ]] || total_requests=0
                [[ "$unique_domains" =~ ^[0-9]+$ ]] || unique_domains=0
                [[ "$packets" =~ ^[0-9]+$ ]] || packets=0
                [[ "$bytes" =~ ^[0-9]+$ ]] || bytes=0

                local device_json
                printf -v device_json '{"device": "%s", "ip": "%s", "vendor": "%s", "stats": {"total_requests": %d, "unique_domains": %d, "packets": %d, "bytes": %d}, "protocols": "%s", "ports": "%s", "websites": %s}' "$friendly_name" "$source_ip" "$source_vendor" "$total_requests" "$unique_domains" "$packets" "$bytes" "$protocols" "$unique_ports" "$websites_json"
                json+="$device_json"
                # Log timestamped entry for this device
                log_verbose "Device $friendly_name ($source_ip): total_requests=$total_requests, unique_domains=$unique_domains, packets=$packets, bytes=$bytes, concerning_sites=$concerning_domains"
            done <<< "$unique_sources"
            json="$json]"

            if [ $view_flag -eq 1 ]; then
                export_data "$json"
            elif [ $simple_dashboard -eq 1 ]; then
                display_simple_dashboard "$json" "$cycle" "$duration" "$parental_controls"
            else
                display_realtime_stats "$json" "$cycle" "$duration" "$parental_controls"
            fi
        fi

        if [ $loop -eq 0 ]; then
            break
        fi
        sleep "$duration"
    done
    log_verbose "Script completed"
}

main "$@"

