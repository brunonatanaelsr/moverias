#!/bin/bash
# Move Marias - Service Manager Script
# Centralized service management for production environment

set -e

# Configuration
PROJECT_NAME="movemarias"
PROJECT_DIR="/var/www/movemarias"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="movemarias"
NGINX_SERVICE="nginx"
REDIS_SERVICE="redis-server"
LOG_DIR="/var/log/movemarias"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Check if service exists
service_exists() {
    systemctl list-unit-files | grep -q "^$1.service"
}

# Get service status
get_service_status() {
    if service_exists "$1"; then
        systemctl is-active "$1" 2>/dev/null || echo "inactive"
    else
        echo "not-found"
    fi
}

# Display service status
show_status() {
    echo -e "\n${BLUE}=== Move Marias Service Status ===${NC}"
    
    # Django Application
    django_status=$(get_service_status "$SERVICE_NAME")
    case $django_status in
        "active")
            echo -e "🐍 Django App: ${GREEN}Running${NC}"
            ;;
        "inactive"|"failed")
            echo -e "🐍 Django App: ${RED}Stopped${NC}"
            ;;
        *)
            echo -e "🐍 Django App: ${YELLOW}Unknown${NC}"
            ;;
    esac
    
    # Nginx
    nginx_status=$(get_service_status "$NGINX_SERVICE")
    case $nginx_status in
        "active")
            echo -e "🌐 Nginx: ${GREEN}Running${NC}"
            ;;
        "inactive"|"failed")
            echo -e "🌐 Nginx: ${RED}Stopped${NC}"
            ;;
        *)
            echo -e "🌐 Nginx: ${YELLOW}Unknown${NC}"
            ;;
    esac
    
    # Redis
    redis_status=$(get_service_status "$REDIS_SERVICE")
    case $redis_status in
        "active")
            echo -e "📦 Redis: ${GREEN}Running${NC}"
            ;;
        "inactive"|"failed")
            echo -e "📦 Redis: ${RED}Stopped${NC}"
            ;;
        *)
            echo -e "📦 Redis: ${YELLOW}Unknown${NC}"
            ;;
    esac
    
    # System Resources
    echo -e "\n${BLUE}=== System Resources ===${NC}"
    if command -v free >/dev/null 2>&1; then
        memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
        echo -e "💾 Memory Usage: ${memory_usage}%"
    fi
    
    if command -v df >/dev/null 2>&1; then
        disk_usage=$(df / | awk 'NR==2 {print $5}')
        echo -e "💽 Disk Usage: ${disk_usage}"
    fi
    
    echo -e "⚡ Load Average: $(uptime | awk -F'load average:' '{print $2}')"
    
    # Application Health
    echo -e "\n${BLUE}=== Application Health ===${NC}"
    if curl -f -s http://localhost:8000/health/ >/dev/null 2>&1; then
        echo -e "🏥 Health Check: ${GREEN}Healthy${NC}"
    else
        echo -e "🏥 Health Check: ${RED}Unhealthy${NC}"
    fi
}

# Start services
start_services() {
    log "🚀 Starting Move Marias services..."
    
    # Start Redis first
    if service_exists "$REDIS_SERVICE"; then
        log "Starting Redis..."
        sudo systemctl start "$REDIS_SERVICE"
        sleep 2
    fi
    
    # Start Django application
    if service_exists "$SERVICE_NAME"; then
        log "Starting Django application..."
        sudo systemctl start "$SERVICE_NAME"
        sleep 5
    else
        error "Django service not found. Please install the service first."
        return 1
    fi
    
    # Start Nginx
    if service_exists "$NGINX_SERVICE"; then
        log "Starting Nginx..."
        sudo systemctl start "$NGINX_SERVICE"
    fi
    
    # Verify services are running
    sleep 3
    show_status
}

# Stop services
stop_services() {
    log "🛑 Stopping Move Marias services..."
    
    # Stop in reverse order
    if service_exists "$NGINX_SERVICE"; then
        log "Stopping Nginx..."
        sudo systemctl stop "$NGINX_SERVICE"
    fi
    
    if service_exists "$SERVICE_NAME"; then
        log "Stopping Django application..."
        sudo systemctl stop "$SERVICE_NAME"
    fi
    
    if service_exists "$REDIS_SERVICE"; then
        log "Stopping Redis..."
        sudo systemctl stop "$REDIS_SERVICE"
    fi
    
    show_status
}

# Restart services
restart_services() {
    log "🔄 Restarting Move Marias services..."
    stop_services
    sleep 2
    start_services
}

# Reload configuration
reload_services() {
    log "⚡ Reloading service configurations..."
    
    if service_exists "$NGINX_SERVICE"; then
        log "Reloading Nginx configuration..."
        sudo systemctl reload "$NGINX_SERVICE"
    fi
    
    if service_exists "$SERVICE_NAME"; then
        log "Restarting Django application..."
        sudo systemctl restart "$SERVICE_NAME"
    fi
    
    show_status
}

# Deploy new version
deploy() {
    log "🚀 Deploying new version..."
    
    # Stop services
    log "Stopping services for deployment..."
    sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    
    # Backup current version
    if [ -d "$PROJECT_DIR" ]; then
        log "Creating backup of current version..."
        sudo cp -r "$PROJECT_DIR" "/tmp/movemarias_backup_$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Update code (assuming git repository)
    if [ -d "$PROJECT_DIR/.git" ]; then
        log "Updating code from repository..."
        cd "$PROJECT_DIR"
        sudo git pull origin main
    fi
    
    # Install/update dependencies
    log "Installing dependencies..."
    sudo "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
    
    # Run migrations
    log "Running database migrations..."
    sudo -u www-data "$VENV_DIR/bin/python" "$PROJECT_DIR/manage.py" migrate
    
    # Collect static files
    log "Collecting static files..."
    sudo -u www-data "$VENV_DIR/bin/python" "$PROJECT_DIR/manage.py" collectstatic --noinput
    
    # Start services
    log "Starting services..."
    sudo systemctl start "$SERVICE_NAME"
    sudo systemctl start "$NGINX_SERVICE"
    
    # Verify deployment
    sleep 5
    if curl -f -s http://localhost:8000/health/ >/dev/null 2>&1; then
        log "✅ Deployment successful!"
    else
        error "❌ Deployment verification failed!"
        return 1
    fi
    
    show_status
}

# Show logs
show_logs() {
    service=${2:-$SERVICE_NAME}
    lines=${3:-50}
    
    echo -e "\n${BLUE}=== Recent logs for $service (last $lines lines) ===${NC}"
    
    if service_exists "$service"; then
        sudo journalctl -u "$service" -n "$lines" --no-pager
    else
        # Show application logs if service logs not available
        if [ -f "$LOG_DIR/django.log" ]; then
            tail -n "$lines" "$LOG_DIR/django.log"
        else
            error "No logs found for $service"
        fi
    fi
}

# Performance check
performance_check() {
    echo -e "\n${BLUE}=== Performance Check ===${NC}"
    
    # Check response time
    response_time=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8000/health/ 2>/dev/null || echo "0")
    echo -e "⏱️  Response Time: ${response_time}s"
    
    # Check active connections
    if command -v ss >/dev/null 2>&1; then
        connections=$(ss -tuln | grep :8000 | wc -l)
        echo -e "🔗 Active Connections: $connections"
    fi
    
    # Check memory usage of Django processes
    if command -v pgrep >/dev/null 2>&1; then
        django_pids=$(pgrep -f "gunicorn.*movemarias" || echo "")
        if [ -n "$django_pids" ]; then
            total_memory=$(ps -o rss= -p $django_pids | awk '{sum+=$1} END {printf "%.1f", sum/1024}')
            echo -e "🧠 Django Memory Usage: ${total_memory}MB"
        fi
    fi
}

# Main script logic
case "${1:-status}" in
    "status"|"st")
        show_status
        ;;
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart"|"re")
        restart_services
        ;;
    "reload"|"rl")
        reload_services
        ;;
    "deploy")
        deploy
        ;;
    "logs"|"log")
        show_logs "$@"
        ;;
    "performance"|"perf")
        performance_check
        ;;
    "monitor"|"mon")
        python3 "$PROJECT_DIR/deploy/system_monitor.py"
        ;;
    "backup")
        "$PROJECT_DIR/deploy/backup_system.sh"
        ;;
    "help"|"--help"|"-h")
        echo "Move Marias Service Manager"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  status, st          Show service status (default)"
        echo "  start               Start all services"
        echo "  stop                Stop all services"
        echo "  restart, re         Restart all services"
        echo "  reload, rl          Reload configurations"
        echo "  deploy              Deploy new version"
        echo "  logs, log [service] Show recent logs"
        echo "  performance, perf   Show performance metrics"
        echo "  monitor, mon        Run system monitor"
        echo "  backup              Run backup script"
        echo "  help                Show this help"
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac
