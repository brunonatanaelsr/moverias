#!/bin/bash
# System monitoring script for Move Marias

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="movemarias"
LOG_DIR="/var/log/movemarias"
HEALTH_URL="http://localhost:8000/health/"
METRICS_URL="http://localhost:8000/metrics/"

# Thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=80
DISK_THRESHOLD=85
RESPONSE_TIME_THRESHOLD=2.0

echo "=== Move Marias System Monitor ==="
echo "Timestamp: $(date)"
echo

# Function to check service status
check_service() {
    local service=$1
    if systemctl is-active --quiet $service; then
        echo -e "${GREEN}✓${NC} $service is running"
        return 0
    else
        echo -e "${RED}✗${NC} $service is not running"
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    local path=$1
    local usage=$(df $path | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ $usage -lt $DISK_THRESHOLD ]; then
        echo -e "${GREEN}✓${NC} Disk usage: ${usage}% (${path})"
    else
        echo -e "${RED}✗${NC} Disk usage: ${usage}% (${path}) - Above threshold!"
    fi
}

# Function to check memory usage
check_memory() {
    local memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    
    if [ $memory_usage -lt $MEMORY_THRESHOLD ]; then
        echo -e "${GREEN}✓${NC} Memory usage: ${memory_usage}%"
    else
        echo -e "${RED}✗${NC} Memory usage: ${memory_usage}% - Above threshold!"
    fi
}

# Function to check CPU usage
check_cpu() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    cpu_usage=$(printf "%.0f" $cpu_usage)
    
    if [ $cpu_usage -lt $CPU_THRESHOLD ]; then
        echo -e "${GREEN}✓${NC} CPU usage: ${cpu_usage}%"
    else
        echo -e "${RED}✗${NC} CPU usage: ${cpu_usage}% - Above threshold!"
    fi
}

# Function to check application health
check_app_health() {
    local start_time=$(date +%s.%3N)
    local response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL 2>/dev/null)
    local end_time=$(date +%s.%3N)
    local response_time=$(echo "$end_time - $start_time" | bc)
    
    if [ "$response" = "200" ]; then
        if (( $(echo "$response_time < $RESPONSE_TIME_THRESHOLD" | bc -l) )); then
            echo -e "${GREEN}✓${NC} Application health: OK (${response_time}s)"
        else
            echo -e "${YELLOW}⚠${NC} Application health: OK but slow (${response_time}s)"
        fi
    else
        echo -e "${RED}✗${NC} Application health: Failed (HTTP $response)"
    fi
}

# Function to check database connectivity
check_database() {
    if sudo -u postgres psql -c "SELECT 1;" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Database connectivity: OK"
    else
        echo -e "${RED}✗${NC} Database connectivity: Failed"
    fi
}

# Function to check Redis
check_redis() {
    if redis-cli ping >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Redis connectivity: OK"
    else
        echo -e "${RED}✗${NC} Redis connectivity: Failed"
    fi
}

# Function to check log files
check_logs() {
    echo "=== Recent Error Logs ==="
    if [ -f "$LOG_DIR/error.log" ]; then
        local error_count=$(tail -100 "$LOG_DIR/error.log" | grep -c "ERROR")
        if [ $error_count -gt 0 ]; then
            echo -e "${YELLOW}⚠${NC} Found $error_count errors in last 100 lines"
            echo "Recent errors:"
            tail -10 "$LOG_DIR/error.log" | grep "ERROR" | tail -3
        else
            echo -e "${GREEN}✓${NC} No recent errors found"
        fi
    else
        echo -e "${YELLOW}⚠${NC} Error log file not found"
    fi
}

# Function to check SSL certificate (if applicable)
check_ssl() {
    local domain="movemarias.org"  # Change to your domain
    local cert_info=$(echo | openssl s_client -servername $domain -connect $domain:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        local expiry=$(echo "$cert_info" | grep "notAfter" | cut -d= -f2)
        local expiry_date=$(date -d "$expiry" +%s)
        local current_date=$(date +%s)
        local days_left=$(( (expiry_date - current_date) / 86400 ))
        
        if [ $days_left -gt 30 ]; then
            echo -e "${GREEN}✓${NC} SSL Certificate: Valid ($days_left days remaining)"
        elif [ $days_left -gt 7 ]; then
            echo -e "${YELLOW}⚠${NC} SSL Certificate: Expires soon ($days_left days remaining)"
        else
            echo -e "${RED}✗${NC} SSL Certificate: Expires very soon ($days_left days remaining)"
        fi
    else
        echo -e "${YELLOW}⚠${NC} SSL Certificate: Cannot verify"
    fi
}

# Main monitoring checks
echo "=== Service Status ==="
check_service "movemarias"
check_service "nginx"
check_service "postgresql"
check_service "redis"

echo
echo "=== System Resources ==="
check_cpu
check_memory
check_disk_space "/"
check_disk_space "/var"

echo
echo "=== Application Status ==="
check_app_health
check_database
check_redis

echo
check_logs

echo
echo "=== Security ==="
check_ssl

echo
echo "=== Quick Stats ==="
echo "Active connections: $(ss -tuln | wc -l)"
echo "Running processes: $(ps aux | wc -l)"
echo "Load average: $(uptime | awk -F'load average:' '{print $2}')"

# Generate summary
echo
echo "=== Summary ==="
echo "Monitor completed at $(date)"
echo "For detailed metrics, visit: $METRICS_URL"
