# Production Deployment Guide

This guide covers deploying the Ekumen Assistant to production with proper file storage, database, and monitoring.

## 🎯 **Production Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Supabase      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL   │
│                 │    │                 │    │    + Storage)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Redis         │
                       │   (Cache)       │
                       └─────────────────┘
```

## 🚀 **Quick Start (Production)**

### 1. **Prerequisites**

- Docker and Docker Compose
- Supabase account and project
- Domain name (optional, for SSL)

### 2. **Setup Supabase**

```bash
# 1. Create Supabase project at https://supabase.com
# 2. Get your project details:
#    - Project Reference ID
#    - Database Password
#    - Service Role Key

# 3. Enable PostGIS extension in Supabase SQL Editor:
CREATE EXTENSION IF NOT EXISTS postgis;
```

### 3. **Configure Environment**

```bash
# Copy production environment template
cp env.production.example .env

# Edit with your actual values
nano .env
```

**Required values:**
```bash
# Supabase
SUPABASE_PROJECT_REF=your-project-ref
SUPABASE_DB_PASSWORD=your-db-password
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Security
SECRET_KEY=$(openssl rand -hex 32)

# API Keys
OPENAI_API_KEY=your-openai-key
```

### 4. **Deploy**

```bash
# Deploy with production configuration
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 5. **Run Database Migrations**

```bash
# Run migrations on Supabase
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.database import Base, sync_engine
from app.models import *
Base.metadata.create_all(bind=sync_engine)
print('✅ Database tables created!')
"
```

### 6. **Verify Deployment**

```bash
# Health check
curl http://localhost:8000/health

# Test file upload (should use Supabase Storage)
curl -X POST http://localhost:8000/api/v1/knowledge-base/submit \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf" \
  -F "document_type=REGULATION"
```

---

## 📁 **File Storage Strategy**

### **Development (Local)**
```python
# Uses local filesystem
uploads/knowledge_base/{org_id}/{hash[:2]}/{hash[2:4]}/{hash}
```

### **Production (Supabase Storage)**
```python
# Uses Supabase Storage with CDN
https://your-project.supabase.co/storage/v1/object/public/knowledge-base-files/{org_id}/{hash[:2]}/{hash[2:4]}/{hash}
```

**Benefits:**
- ✅ **Persistent** - Files survive container restarts
- ✅ **Scalable** - Multiple instances can access same files
- ✅ **CDN** - Fast global access
- ✅ **Backup** - Automatic backups
- ✅ **Security** - Row-level security support

---

## 🔧 **Configuration Options**

### **Environment Variables**

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SUPABASE_URL` | ✅ | Supabase project URL | `https://abc123.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Service role key | `eyJhbGciOiJIUzI1NiIs...` |
| `DATABASE_URL` | ✅ | Database connection | `postgresql+asyncpg://postgres:pass@db.abc123.supabase.co:5432/postgres` |
| `SECRET_KEY` | ✅ | JWT secret | `openssl rand -hex 32` |
| `OPENAI_API_KEY` | ✅ | OpenAI API key | `sk-...` |
| `REDIS_URL` | ✅ | Redis connection | `redis://:pass@redis:6379` |

### **File Storage Configuration**

The system automatically chooses the right storage backend:

```python
# If Supabase is configured → Use Supabase Storage
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    storage = SupabaseStorageService()
else:
    # Fallback to local storage (development)
    storage = FileStorageService()
```

---

## 🚨 **Production Checklist**

### **Before Deployment**

- [ ] **Supabase project created** with PostGIS enabled
- [ ] **Environment variables** configured with real values
- [ ] **SSL certificates** obtained (if using custom domain)
- [ ] **Domain DNS** configured (if using custom domain)
- [ ] **API keys** obtained and configured
- [ ] **Database migrations** tested
- [ ] **File upload** tested with Supabase Storage

### **After Deployment**

- [ ] **Health check** passes (`/health` endpoint)
- [ ] **Database connection** working
- [ ] **File upload** working (check Supabase Storage dashboard)
- [ ] **Authentication** working
- [ ] **API endpoints** responding
- [ ] **Logs** being generated
- [ ] **Monitoring** configured (optional)

---

## 📊 **Monitoring & Logging**

### **Health Checks**

```bash
# Application health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db

# Storage health
curl http://localhost:8000/health/storage
```

### **Logs**

```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs -f backend

# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# Log rotation (configured in docker-compose.prod.yml)
# - Max size: 10MB per file
# - Max files: 3
```

### **Metrics (Optional)**

```bash
# Prometheus metrics (if enabled)
curl http://localhost:9090/metrics
```

---

## 🔄 **Database Migrations**

### **Automatic (Recommended)**

```bash
# Run migrations on startup
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.database import Base, sync_engine
from app.models import *
Base.metadata.create_all(bind=sync_engine)
"
```

### **Manual (Advanced)**

```bash
# Using Alembic (if configured)
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## 🛡️ **Security**

### **Environment Security**

```bash
# Generate secure secrets
SECRET_KEY=$(openssl rand -hex 32)
REDIS_PASSWORD=$(openssl rand -hex 16)

# Use strong passwords
SUPABASE_DB_PASSWORD=$(openssl rand -base64 32)
```

### **Network Security**

```bash
# Firewall rules (example)
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 8000/tcp   # Block direct backend access
```

### **SSL/TLS (Optional)**

```bash
# Using Let's Encrypt with Nginx
certbot --nginx -d your-domain.com
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. Database Connection Failed**
```bash
# Check Supabase connection
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.database import SessionLocal
db = SessionLocal()
print('✅ Database connected!')
db.close()
"
```

#### **2. File Upload Failed**
```bash
# Check Supabase Storage
# 1. Go to Supabase Dashboard > Storage
# 2. Verify bucket 'knowledge-base-files' exists
# 3. Check service role key permissions
```

#### **3. Container Won't Start**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Check environment variables
docker-compose -f docker-compose.prod.yml exec backend env | grep SUPABASE
```

#### **4. Memory Issues**
```bash
# Check resource usage
docker stats

# Adjust memory limits in docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 2G  # Increase if needed
```

---

## 📈 **Scaling**

### **Horizontal Scaling**

```bash
# Scale backend instances
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Use load balancer (Nginx, HAProxy, etc.)
```

### **Database Scaling**

- **Supabase Pro**: Automatic scaling
- **Connection pooling**: Already configured
- **Read replicas**: Available in Supabase Pro

### **Storage Scaling**

- **Supabase Storage**: Automatic scaling
- **CDN**: Built-in global distribution
- **Bandwidth**: Scales with Supabase plan

---

## 🔄 **Backup & Recovery**

### **Database Backups**

```bash
# Supabase handles automatic backups
# Manual backup (if needed)
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.database import SessionLocal
import json
# Export data logic here
"
```

### **File Backups**

- **Supabase Storage**: Automatic backups
- **Manual backup**: Download from Supabase Dashboard

### **Configuration Backups**

```bash
# Backup environment
cp .env .env.backup.$(date +%Y%m%d)

# Backup Docker Compose
cp docker-compose.prod.yml docker-compose.prod.yml.backup.$(date +%Y%m%d)
```

---

## 🎯 **Performance Optimization**

### **Database**

```sql
-- Add indexes for better performance
CREATE INDEX CONCURRENTLY idx_knowledge_base_documents_org_hash 
ON knowledge_base_documents(organization_id, file_hash);

CREATE INDEX CONCURRENTLY idx_knowledge_base_documents_created_at 
ON knowledge_base_documents(created_at);
```

### **Caching**

```python
# Redis caching is already configured
# Cache frequently accessed data
@cache(expire=3600)  # 1 hour
def get_organization_documents(org_id: str):
    # Implementation
```

### **File Storage**

```python
# Use signed URLs for private files
signed_url = storage_service.get_signed_url(file_path, expires_in=3600)
```

---

## 📞 **Support**

### **Logs & Debugging**

```bash
# Enable debug logging (temporarily)
echo "DEBUG=true" >> .env
docker-compose -f docker-compose.prod.yml restart backend

# View detailed logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### **Health Monitoring**

```bash
# Create monitoring script
#!/bin/bash
curl -f http://localhost:8000/health || echo "Health check failed!"
```

---

## 🎉 **Success!**

Your Ekumen Assistant is now running in production with:

- ✅ **Supabase PostgreSQL** - Managed database
- ✅ **Supabase Storage** - Persistent file storage
- ✅ **Redis** - Caching and sessions
- ✅ **Docker** - Containerized deployment
- ✅ **Health checks** - Monitoring
- ✅ **Logging** - Debugging support
- ✅ **Security** - Environment variables and secrets

**Next steps:**
1. Set up monitoring (Prometheus, Grafana)
2. Configure SSL/TLS certificates
3. Set up automated backups
4. Configure alerting
5. Performance testing
