#!/bin/bash

# SSL/TLS Setup Script for Move Marias
# This script sets up SSL certificates using Let's Encrypt

set -e

# Configuration
DOMAIN="yourdomain.com"
EMAIL="admin@yourdomain.com"
WEBROOT="/var/www/html"
NGINX_CONF="/etc/nginx/sites-available/movemarias"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if domain is set
if [ "$DOMAIN" == "yourdomain.com" ]; then
    print_error "Please configure your domain in this script"
    exit 1
fi

# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    print_status "Installing certbot..."
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
fi

# Stop nginx temporarily
print_status "Stopping nginx..."
sudo systemctl stop nginx

# Generate SSL certificate
print_status "Generating SSL certificate for $DOMAIN..."
sudo certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

# Generate strong DH parameters
print_status "Generating DH parameters..."
if [ ! -f /etc/ssl/certs/dhparam.pem ]; then
    sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048
fi

# Create nginx SSL configuration
print_status "Creating nginx SSL configuration..."
sudo tee "$NGINX_CONF" > /dev/null <<EOF
# Move Marias SSL Configuration
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_dhparam /etc/ssl/certs/dhparam.pem;
    
    # SSL Session Settings
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';" always;
    
    # Root directory
    root /var/www/movemarias;
    index index.html;
    
    # Client settings
    client_max_body_size 100M;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        application/atom+xml
        application/javascript
        application/json
        application/rss+xml
        application/vnd.ms-fontobject
        application/x-font-ttf
        application/x-web-app-manifest+json
        application/xhtml+xml
        application/xml
        font/opentype
        image/svg+xml
        image/x-icon
        text/css
        text/plain
        text/x-component;
    
    # Static files
    location /static/ {
        alias /var/www/movemarias/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/movemarias/media/;
        expires 1y;
    }
    
    # Django application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$server_name;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    # Health check endpoint
    location /health/ {
        proxy_pass http://127.0.0.1:8000/health/;
        access_log off;
    }
    
    # Deny access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ /(\.env|\.git|\.gitignore|requirements\.txt|manage\.py) {
        deny all;
    }
}
EOF

# Enable the site
print_status "Enabling nginx site..."
sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/

# Test nginx configuration
print_status "Testing nginx configuration..."
sudo nginx -t

# Start nginx
print_status "Starting nginx..."
sudo systemctl start nginx
sudo systemctl enable nginx

# Set up automatic renewal
print_status "Setting up automatic SSL renewal..."
sudo crontab -l 2>/dev/null | grep -v certbot | sudo tee /tmp/crontab.tmp > /dev/null
echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'" | sudo tee -a /tmp/crontab.tmp > /dev/null
sudo crontab /tmp/crontab.tmp
sudo rm /tmp/crontab.tmp

# Create renewal hook script
sudo tee /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh > /dev/null <<EOF
#!/bin/bash
systemctl reload nginx
EOF

sudo chmod +x /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh

# Test SSL certificate
print_status "Testing SSL certificate..."
if curl -sSf "https://$DOMAIN" > /dev/null; then
    print_status "SSL certificate is working correctly!"
else
    print_warning "SSL certificate test failed. Please check your configuration."
fi

# Display SSL information
print_status "SSL Configuration Summary:"
echo "Domain: $DOMAIN"
echo "Certificate: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
echo "Private Key: /etc/letsencrypt/live/$DOMAIN/privkey.pem"
echo "Nginx Config: $NGINX_CONF"
echo "Auto-renewal: Enabled (daily at 12:00)"

print_status "SSL setup completed successfully!"
print_status "Your site should now be available at: https://$DOMAIN"

# Security recommendations
print_status "Security Recommendations:"
echo "1. Test your SSL configuration at: https://www.ssllabs.com/ssltest/"
echo "2. Monitor certificate expiration dates"
echo "3. Keep nginx and certbot updated"
echo "4. Consider implementing additional security measures like fail2ban"
