# 🚀 Agricultural Backend - Quick Start Guide

## 📁 Project Structure
```
agricultural-backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── config.py          # Configuration settings
│   │   ├── database.py        # Database connection & session
│   │   ├── celery.py          # Celery configuration
│   │   └── security.py        # Authentication & JWT
│   ├── models/
│   │   ├── mesparcelles.py    # MesParcelles data models
│   │   └── ephy.py            # EPHY data models
│   ├── schemas/
│   │   ├── mesparcelles.py    # Pydantic schemas for API
│   │   └── ephy.py            # EPHY schemas
│   ├── api/v1/
│   │   ├── api.py             # API router setup
│   │   └── endpoints/         # API endpoint definitions
│   ├── services/
│   │   ├── mesparcelles_sync.py  # MesParcelles integration
│   │   ├── compliance.py         # Compliance checking
│   │   └── ephy_import.py        # EPHY data import
│   └── tasks/                 # Celery background tasks
├── docker-compose.yml         # Docker services setup
├── Dockerfile                 # Container definition
├── pyproject.toml            # Python dependencies
├── env.example               # Environment variables template
├── Makefile                  # Development shortcuts
└── scripts/                  # Utility scripts
```

## 🏃‍♂️ Quick Start

### 1. Clone and Setup
```bash
# Create project directory
mkdir agricultural-backend && cd agricultural-backend

# Copy the provided code files into the structure above
# Create .env file from env.example
cp env.example .env

# Edit .env with your actual values
nano .env
```

### 2. Start with Docker (Recommended)
```bash
# Build and start all services
make build
make up

# Or without Make:
docker-compose build
docker-compose up -d
```

### 3. Alternative: Local Development
```bash
# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Start PostgreSQL and Redis (via Docker)
docker-compose up postgres redis -d

# Run database migrations
poetry run alembic upgrade head

# Seed database with initial data
poetry run python scripts/seed_data.py

# Start FastAPI server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
poetry run celery -A app.core.celery worker --loglevel=info

# In another terminal, start Celery beat (scheduler)
poetry run celery -A app.core.celery beat --loglevel=info
```

## 🔧 Environment Variables

Create `.env` file with these variables:

```env
# Database
DATABASE_URL=postgresql://agri_user:agri_password@localhost:5432/agri_db

# Security
SECRET_KEY=your-super-secret-key-minimum-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379

# MesParcelles API
MESPARCELLES_API_URL=https://api.mesparcelles.fr/v1
MESPARCELLES_API_KEY=your-api-key-here

# Other settings
ALLOWED_HOSTS=["*"]
DEBUG=true
```

## 📊 Key Features

### ✅ What's Included

1. **Complete Database Schema**
   - MesParcelles entities (exploitations, parcelles, interventions)
   - EPHY products and compliance data
   - Full relationships and constraints

2. **REST API Endpoints**
   - CRUD operations for all entities
   - Data synchronization endpoints
   - Compliance validation
   - Background task management

3. **Background Processing**
   - Scheduled data synchronization
   - Compliance checking
   - Report generation
   - CSV import processing

4. **Docker Setup**
   - PostgreSQL database
   - Redis for caching/queues
   - FastAPI application
   - Celery workers
   - Nginx (production ready)

5. **Data Integration**
   - MesParcelles API synchronization
   - EPHY CSV import system
   - Compliance validation engine

## 🌐 API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📋 Common Operations

### Sync Data from MesParcelles
```bash
# Sync specific exploitation
curl -X POST "http://localhost:8000/api/v1/tasks/sync/exploitation/80240331100029?millesime=2024"

# Sync all exploitations
curl -X POST "http://localhost:8000/api/v1/tasks/sync/all-exploitations?millesime=2024"
```

### Import EPHY Data
```bash
# Import EPHY products from CSV
curl -X POST "http://localhost:8000/api/v1/tasks/ephy/import-csv" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/data/ephy/products.csv", "csv_type": "products"}'
```

### Check Compliance
```bash
# Validate specific intervention
curl "http://localhost:8000/api/v1/compliance/intervention/{intervention_id}"

# Check exploitation compliance
curl "http://localhost:8000/api/v1/compliance/exploitation/80240331100029?year=2024"
```

### Monitor Tasks
```bash
# Get task status
curl "http://localhost:8000/api/v1/tasks/status/{task_id}"

# List active tasks
curl "http://localhost:8000/api/v1/tasks/active"
```

## 🔍 Database Management

```bash
# Create new migration
make migration name="add_new_field"

# Run migrations
make migrate

# Backup database
make backup

# Restore from backup
make restore file=backup_20241228_120000.sql
```

## 📈 Monitoring & Logs

```bash
# View all logs
make logs

# View specific service logs
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f postgres

# Monitor Celery tasks
# Visit Flower (if configured): http://localhost:5555
```

## 🛠️ Development Workflow

1. **Add New Feature**
   ```bash
   # Create new branch
   git checkout -b feature/new-endpoint
   
   # Make changes
   # Add tests
   pytest
   
   # Format code
   make format
   
   # Run linting
   make lint
   ```

2. **Database Changes**
   ```bash
   # Modify models in app/models/
   # Generate migration
   make migration name="descriptive_name"
   
   # Review migration file
   # Apply migration
   make migrate
   ```

3. **API Changes**
   ```bash
   # Add endpoint in app/api/v1/endpoints/
   # Add schema in app/schemas/
   # Test endpoint at /docs
   ```

## 🚀 Production Deployment

1. **Environment Setup**
   ```bash
   # Use production environment variables
   export DEBUG=false
   export SECRET_KEY="strong-production-key"
   
   # Use production database
   export DATABASE_URL="postgresql://user:pass@prod-db:5432/agri_db"
   ```

2. **Start Production Services**
   ```bash
   # Start with Nginx proxy
   docker-compose --profile production up -d
   ```

3. **SSL Configuration**
   ```bash
   # Add SSL certificates to ./ssl/
   # Update nginx.conf for HTTPS
   ```

## 📞 API Examples

### Create Exploitation
```python
import httpx

response = httpx.post("http://localhost:8000/api/v1/exploitations/", json={
    "siret": "12345678901234"
})
print(response.json())
```

### Get Parcelles
```python
response = httpx.get("http://localhost:8000/api/v1/parcelles/", params={
    "siret_exploitation": "80240331100029",
    "millesime": 2024
})
print(response.json())
```

### Validate Intervention
```python
intervention_id = "92eb897c-7862-4047-902f-2644a085f2f7"
response = httpx.get(f"http://localhost:8000/api/v1/compliance/intervention/{intervention_id}")
print(response.json())
```

## 🎯 Next Steps

1. **Authentication**: Implement JWT authentication for production
2. **Authorization**: Add role-based access control
3. **Rate Limiting**: Configure API rate limits
4. **Monitoring**: Add application monitoring (Prometheus/Grafana)
5. **Testing**: Expand test coverage
6. **Documentation**: API documentation and user guides
7. **CI/CD**: Set up automated deployment pipeline

## 🆘 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres psql -U agri_user -d agri_db -c "SELECT 1;"
```

**Celery Tasks Not Running**
```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# Check worker logs
docker-compose logs worker
```

**API Not Responding**
```bash
# Check API logs
docker-compose logs api

# Verify health endpoint
curl http://localhost:8000/health
```

**Memory Issues**
```bash
# Increase Docker memory allocation
# Or run individual services
docker-compose up postgres redis -d
poetry run uvicorn app.main:app --reload
```

You now have a production-ready agricultural data management backend! 🌾✨
