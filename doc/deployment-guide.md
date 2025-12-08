# Knowledge Base Document Management Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Knowledge Base Document Management system to production environments. It covers infrastructure setup, configuration, security hardening, and operational procedures.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Requirements](#infrastructure-requirements)
3. [Environment Setup](#environment-setup)
4. [Database Setup](#database-setup)
5. [RAGFlow Configuration](#ragflow-configuration)
6. [Application Deployment](#application-deployment)
7. **[Security Hardening](#security-hardening)**
8. [Monitoring Setup](#monitoring-setup)
9. [Backup and Recovery](#backup-and-recovery)
10. [Performance Tuning](#performance-tuning)
11. [Troubleshooting](#troubleshooting)
12. [Maintenance Procedures](#maintenance-procedures)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04 LTS or CentOS 8+
- **Python**: 3.8 or higher
- **Node.js**: 16.0 or higher
- **Database**: PostgreSQL 12+ or MySQL 8.0+ (SQLite for development)
- **Redis**: 6.0+ for caching and session storage
- **Web Server**: Nginx 1.18+
- **SSL Certificate**: Valid certificate for HTTPS

### Required Services

- **RAGFlow Instance**: Running and accessible instance
- **Message Queue**: Redis or RabbitMQ for background processing
- **File Storage**: Local storage or S3-compatible object storage
- **Load Balancer**: (Optional for high availability)

### Software Dependencies

#### Backend Dependencies
```bash
# Python packages (from requirements.txt)
Flask>=2.3.3
Flask-SQLAlchemy>=2.5.1
Flask-Migrate>=3.1.0
Flask-RESTful>=0.3.10
Flask-CORS>=3.0.10
Flask-JWT-Extended>=4.3.1
SQLAlchemy>=1.4.23
redis>=4.0.2
celery>=5.2.0
requests>=2.27.0
python-magic>=0.4.24
Pillow>=8.4.0
```

#### Frontend Dependencies
```bash
# Node packages (from package.json)
react>=18.2.0
react-dom>=18.2.0
typescript>=4.5.0
vite>=4.0.0
tailwindcss>=3.3.0
lucide-react>=0.344.0
axios>=1.6.0
react-dropzone>=14.2.0
```

## Infrastructure Requirements

### Minimum Production Setup

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 4 cores | 8 cores |
| **Memory** | 8 GB | 16 GB |
| **Storage** | 100 GB SSD | 500 GB SSD |
| **Network** | 100 Mbps | 1 Gbps |
| **Database** | PostgreSQL 12+ | PostgreSQL 14+ |
| **Cache** | Redis 6+ | Redis 7+ |

### High Availability Setup

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Application Servers** | 2 | 3+ |
| **Database Servers** | 1 (Primary) | 2 (Primary + Replica) |
| **Redis Servers** | 1 | 3 (Cluster) |
| **Load Balancers** | 1 | 2 (Active + Passive) |

## Environment Setup

### 1. Server Preparation

```bash
#!/bin/bash
# Server setup script

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y \
    python3.8 \
    python3.8-dev \
    python3-pip \
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
    unzip

# Install additional security packages
sudo apt install -y \
    clamav \
    clamav-daemon \
    fail2ban \
    ufw

# Create application user
sudo useradd -m -s /bin/bash mrc-user
sudo usermod -aG sudo mrc-user

# Create application directories
sudo mkdir -p /opt/mrc/{app,data,logs,backups}
sudo chown -R mrc-user:mrc-user /opt/mrc

# Install Python virtual environment
sudo -u mrc-user python3 -m venv /opt/mrc/app/venv
sudo -u mrc-user /opt/mrc/app/venv/bin/pip install --upgrade pip
```

### 2. Application Deployment

```bash
#!/bin/bash
# Application deployment script

# Set variables
APP_DIR="/opt/mrc/app"
DATA_DIR="/opt/mrc/data"
LOG_DIR="/opt/mrc/logs"
BACKUP_DIR="/opt/mrc/backups"

# Clone repository (replace with your repository URL)
cd $APP_DIR
sudo -u mrc-user git clone https://github.com/yourorg/mrc-document-management.git .

# Backend setup
cd $APP_DIR/backend
sudo -u mrc-user $APP_DIR/app/venv/bin/pip install -r requirements.txt

# Frontend setup
cd $APP_DIR/front
sudo -u mrc-user npm install
sudo -u mrc-user npm run build

# Set up environment files
sudo -u mrc-user cp $APP_DIR/backend/.env.example $APP_DIR/backend/.env
sudo -u mrc-user cp $APP_DIR/front/.env.example $APP_DIR/front/.env

# Set permissions
sudo chown -R mrc-user:mrc-user $APP_DIR
sudo chmod +x $APP_DIR/backend/*.py
```

### 3. Environment Configuration

#### Backend Configuration (.env)

```bash
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False

# Database Configuration
DATABASE_URL=postgresql://mrc-user:password@localhost:5432/mrc_documents
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_SESSION_URL=redis://localhost:6379/1

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# RAGFlow Configuration
RAGFLOW_API_KEY=your-ragflow-api-key
RAGFLOW_BASE_URL=https://your-ragflow-instance.com
RAGFLOW_TIMEOUT=30
RAGFLOW_MAX_RETRIES=3
RAGFLOW_RETRY_DELAY=1.0
RAGFLOW_VERIFY_SSL=True

# File Upload Configuration
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_FOLDER=/opt/mrc/data/uploads
TEMP_UPLOAD_FOLDER=/opt/mrc/data/temp
ALLOWED_EXTENSIONS=pdf,doc,docx,txt,md,html,htm,rtf,jpg,jpeg,png,gif,bmp,svg

# Security Configuration
ENABLE_VIRUS_SCANNING=True
CLAMAV_SOCKET=/var/run/clamav/clamd.sock
ENABLE_ENCRYPTION_AT_REST=True
ENCRYPTION_KEY_FILE=/opt/mrc/data/encryption.key

# Rate Limiting Configuration
ENABLE_RATE_LIMITING=True
RATE_LIMIT_STORAGE=redis
MAX_API_REQUESTS_PER_HOUR=1000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/opt/mrc/logs/app.log
SECURITY_LOG_FILE=/opt/mrc/logs/security.log
ERROR_LOG_FILE=/opt/mrc/logs/error.log

# Monitoring Configuration
ENABLE_MONITORING=True
PROMETHEUS_PORT=9090
HEALTH_CHECK_ENDPOINT=/health

# SSL Configuration
SSL_CERT_PATH=/etc/ssl/certs/mrc-cert.pem
SSL_KEY_PATH=/etc/ssl/private/mrc-key.pem
```

#### Frontend Configuration (.env)

```bash
# API Configuration
VITE_API_BASE_URL=https://your-domain.com/api
VITE_API_BASE_URL_ALT=https://api.your-domain.com

# Application Configuration
VITE_APP_NAME=MRC Document Management
VITE_APP_VERSION=1.0.0
VITE_ENVIRONMENT=production

# Feature Flags
VITE_ENABLE_DOCUMENT_UPLOAD=true
VITE_ENABLE_ADVANCED_SEARCH=true
VITE_ENABLE_REAL_TIME_PROGRESS=true

# Analytics (Optional)
VITE_ENABLE_ANALYTICS=false
VITE_ANALYTICS_ID=your-analytics-id

# Security
VITE_ENABLE_CSP=true
VITE_CSP_NONCE=random
```

## Database Setup

### PostgreSQL Setup

```bash
#!/bin/bash
# Database setup script

# Switch to postgres user
sudo -u postgres psql << EOF

-- Create database
CREATE DATABASE mrc_documents;

-- Create user
CREATE USER mrc_user WITH ENCRYPTED PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE mrc_documents TO mrc_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mrc_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mrc_user;

-- Exit PostgreSQL
\q

EOF

# Create database extensions
sudo -u postgres psql mrc_documents << EOF

-- Install required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Exit
\q

EOF
```

### Database Migration

```bash
#!/bin/bash
# Database migration script

cd /opt/mrc/backend

# Activate virtual environment
source /opt/mrc/app/venv/bin/activate

# Run database migrations
python run.py init-db

# Create document management tables
python add_document_management_tables.py

# Add knowledge base configuration migration if needed
python add_knowledge_base_config_migration.py

# Verify database integrity
python check_db.py
```

## RAGFlow Configuration

### RAGFlow Instance Setup

1. **Deploy RAGFlow Instance**:
   ```bash
   # Deploy RAGFlow using Docker (recommended)
   docker run -d \
     --name ragflow \
     -p 9380:9380 \
     -v /opt/mrc/data/ragflow:/ragflow/data \
     -e RAGFLOW_API_KEY=your-api-key \
     infiniflow/ragflow:latest
   ```

2. **Configure RAGFlow**:
   ```bash
   # RAGFlow configuration
   export RAGFLOW_API_KEY="your-secure-api-key"
   export RAGFLOW_HOST="https://your-ragflow-domain.com"
   export RAGFLOW_PORT="9380"
   ```

3. **Test RAGFlow Connection**:
   ```bash
   # Test connection
   curl -H "Authorization: Bearer your-api-key" \
        https://your-ragflow-domain.com/api/datasets
   ```

## Application Deployment

### 1. Systemd Services

#### Backend Service

```ini
# /etc/systemd/system/mrc-backend.service

[Unit]
Description=MRC Document Management Backend
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=simple
User=mrc-user
Group=mrc-user
WorkingDirectory=/opt/mrc/backend
Environment=PATH=/opt/mrc/app/venv/bin
EnvironmentFile=/opt/mrc/backend/.env
ExecStart=/opt/mrc/app/venv/bin/python run.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=mrc-backend

[Install]
WantedBy=multi-user.target
```

#### Celery Worker Service

```ini
# /etc/systemd/system/mrc-celery.service

[Unit]
Description=MRC Document Management Celery Worker
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=mrc-user
Group=mrc-user
WorkingDirectory=/opt/mrc/backend
Environment=PATH=/opt/mrc/app/venv/bin
EnvironmentFile=/opt/mrc/backend/.env
ExecStart=/opt/mrc/app/venv/bin/celery -A app.celery worker --loglevel=INFO
ExecStop=/bin/kill -TERM $MAINPID
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=mrc-celery

[Install]
WantedBy=multi-user.target
```

#### Frontend Service

```ini
# /etc/systemd/system/mrc-frontend.service

[Unit]
Description=MRC Document Management Frontend
After=network.target

[Service]
Type=simple
User=mrc-user
Group=mrc-user
WorkingDirectory=/opt/mrc/front
Environment=NODE_ENV=production
ExecStart=/usr/bin/npm run preview
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=mrc-frontend

[Install]
WantedBy=multi-user.target
```

### 2. Nginx Configuration

```nginx
# /etc/nginx/sites-available/mrc-document-management

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/mrc-cert.pem;
    ssl_certificate_key /etc/ssl/private/mrc-key.pem;
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
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;";

    # Frontend (served from build directory)
    location / {
        root /opt/mrc/front/dist;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;

        # File upload configuration
        client_max_body_size 50M;
        proxy_request_buffering off;
        proxy_buffering off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # WebSocket support for real-time updates
    location /ws/ {
        proxy_pass http://127.0.0.1:5010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5010/health;
        access_log off;
    }
}
```

### 3. Enable Services

```bash
#!/bin/bash
# Enable and start services

# Enable services
sudo systemctl enable mrc-backend
sudo systemctl enable mrc-celery
sudo systemctl enable mrc-frontend
sudo systemctl enable nginx
sudo systemctl enable postgresql
sudo systemctl enable redis-server

# Start services
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl start mrc-celery
sudo systemctl start mrc-backend
sudo systemctl start nginx

# Check service status
sudo systemctl status mrc-backend
sudo systemctl status mrc-celery
sudo systemctl status mrc-frontend
sudo systemctl status nginx
```

## Security Hardening

### 1. Firewall Configuration

```bash
#!/bin/bash
# Firewall setup script

# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (with rate limiting)
sudo ufw allow ssh
sudo ufw limit ssh

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow application-specific ports (internal only)
sudo ufw allow from 10.0.0.0/8 to any port 5010
sudo ufw allow from 172.16.0.0/12 to any port 5010
sudo ufw allow from 192.168.0.0/16 to any port 5010

# Enable firewall
sudo ufw enable
```

### 2. Fail2Ban Configuration

```ini
# /etc/fail2ban/jail.local

[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
```

### 3. SSL Certificate Management

```bash
#!/bin/bash
# SSL certificate setup

# Option 1: Self-signed certificate (for testing)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/mrc-key.pem \
    -out /etc/ssl/certs/mrc-cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

# Option 2: Let's Encrypt certificate (recommended for production)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Set up automatic renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 4. Application Security

```python
# Production security configuration
SECURITY_CONFIG = {
    'ENABLE_SECURITY_HEADERS': True,
    'ENABLE_CSRF_PROTECTION': True,
    'ENABLE_RATE_LIMITING': True,
    'ENABLE_INPUT_VALIDATION': True,
    'ENABLE_AUDIT_LOGGING': True,
    'ENABLE_VIRUS_SCANNING': True,
    'ENABLE_ENCRYPTION': True,
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': 3600,
    'WTF_CSRF_TIME_LIMIT': 3600,
    'WTF_CSRF_SSL_STRICT': True
}
```

## Monitoring Setup

### 1. Prometheus Configuration

```yaml
# /etc/prometheus/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'mrc-backend'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s
    metrics_path: /metrics

  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
    scrape_interval: 30s
```

### 2. Grafana Dashboard

```json
{
  "dashboard": {
    "title": "MRC Document Management Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(flask_http_request_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Active Uploads",
        "type": "stat",
        "targets": [
          {
            "expr": "active_document_uploads",
            "legendFormat": "Active Uploads"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_activity_count",
            "legendFormat": "Active Connections"
          }
        ]
      }
    ]
  }
}
```

### 3. Health Checks

```python
# /opt/mrc/backend/health_check.py

from flask import Blueprint, jsonify
import psutil
import redis
from app import db

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # Database health
    try:
        db.session.execute('SELECT 1')
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time": "fast"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"

    # Redis health
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy"
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # System resources
    health_status["checks"]["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "status": "healthy"
    }

    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code
```

## Backup and Recovery

### 1. Database Backup Script

```bash
#!/bin/bash
# Database backup script

BACKUP_DIR="/opt/mrc/backups"
DB_NAME="mrc_documents"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create database backup
sudo -u postgres pg_dump $DB_NAME > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Database backup completed: $BACKUP_FILE.gz"
```

### 2. File Backup Script

```bash
#!/bin/bash
# File backup script

BACKUP_DIR="/opt/mrc/backups"
APP_DATA_DIR="/opt/mrc/data"
DATE=$(date +%Y%m%d_%H%M%S)
FILE_BACKUP_DIR="$BACKUP_DIR/files_backup_$DATE"

# Create backup directory
mkdir -p $FILE_BACKUP_DIR

# Backup application files
rsync -av --exclude='temp/*' $APP_DATA_DIR/ $FILE_BACKUP_DIR/

# Compress backup
tar -czf "$FILE_BACKUP_DIR.tar.gz" -C $BACKUP_DIR $(basename $FILE_BACKUP_DIR)
rm -rf $FILE_BACKUP_DIR

# Remove file backups older than 7 days
find $BACKUP_DIR -name "files_backup_*.tar.gz" -mtime +7 -delete

echo "File backup completed: $FILE_BACKUP_DIR.tar.gz"
```

### 3. Automated Backup Cron Job

```bash
# Add to crontab
crontab -e

# Daily database backup at 2 AM
0 2 * * * /opt/mrc/scripts/backup_database.sh

# Weekly file backup on Sunday at 3 AM
0 3 * * 0 /opt/mrc/scripts/backup_files.sh

# Monthly cleanup of old logs
0 4 1 * * find /opt/mrc/logs -name "*.log" -mtime +90 -delete
```

## Performance Tuning

### 1. Database Optimization

```sql
-- PostgreSQL performance tuning
-- postgresql.conf key settings

# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Connection settings
max_connections = 100
shared_preload_libraries = 'pg_stat_statements'

# Query optimization
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
```

### 2. Redis Optimization

```bash
# redis.conf key settings

# Memory settings
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence settings
save 900 1
save 300 10
save 60 10000

# Network settings
tcp-keepalive 300
timeout 0

# Security settings
requirepass your-redis-password
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
```

### 3. Nginx Optimization

```nginx
# Performance optimizations in nginx.conf

# Worker processes
worker_processes auto;
worker_connections 1024;

# File descriptors
worker_rlimit_nofile 65535;

# Enable gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/json
    application/javascript
    application/xml+rss
    application/atom+xml
    image/svg+xml;

# Caching
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary Accept-Encoding;
}
```

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check service status
sudo systemctl status mrc-backend
sudo journalctl -u mrc-backend -f

# Check logs
tail -f /opt/mrc/logs/app.log
tail -f /opt/mrc/logs/error.log

# Check configuration
python -c "from app import create_app; app = create_app(); print('Config OK')"
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql
sudo -u postgres psql -l

# Test connection
psql -h localhost -U mrc_user -d mrc_documents

# Check network connectivity
telnet localhost 5432
```

#### 3. File Upload Issues

```bash
# Check upload permissions
ls -la /opt/mrc/data/uploads
sudo chown -R mrc-user:mrc-user /opt/mrc/data

# Check disk space
df -h
du -sh /opt/mrc/data

# Check file size limits
cat /proc/sys/fs/file-max
ulimit -n
```

#### 4. RAGFlow Integration Issues

```bash
# Test RAGFlow connection
curl -H "Authorization: Bearer your-api-key" \
     https://your-ragflow-domain.com/api/datasets

# Check network connectivity
ping your-ragflow-domain.com
telnet your-ragflow-domain.com 443

# Check API key validity
curl -X POST \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     https://your-ragflow-domain.com/api/chat \
     -d '{"dataset_id": "test", "question": "test"}'
```

### Performance Debugging

```bash
# Check system resources
htop
iotop
netstat -tulnp

# Check application performance
ps aux | grep python
ps aux | grep node

# Check database performance
sudo -u postgres psql -d mrc_documents -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC LIMIT 10;"
```

## Maintenance Procedures

### 1. Regular Maintenance Tasks

```bash
#!/bin/bash
# Daily maintenance script

# Log cleanup
find /opt/mrc/logs -name "*.log" -mtime +30 -delete

# Database maintenance
sudo -u postgres psql mrc_documents -c "VACUUM ANALYZE;"

# Cache cleanup
redis-cli --scan --pattern "cache:*" | xargs redis-cli del

# Security log rotation
logrotate /etc/logrotate.d/mrc-security
```

### 2. Application Updates

```bash
#!/bin/bash
# Application update script

# Backup current version
/opt/mrc/scripts/backup_database.sh
/opt/mrc/scripts/backup_files.sh

# Pull latest code
cd /opt/mrc/backend
sudo -u mrc-user git pull origin main

# Update dependencies
sudo -u mrc-user /opt/mrc/app/venv/bin/pip install -r requirements.txt

# Run migrations
sudo -u mrc-user /opt/mrc/app/venv/bin/python run.py db upgrade

# Restart services
sudo systemctl restart mrc-backend
sudo systemctl restart mrc-celery

# Update frontend
cd /opt/mrc/front
sudo -u mrc-user git pull origin main
sudo -u mrc-user npm install
sudo -u mrc-user npm run build

# Restart frontend service
sudo systemctl restart mrc-frontend
sudo systemctl restart nginx
```

### 3. Security Updates

```bash
#!/bin/bash
# Security update script

# Update system packages
sudo apt update && sudo apt upgrade -y

# Update virus definitions
sudo freshclam

# Update SSL certificates
sudo certbot renew --quiet

# Review security logs
grep "WARNING\|ERROR" /opt/mrc/logs/security.log | tail -20
```

## Deployment Checklist

### Pre-Deployment Checklist

- [ ] Infrastructure requirements met (CPU, RAM, Storage)
- [ ] All required software installed and configured
- [ ] Database created and migrated
- [ ] RAGFlow instance configured and tested
- [ ] SSL certificates installed and valid
- [ ] Security headers and hardening applied
- [ ] Monitoring and logging configured
- [ ] Backup procedures tested
- [ ] Load testing completed successfully
- [ ] Security review passed

### Post-Deployment Checklist

- [ ] All services running and healthy
- [ ] Application accessible via HTTPS
- [ ] Database connections working
- [ ] RAGFlow integration functional
- [ ] File uploads working correctly
- [ ] Search functionality operational
- [ ] Monitoring metrics available
- [ ] Logs being generated correctly
- [ ] Health checks passing
- [ ] Documentation updated

This deployment guide provides a comprehensive framework for deploying the Knowledge Base Document Management system to production environments. Regular maintenance and monitoring will ensure continued reliable operation.