# Deployment Guide

**Last Updated:** 2025-10-01  
**Status:** Production Ready

---

## Prerequisites

### System Requirements
- **OS:** Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Python:** 3.9 or higher
- **PostgreSQL:** 14 or higher
- **Redis:** 7 or higher (optional but recommended)
- **Memory:** 4GB minimum, 8GB recommended
- **Storage:** 10GB minimum

### Required API Keys
- **OpenAI API Key** (required) - GPT-4 access
- **Tavily API Key** (optional) - For supplier/internet agents
- **Weather API Key** (optional) - For weather tools

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/logicshaper19/ekumenme.git
cd ekumenme/Ekumen-assistant
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Setup PostgreSQL

```bash
# Install PostgreSQL (Ubuntu)
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE ekumen_assistant;
CREATE USER ekumen_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ekumen_assistant TO ekumen_user;
\q
```

### 5. Setup Redis (Optional)

```bash
# Install Redis (Ubuntu)
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis
```

### 6. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required `.env` variables:**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://ekumen_user:your_password@localhost/ekumen_assistant

# OpenAI
OPENAI_API_KEY=sk-...

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Tavily (optional)
TAVILY_API_KEY=tvly-...

# Weather API (optional)
WEATHER_API_KEY=...
WEATHER_API_URL=https://api.openweathermap.org/data/2.5

# Application
SECRET_KEY=your-secret-key-here
DEBUG=True
ENVIRONMENT=development
```

### 7. Run Database Migrations

```bash
# Initialize database
alembic upgrade head
```

### 8. Start Application

```bash
# Development server with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or production server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 9. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"Ekumen Assistant","version":"1.0.0"}

# Run critical import tests
python tests/test_critical_imports.py
```

---

## Production Deployment

### Option 1: Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://ekumen_user:password@db/ekumen_assistant
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=ekumen_assistant
      - POSTGRES_USER=ekumen_user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

#### 3. Deploy

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down
```

---

### Option 2: Cloud Deployment (AWS/GCP/Azure)

#### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.9 ekumen-assistant

# Create environment
eb create ekumen-prod

# Deploy
eb deploy

# Open application
eb open
```

#### Google Cloud Run

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/ekumen-assistant

# Deploy
gcloud run deploy ekumen-assistant \
  --image gcr.io/PROJECT_ID/ekumen-assistant \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure App Service

```bash
# Create resource group
az group create --name ekumen-rg --location eastus

# Create app service plan
az appservice plan create --name ekumen-plan --resource-group ekumen-rg --sku B1 --is-linux

# Create web app
az webapp create --resource-group ekumen-rg --plan ekumen-plan --name ekumen-assistant --runtime "PYTHON|3.9"

# Deploy
az webapp up --name ekumen-assistant
```

---

### Option 3: VPS Deployment (DigitalOcean, Linode, etc.)

#### 1. Setup Server

```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt-get update && apt-get upgrade -y

# Install dependencies
apt-get install -y python3.9 python3.9-venv postgresql redis-server nginx
```

#### 2. Setup Application

```bash
# Create app user
useradd -m -s /bin/bash ekumen
su - ekumen

# Clone repository
git clone https://github.com/logicshaper19/ekumenme.git
cd ekumenme/Ekumen-assistant

# Setup virtual environment
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env
```

#### 3. Setup Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/ekumen.service
```

```ini
[Unit]
Description=Ekumen Assistant
After=network.target

[Service]
User=ekumen
Group=ekumen
WorkingDirectory=/home/ekumen/ekumenme/Ekumen-assistant
Environment="PATH=/home/ekumen/ekumenme/Ekumen-assistant/venv/bin"
ExecStart=/home/ekumen/ekumenme/Ekumen-assistant/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable ekumen
sudo systemctl start ekumen
sudo systemctl status ekumen
```

#### 4. Setup Nginx Reverse Proxy

```bash
# Create nginx config
sudo nano /etc/nginx/sites-available/ekumen
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ekumen /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 5. Setup SSL (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host/db` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `SECRET_KEY` | Application secret key | Random string |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `TAVILY_API_KEY` | Tavily API key | None |
| `WEATHER_API_KEY` | Weather API key | None |
| `DEBUG` | Debug mode | `False` |
| `ENVIRONMENT` | Environment name | `production` |
| `LOG_LEVEL` | Logging level | `INFO` |

---

## Database Migrations

### Create Migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific version
alembic upgrade <revision_id>

# Downgrade
alembic downgrade -1
```

---

## Monitoring

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db

# Redis health
curl http://localhost:8000/health/redis
```

### Logs

```bash
# Application logs
tail -f logs/app.log

# Systemd logs
sudo journalctl -u ekumen -f

# Docker logs
docker-compose logs -f app
```

---

## Backup and Recovery

### Database Backup

```bash
# Backup
pg_dump -U ekumen_user ekumen_assistant > backup_$(date +%Y%m%d).sql

# Restore
psql -U ekumen_user ekumen_assistant < backup_20251001.sql
```

### Automated Backups

```bash
# Add to crontab
0 2 * * * pg_dump -U ekumen_user ekumen_assistant > /backups/ekumen_$(date +\%Y\%m\%d).sql
```

---

## Scaling

### Horizontal Scaling

```bash
# Increase workers
uvicorn app.main:app --workers 8

# Load balancer (nginx)
upstream ekumen {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}
```

### Database Scaling

- Read replicas for read-heavy workloads
- Connection pooling (PgBouncer)
- Query optimization

### Caching

- Redis for distributed caching
- In-memory cache for local caching
- CDN for static assets

---

## Security Checklist

- [ ] Change default passwords
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall
- [ ] Limit database access
- [ ] Enable rate limiting
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] API key rotation
- [ ] Monitor access logs

---

## Troubleshooting

### Common Issues

**Database connection error:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection string
echo $DATABASE_URL
```

**Redis connection error:**
```bash
# Check Redis is running
sudo systemctl status redis

# Test connection
redis-cli ping
```

**Import errors:**
```bash
# Run critical import tests
python tests/test_critical_imports.py
```

---

## References

- [Architecture](ARCHITECTURE.md)
- [Development Guide](DEVELOPMENT.md)
- [Testing Guide](TESTING.md)

