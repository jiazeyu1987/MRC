#!/bin/bash

# Knowledge Base Document Management Deployment Script
# This script automates the complete deployment process

set -e  # Exit on any error

# Configuration
DEPLOYMENT_ENV=${1:-production}
DOMAIN=${2:-your-domain.com}
DB_HOST=${3:-localhost}
DB_PASSWORD=${4:-secure_password}
RAGFLOW_API_KEY=${5:-your-ragflow-api-key}
RAGFLOW_URL=${6:-https://your-ragflow-instance.com}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    error "This script should not be run as root. Please run as a regular user with sudo privileges."
fi

# Validate required parameters
if [[ -z "$DOMAIN" || -z "$DB_PASSWORD" || -z "$RAGFLOW_API_KEY" || -z "$RAGFLOW_URL" ]]; then
    error "Missing required parameters. Usage: $0 <environment> <domain> <db_host> <db_password> <ragflow_api_key> <ragflow_url>"
fi

# Display deployment information
log "Starting Knowledge Base Document Management deployment"
info "Environment: $DEPLOYMENT_ENV"
info "Domain: $DOMAIN"
info "Database Host: $DB_HOST"
info "RAGFlow URL: $RAGFLOW_URL"

# Create deployment directories
DEPLOY_BASE="/opt/mrc"
APP_DIR="$DEPLOY_BASE/app"
DATA_DIR="$DEPLOY_BASE/data"
LOG_DIR="$DEPLOY_BASE/logs"
BACKUP_DIR="$DEPLOY_BASE/backups"
CONFIG_DIR="$DEPLOY_BASE/config"

log "Creating deployment directories..."
sudo mkdir -p $APP_DIR $DATA_DIR $LOG_DIR $BACKUP_DIR $CONFIG_DIR
sudo mkdir -p $DATA_DIR/{uploads,temp,chunks,processing}
sudo mkdir -p $LOG_DIR/{app,security,error}
sudo mkdir -p $CONFIG_DIR/{nginx,ssl}

# Set ownership and permissions
log "Setting ownership and permissions..."
sudo chown -R $USER:$USER $DEPLOY_BASE
chmod 755 $DEPLOY_BASE

# Install system dependencies
log "Installing system dependencies..."
sudo apt update
sudo apt install -y \
    python3.8 \
    python3.8-dev \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    nginx \
    postgresql \
    postgresql-contrib \
    redis-server \
    git \
    curl \
    wget \
    htop \
    unzip \
    build-essential \
    libpq-dev \
    libmagic1 \
    clamav \
    clamav-daemon \
    ufw \
    fail2ban

# Install Python virtual environment
log "Setting up Python virtual environment..."
python3.8 -m venv $APP_DIR/venv
$APP_DIR/venv/bin/pip install --upgrade pip setuptools wheel

# Clone or update the repository
REPO_URL="https://github.com/yourorg/mrc-document-management.git"
if [[ -d "$APP_DIR/mrc-document-management" ]]; then
    log "Updating existing repository..."
    cd $APP_DIR/mrc-document-management
    git pull origin main
else
    log "Cloning repository..."
    cd $APP_DIR
    git clone $REPO_URL mrc-document-management
fi

APP_CODE_DIR="$APP_DIR/mrc-document-management"

# Install Python dependencies
log "Installing Python dependencies..."
cd $APP_CODE_DIR/backend
$APP_DIR/venv/bin/pip install -r requirements.txt

# Install Node.js dependencies and build frontend
log "Installing Node.js dependencies and building frontend..."
cd $APP_CODE_DIR/front
npm install
npm run build

# Setup environment files
log "Setting up environment configuration..."

# Backend environment file
cat > $APP_CODE_DIR/backend/.env << EOF
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=$DEPLOYMENT_ENV
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False

# Database Configuration
DATABASE_URL=postgresql://mrc_user:$DB_PASSWORD@$DB_HOST:5432/mrc_documents
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_SESSION_URL=redis://localhost:6379/1

# JWT Configuration
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ACCESS_TOKEN_EXPIRES=3600

# RAGFlow Configuration
RAGFLOW_API_KEY=$RAGFLOW_API_KEY
RAGFLOW_BASE_URL=$RAGFLOW_URL
RAGFLOW_TIMEOUT=30
RAGFLOW_MAX_RETRIES=3
RAGFLOW_RETRY_DELAY=1.0
RAGFLOW_VERIFY_SSL=True

# File Upload Configuration
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_FOLDER=$DATA_DIR/uploads
TEMP_UPLOAD_FOLDER=$DATA_DIR/temp
ALLOWED_EXTENSIONS=pdf,doc,docx,txt,md,html,htm,rtf,jpg,jpeg,png,gif,bmp,svg,zip,rar,7z,tar,gz

# Security Configuration
ENABLE_VIRUS_SCANNING=True
CLAMAV_SOCKET=/var/run/clamav/clamd.sock
ENABLE_ENCRYPTION_AT_REST=True
ENCRYPTION_KEY_FILE=$CONFIG_DIR/encryption.key

# Rate Limiting Configuration
ENABLE_RATE_LIMITING=True
RATE_LIMIT_STORAGE=redis
MAX_API_REQUESTS_PER_HOUR=1000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=$LOG_DIR/app.log
SECURITY_LOG_FILE=$LOG_DIR/security.log
ERROR_LOG_FILE=$LOG_DIR/error.log

# Monitoring Configuration
ENABLE_MONITORING=True
HEALTH_CHECK_ENDPOINT=/health

# SSL Configuration
SSL_CERT_PATH=$CONFIG_DIR/ssl/mrc-cert.pem
SSL_KEY_PATH=$CONFIG_DIR/ssl/mrc-key.pem
EOF

# Frontend environment file
cat > $APP_CODE_DIR/front/.env << EOF
# API Configuration
VITE_API_BASE_URL=https://$DOMAIN/api
VITE_API_BASE_URL_ALT=https://$DOMAIN/api

# Application Configuration
VITE_APP_NAME=MRC Document Management
VITE_APP_VERSION=1.0.0
VITE_ENVIRONMENT=$DEPLOYMENT_ENV

# Feature Flags
VITE_ENABLE_DOCUMENT_UPLOAD=true
VITE_ENABLE_ADVANCED_SEARCH=true
VITE_ENABLE_REAL_TIME_PROGRESS=true

# Security
VITE_ENABLE_CSP=true
VITE_CSP_NONCE=random
EOF

# Generate encryption key
log "Generating encryption key..."
openssl rand -hex 32 > $CONFIG_DIR/encryption.key
chmod 600 $CONFIG_DIR/encryption.key

# Setup PostgreSQL
log "Setting up PostgreSQL database..."
sudo -u postgres psql << EOF
CREATE USER mrc_user WITH ENCRYPTED PASSWORD '$DB_PASSWORD';
CREATE DATABASE mrc_documents;
GRANT ALL PRIVILEGES ON DATABASE mrc_documents TO mrc_user;
ALTER USER mrc_user CREATEDB;
\q
EOF

# Install PostgreSQL extensions
sudo -u postgres psql mrc_documents << EOF
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
\q
EOF

# Run database migrations
log "Running database migrations..."
cd $APP_CODE_DIR/backend
$APP_DIR/venv/bin/python run.py init-db
$APP_DIR/venv/bin/python add_document_management_tables.py

# Setup SSL certificates
log "Setting up SSL certificates..."
mkdir -p $CONFIG_DIR/ssl

# Generate self-signed certificate (replace with Let's Encrypt in production)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout $CONFIG_DIR/ssl/mrc-key.pem \
    -out $CONFIG_DIR/ssl/mrc-cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"

chmod 600 $CONFIG_DIR/ssl/mrc-key.pem
chmod 644 $CONFIG_DIR/ssl/mrc-cert.pem

# Configure Nginx
log "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/mrc-document-management << EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL Configuration
    ssl_certificate $CONFIG_DIR/ssl/mrc-cert.pem;
    ssl_certificate_key $CONFIG_DIR/ssl/mrc-key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Frontend
    location / {
        root $APP_CODE_DIR/front/dist;
        try_files \$uri \$uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5010;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;

        # File upload configuration
        client_max_body_size 50M;
        proxy_request_buffering off;
        proxy_buffering off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://127.0.0.1:5010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:5010/health;
        access_log off;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/mrc-document-management /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Setup systemd services
log "Setting up systemd services..."

# Backend service
sudo tee /etc/systemd/system/mrc-backend.service << EOF
[Unit]
Description=MRC Document Management Backend
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$APP_CODE_DIR/backend
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_CODE_DIR/backend/.env
ExecStart=$APP_DIR/venv/bin/python run.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=mrc-backend

[Install]
WantedBy=multi-user.target
EOF

# Celery service
sudo tee /etc/systemd/system/mrc-celery.service << EOF
[Unit]
Description=MRC Document Management Celery Worker
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$APP_CODE_DIR/backend
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_CODE_DIR/backend/.env
ExecStart=$APP_DIR/venv/bin/celery -A app.celery worker --loglevel=INFO
ExecStop=/bin/kill -TERM \$MAINPID
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=mrc-celery

[Install]
WantedBy=multi-user.target
EOF

# Configure firewall
log "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Setup log rotation
log "Setting up log rotation..."
sudo tee /etc/logrotate.d/mrc-document-management << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        systemctl reload mrc-backend || true
    endscript
}

$CONFIG_DIR/ssl/*.pem {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF

# Setup monitoring
log "Setting up basic monitoring..."
sudo tee $CONFIG_DIR/monitoring-setup.sh << 'EOF'
#!/bin/bash
# Basic monitoring setup

# Create monitoring directories
mkdir -p $LOG_DIR/monitoring

# Health check script
cat > $LOG_DIR/monitoring/health_check.sh << 'HEALTH_EOF'
#!/bin/bash
# Health check script
HEALTH_URL="https://$DOMAIN/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$RESPONSE" -eq 200 ]; then
    echo "OK: Application is healthy"
    exit 0
else
    echo "CRITICAL: Application health check failed (HTTP $RESPONSE)"
    exit 1
fi
HEALTH_EOF

chmod +x $LOG_DIR/monitoring/health_check.sh
EOF

chmod +x $CONFIG_DIR/monitoring-setup.sh
sudo -u $USER $CONFIG_DIR/monitoring-setup.sh

# Enable and start services
log "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable mrc-backend
sudo systemctl enable mrc-celery
sudo systemctl enable nginx
sudo systemctl enable postgresql
sudo systemctl enable redis-server

sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl start mrc-celery
sudo systemctl start mrc-backend
sudo systemctl restart nginx

# Wait for services to start
sleep 5

# Verify deployment
log "Verifying deployment..."

# Check service status
services=("mrc-backend" "mrc-celery" "nginx" "postgresql" "redis-server")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        log "✓ $service is running"
    else
        error "✗ $service failed to start"
    fi
done

# Test health endpoint
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5010/health")
if [ "$HEALTH_RESPONSE" -eq 200 ]; then
    log "✓ Backend health check passed"
else
    error "✗ Backend health check failed (HTTP $HEALTH_RESPONSE)"
fi

# Test database connection
if sudo -u postgres psql -h $DB_HOST -U mrc_user -d mrc_documents -c "SELECT 1;" >/dev/null 2>&1; then
    log "✓ Database connection successful"
else
    error "✗ Database connection failed"
fi

# Test Redis connection
if redis-cli ping >/dev/null 2>&1; then
    log "✓ Redis connection successful"
else
    error "✗ Redis connection failed"
fi

# Test RAGFlow connection
if curl -s -H "Authorization: Bearer $RAGFLOW_API_KEY" "$RAGFLOW_URL/api/datasets" >/dev/null 2>&1; then
    log "✓ RAGFlow connection successful"
else
    warn "RAGFlow connection test failed - please verify manually"
fi

# Create deployment success file
echo "DEPLOYMENT_SUCCESS=$(date +%s)" > $CONFIG_DIR/deployment_info.txt
echo "DEPLOYMENT_ENV=$DEPLOYMENT_ENV" >> $CONFIG_DIR/deployment_info.txt
echo "DOMAIN=$DOMAIN" >> $CONFIG_DIR/deployment_info.txt

# Display completion message
log "Deployment completed successfully!"
echo ""
echo "Access Information:"
echo "  Application URL: https://$DOMAIN"
echo "  Admin Interface: https://$DOMAIN/api/health"
echo "  Logs: $LOG_DIR/"
echo "  Config: $CONFIG_DIR/"
echo ""
echo "Next Steps:"
echo "  1. Update your DNS to point $DOMAIN to this server"
echo "  2. Configure SSL with Let's Encrypt for production"
echo "  3. Set up monitoring and alerting"
echo "  4. Configure backup procedures"
echo "  5. Review security settings"
echo ""
echo "Management Commands:"
echo "  View logs: sudo journalctl -u mrc-backend -f"
echo "  Restart app: sudo systemctl restart mrc-backend"
echo "  Check status: sudo systemctl status mrc-backend"
echo "  Database backup: sudo -u postgres pg_dump mrc_documents > backup.sql"
echo ""

exit 0