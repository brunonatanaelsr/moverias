#!/bin/bash

# MoveMarias Production Deployment Script
# This script handles the complete deployment process for production

set -e  # Exit on any error

echo "🚀 Starting MoveMarias Production Deployment"

# Configuration
PROJECT_DIR="/opt/movemarias"
BACKUP_DIR="/opt/movemarias/backups"
VENV_DIR="/opt/movemarias/venv"
USER="movemarias"
GROUP="movemarias"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root"
   exit 1
fi

# Create system user if not exists
if ! id "$USER" &>/dev/null; then
    log_info "Creating system user: $USER"
    useradd -r -s /bin/bash -d "$PROJECT_DIR" "$USER"
    mkdir -p "$PROJECT_DIR"
    chown "$USER:$GROUP" "$PROJECT_DIR"
fi

# Create directories
log_info "Creating project directories"
mkdir -p "$PROJECT_DIR"/{logs,media,staticfiles,backups}
mkdir -p "$BACKUP_DIR"

# Setup Python virtual environment
log_info "Setting up Python virtual environment"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install/upgrade pip and dependencies
log_info "Installing Python dependencies"
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary redis

# Database backup
log_info "Creating database backup"
BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
    cp "$PROJECT_DIR/db.sqlite3" "$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3"
fi

# Run migrations
log_info "Running database migrations"
python manage.py migrate --settings=movemarias.settings_production

# Collect static files
log_info "Collecting static files"
python manage.py collectstatic --noinput --settings=movemarias.settings_production

# Create superuser if needed
log_info "Checking for superuser"
python manage.py shell --settings=movemarias.settings_production -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@movemarias.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Set proper permissions
log_info "Setting file permissions"
chown -R "$USER:$GROUP" "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"
chmod -R 775 "$PROJECT_DIR"/{logs,media,staticfiles}

# Install systemd service
log_info "Installing systemd service"
cat > /etc/systemd/system/movemarias.service << 'EOF'
[Unit]
Description=MoveMarias Django Application
After=network.target

[Service]
Type=notify
User=movemarias
Group=movemarias
WorkingDirectory=/opt/movemarias
Environment=PATH=/opt/movemarias/venv/bin
Environment=DJANGO_SETTINGS_MODULE=movemarias.settings_production
ExecStart=/opt/movemarias/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 movemarias.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Install nginx configuration
log_info "Installing nginx configuration"
cat > /etc/nginx/sites-available/movemarias << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Static files
    location /static/ {
        alias /opt/movemarias/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /opt/movemarias/media/;
        expires 7d;
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check
    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable nginx site
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi
ln -sf /etc/nginx/sites-available/movemarias /etc/nginx/sites-enabled/

# Test nginx configuration
nginx -t

# Install monitoring cron jobs
log_info "Installing monitoring cron jobs"
cat > /tmp/movemarias_cron << 'EOF'
# MoveMarias monitoring and maintenance
*/5 * * * * /opt/movemarias/venv/bin/python /opt/movemarias/manage.py run_monitoring --settings=movemarias.settings_production
0 2 * * * /opt/movemarias/venv/bin/python /opt/movemarias/manage.py run_custom_jobs --settings=movemarias.settings_production
0 3 * * 0 /opt/movemarias/venv/bin/python /opt/movemarias/manage.py clearsessions --settings=movemarias.settings_production
EOF

crontab -u "$USER" /tmp/movemarias_cron
rm /tmp/movemarias_cron

# Create log rotation
log_info "Setting up log rotation"
cat > /etc/logrotate.d/movemarias << 'EOF'
/opt/movemarias/logs/*.log {
    weekly
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        systemctl reload movemarias
    endscript
}
EOF

# Start and enable services
log_info "Starting services"
systemctl daemon-reload
systemctl enable movemarias
systemctl start movemarias
systemctl reload nginx

# Final health check
log_info "Running final health check"
sleep 5
if curl -f http://localhost/health/ > /dev/null 2>&1; then
    log_info "✅ Deployment successful! MoveMarias is running"
else
    log_error "❌ Health check failed"
    systemctl status movemarias
    exit 1
fi

# Show status
log_info "Service status:"
systemctl status movemarias --no-pager -l

log_info "🎉 MoveMarias deployment completed successfully!"
log_info "📊 Access the application at: http://your-domain.com"
log_info "🔧 Admin panel: http://your-domain.com/admin/"
log_info "📈 Monitoring: http://your-domain.com/monitoring/"

echo ""
echo "Next steps:"
echo "1. Configure your domain in ALLOWED_HOSTS"
echo "2. Set up SSL/TLS certificate"
echo "3. Configure email settings"
echo "4. Set up database backups"
echo "5. Monitor logs: tail -f /opt/movemarias/logs/production.log"
