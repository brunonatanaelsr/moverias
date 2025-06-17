#!/bin/bash

# =============================================================================
# MoveMarias VPS Installation Script
# Automated installation script for Ubuntu/Debian VPS
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
PROJECT_NAME="movemarias"
PROJECT_DIR="/var/www/movemarias"
REPO_URL="https://github.com/brunonatanaelsr/02.git"
DOMAIN="move.squadsolucoes.com.br"
EMAIL="admin@movemarias.org"
DB_NAME="movemarias_prod"
DB_USER="movemarias_user"

# Log function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root. Use: sudo $0"
    fi
}

# Update system
update_system() {
    log "Updating system packages..."
    apt update && apt upgrade -y
    apt install -y software-properties-common curl wget gnupg2
}

# Install Python 3.10
install_python() {
    log "Installing Python 3.10 and dependencies..."
    apt install -y python3.10 python3.10-venv python3.10-dev python3-pip
    apt install -y build-essential libssl-dev libffi-dev libpq-dev
    
    # Ensure python3 points to python3.10
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    apt install -y \
        git \
        nginx \
        certbot \
        python3-certbot-nginx \
        redis-server \
        supervisor \
        postgresql \
        postgresql-contrib \
        fail2ban \
        ufw \
        htop \
        unzip
}

# Setup PostgreSQL
setup_postgresql() {
    log "Setting up PostgreSQL database..."
    
    # Generate random password for database user
    DB_PASSWORD=$(openssl rand -base64 32)
    
    # Create database and user
    sudo -u postgres psql << EOF
CREATE DATABASE ${DB_NAME};
CREATE USER ${DB_USER} WITH ENCRYPTED PASSWORD '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
ALTER USER ${DB_USER} CREATEDB;
\q
EOF
    
    # Save database credentials
    echo "DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}" >> /tmp/db_config.env
    
    log "PostgreSQL configured. Database: ${DB_NAME}, User: ${DB_USER}"
}

# Setup Redis
setup_redis() {
    log "Configuring Redis..."
    
    # Configure Redis for production
    sed -i 's/^# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
    sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
    
    systemctl enable redis-server
    systemctl restart redis-server
}

# Clone and setup project
setup_project() {
    log "Setting up MoveMarias project..."
    
    # Remove existing directory if exists
    if [ -d "$PROJECT_DIR" ]; then
        rm -rf "$PROJECT_DIR"
    fi
    
    # Clone repository
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    # Create virtual environment
    python3.10 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install Python dependencies
    pip install -r requirements.txt
    
    # Create .env file from production template
    cp .env.production .env
    
    # Generate Django secret key
    SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    
    # Generate Django cryptography key
    CRYPTO_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
    
    # Update .env file with generated values and database config
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" .env
    sed -i "s/DJANGO_CRYPTOGRAPHY_KEY=.*/DJANGO_CRYPTOGRAPHY_KEY=${CRYPTO_KEY}/" .env
    sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=${DOMAIN},www.${DOMAIN}/" .env
    sed -i "s/CSRF_TRUSTED_ORIGINS=.*/CSRF_TRUSTED_ORIGINS=https:\/\/${DOMAIN},https:\/\/www.${DOMAIN}/" .env
    
    # Add database configuration from PostgreSQL setup
    if [ -f /tmp/db_config.env ]; then
        cat /tmp/db_config.env >> .env
        rm /tmp/db_config.env
    fi
    
    # Set permissions
    chown -R www-data:www-data "$PROJECT_DIR"
    chmod 755 "$PROJECT_DIR"
    chmod 600 "$PROJECT_DIR/.env"
}

# Run Django setup
setup_django() {
    log "Setting up Django application..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Create media and static directories
    mkdir -p "$PROJECT_DIR/media"
    mkdir -p "$PROJECT_DIR/staticfiles"
    
    # Run migrations
    python manage.py migrate
    
    # Collect static files
    python manage.py collectstatic --noinput
    
    # Create superuser (non-interactive)
    echo "from users.models import CustomUser; \
    if not CustomUser.objects.filter(username='admin').exists(): \
        CustomUser.objects.create_superuser('admin', '${EMAIL}', 'MoveMarias2025!')" | python manage.py shell
    
    # Set proper permissions for static and media directories
    chown -R www-data:www-data "$PROJECT_DIR/staticfiles"
    chown -R www-data:www-data "$PROJECT_DIR/media"
    chmod -R 755 "$PROJECT_DIR/staticfiles"
    chmod -R 755 "$PROJECT_DIR/media"
    
    log "Django setup completed. Admin user created with username 'admin' and password 'MoveMarias2025!'"
    log "Static files directory: $PROJECT_DIR/staticfiles"
    log "Media files directory: $PROJECT_DIR/media"
}

# Setup Gunicorn service
setup_gunicorn() {
    log "Setting up Gunicorn service..."
    
    # Create log directory
    mkdir -p /var/log/movemarias
    chown www-data:www-data /var/log/movemarias
    
    # Copy service file
    cp "$PROJECT_DIR/deploy/movemarias.service" /etc/systemd/system/
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable movemarias
    systemctl start movemarias
    
    # Check service status
    if systemctl is-active --quiet movemarias; then
        log "Gunicorn service started successfully"
    else
        error "Failed to start Gunicorn service"
    fi
}

# Setup Nginx
setup_nginx() {
    log "Setting up Nginx..."
    
    # Update nginx configuration with correct domain
    sed -i "s/movemarias.org/${DOMAIN}/g" "$PROJECT_DIR/deploy/nginx.conf"
    sed -i "s/www.movemarias.org/www.${DOMAIN}/g" "$PROJECT_DIR/deploy/nginx.conf"
    
    # Copy Nginx configuration
    cp "$PROJECT_DIR/deploy/nginx.conf" /etc/nginx/sites-available/movemarias
    
    # Enable site and remove default
    ln -sf /etc/nginx/sites-available/movemarias /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test Nginx configuration
    nginx -t
    
    # Restart Nginx
    systemctl restart nginx
    systemctl enable nginx
}

# Setup SSL with Let's Encrypt
setup_ssl() {
    log "Setting up SSL certificate with Let's Encrypt..."
    
    # Stop nginx temporarily for standalone mode
    systemctl stop nginx
    
    # Get SSL certificate
    certbot certonly --standalone \
        -d "$DOMAIN" \
        -d "www.$DOMAIN" \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL"
    
    # Update Nginx config with correct SSL paths
    sed -i "s|/etc/ssl/certs/movemarias.crt|/etc/letsencrypt/live/${DOMAIN}/fullchain.pem|" /etc/nginx/sites-available/movemarias
    sed -i "s|/etc/ssl/private/movemarias.key|/etc/letsencrypt/live/${DOMAIN}/privkey.pem|" /etc/nginx/sites-available/movemarias
    
    # Start nginx
    systemctl start nginx
    
    # Setup auto-renewal
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
}

# Setup firewall
setup_firewall() {
    log "Setting up firewall..."
    
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw --force enable
}

# Setup monitoring and backups
setup_monitoring() {
    log "Setting up monitoring and backups..."
    
    # Copy monitoring scripts
    cp "$PROJECT_DIR/deploy/monitor.sh" /usr/local/bin/
    chmod +x /usr/local/bin/monitor.sh
    
    # Setup cron jobs for monitoring and backups
    cp "$PROJECT_DIR/deploy/production_crontab" /tmp/movemarias_cron
    crontab /tmp/movemarias_cron
    rm /tmp/movemarias_cron
}

# Final checks
final_checks() {
    log "Performing final checks..."
    
    # Check services
    services=("nginx" "movemarias" "postgresql" "redis-server")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log "✓ $service is running"
        else
            warning "✗ $service is not running"
        fi
    done
    
    # Test web connectivity
    if curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN" | grep -q "200\|301\|302"; then
        log "✓ Website is accessible at https://$DOMAIN"
    else
        warning "✗ Website may not be accessible"
    fi
}

# Main installation function
main() {
    log "Starting MoveMarias VPS installation..."
    
    check_root
    update_system
    install_python
    install_system_deps
    setup_postgresql
    setup_redis
    setup_project
    setup_django
    setup_gunicorn
    setup_nginx
    setup_ssl
    setup_firewall
    setup_monitoring
    final_checks
    
    log "==================================================================="
    log "MoveMarias installation completed successfully!"
    log "==================================================================="
    log "Website: https://$DOMAIN"
    log "Admin Panel: https://$DOMAIN/admin/"
    log "Admin Username: admin"
    log "Admin Password: MoveMarias2025!"
    log "==================================================================="
    log "Important files:"
    log "- Project directory: $PROJECT_DIR"
    log "- Environment file: $PROJECT_DIR/.env"
    log "- Nginx config: /etc/nginx/sites-available/movemarias"
    log "- Service file: /etc/systemd/system/movemarias.service"
    log "==================================================================="
    log "To check logs:"
    log "- Application: journalctl -u movemarias -f"
    log "- Nginx: tail -f /var/log/nginx/error.log"
    log "==================================================================="
}

# Run main function
main "$@"
