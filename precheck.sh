#!/bin/bash

# =============================================================================
# MoveMarias Pre-Installation Check Script
# Verifica se a VPS está pronta para instalação
# =============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log() { echo -e "${GREEN}[✓] $1${NC}"; }
error() { echo -e "${RED}[✗] $1${NC}"; }
warning() { echo -e "${YELLOW}[!] $1${NC}"; }
info() { echo -e "${BLUE}[i] $1${NC}"; }

echo "============================================================================="
echo "MoveMarias VPS Pre-Installation Check"
echo "============================================================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    error "Must run as root. Use: sudo $0"
    exit 1
fi

log "Running as root user"

# Check OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" == "ubuntu" && "${VERSION_ID}" > "18.04" ]] || [[ "$ID" == "debian" && "${VERSION_ID}" > "10" ]]; then
        log "OS: $PRETTY_NAME (Supported)"
    else
        warning "OS: $PRETTY_NAME (May not be fully supported)"
    fi
else
    error "Cannot determine OS version"
fi

# Check system resources
info "Checking system resources..."

# RAM
RAM_MB=$(free -m | awk 'NR==2{print $2}')
if [ "$RAM_MB" -ge 2048 ]; then
    log "RAM: ${RAM_MB}MB (Sufficient)"
elif [ "$RAM_MB" -ge 1024 ]; then
    warning "RAM: ${RAM_MB}MB (Minimum, may need optimization)"
else
    error "RAM: ${RAM_MB}MB (Insufficient - need at least 1GB)"
fi

# Disk space
DISK_GB=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$DISK_GB" -ge 20 ]; then
    log "Disk space: ${DISK_GB}GB available (Sufficient)"
elif [ "$DISK_GB" -ge 10 ]; then
    warning "Disk space: ${DISK_GB}GB available (Tight, monitor usage)"
else
    error "Disk space: ${DISK_GB}GB available (Insufficient - need at least 10GB)"
fi

# CPU cores
CPU_CORES=$(nproc)
if [ "$CPU_CORES" -ge 2 ]; then
    log "CPU cores: ${CPU_CORES} (Good)"
else
    warning "CPU cores: ${CPU_CORES} (Single core may impact performance)"
fi

# Check internet connectivity
info "Checking connectivity..."

if ping -c 1 google.com &> /dev/null; then
    log "Internet connectivity: Available"
else
    error "Internet connectivity: Not available"
fi

if ping -c 1 github.com &> /dev/null; then
    log "GitHub connectivity: Available"
else
    error "GitHub connectivity: Not available"
fi

# Check package manager
info "Checking package manager..."

if command -v apt &> /dev/null; then
    log "Package manager: apt (Available)"
    
    # Update package list
    if apt update &> /dev/null; then
        log "Package list: Updated successfully"
    else
        error "Package list: Update failed"
    fi
else
    error "Package manager: apt not found"
fi

# Check for conflicting services
info "Checking for conflicting services..."

services=("apache2" "httpd")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        warning "Conflicting service detected: $service (will be stopped during installation)"
    fi
done

# Check Python availability
info "Checking Python..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
    log "Python: $PYTHON_VERSION available"
else
    warning "Python3: Not found (will be installed)"
fi

# Check Git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | cut -d " " -f 3)
    log "Git: $GIT_VERSION available"
else
    warning "Git: Not found (will be installed)"
fi

# Check curl/wget
if command -v curl &> /dev/null; then
    log "curl: Available"
elif command -v wget &> /dev/null; then
    log "wget: Available"
else
    warning "Neither curl nor wget found (will be installed)"
fi

# Check if domain is configured (if provided)
if [ ! -z "$1" ]; then
    DOMAIN="$1"
    info "Checking domain configuration for: $DOMAIN"
    
    # Get VPS IP
    VPS_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null)
    
    if [ ! -z "$VPS_IP" ]; then
        log "VPS IP: $VPS_IP"
        
        # Check DNS resolution
        DOMAIN_IP=$(dig +short "$DOMAIN" 2>/dev/null | tail -n1)
        
        if [ "$DOMAIN_IP" == "$VPS_IP" ]; then
            log "DNS: $DOMAIN correctly points to $VPS_IP"
        elif [ ! -z "$DOMAIN_IP" ]; then
            warning "DNS: $DOMAIN points to $DOMAIN_IP (should be $VPS_IP)"
        else
            error "DNS: Cannot resolve $DOMAIN"
        fi
    else
        warning "Cannot determine VPS IP address"
    fi
fi

# Summary
echo ""
echo "============================================================================="
echo "Pre-Installation Check Summary"
echo "============================================================================="

# Count errors and warnings
errors=$(grep -c "✗" /tmp/precheck.log 2>/dev/null || echo "0")
warnings=$(grep -c "!" /tmp/precheck.log 2>/dev/null || echo "0")

if [ "$errors" -eq 0 ] && [ "$warnings" -eq 0 ]; then
    log "System is ready for MoveMarias installation!"
    echo ""
    info "Next steps:"
    echo "1. Run: wget https://raw.githubusercontent.com/brunonatanaelsr/02/main/vps_install.sh"
    echo "2. Run: chmod +x vps_install.sh"
    echo "3. Run: ./vps_install.sh"
elif [ "$errors" -eq 0 ]; then
    warning "System has $warnings warning(s) but should work"
    echo ""
    info "You can proceed with installation, but monitor the warnings."
else
    error "System has $errors error(s) that must be fixed before installation"
    echo ""
    info "Please fix the errors above before proceeding."
fi

echo "============================================================================="
