# Supabase Setup Guide for Ekumen

This guide will help you migrate from local PostgreSQL to Supabase.

> **IMPORTANT:** For Phase 2 (Multi-Tenancy), we use **Custom JWT Authentication** (NOT Supabase Auth).
> See [KEY_DECISIONS.md](KEY_DECISIONS.md) for rationale.
> We use Supabase for **PostgreSQL database** and **Storage** only.

## Why Supabase?

- ✅ **Managed PostgreSQL** - No need to run local database
- ✅ **Storage** - File storage for knowledge base PDFs
- ✅ **Dashboard** - Visual database management
- ✅ **Free Tier** - 500MB database, 2GB bandwidth/month
- ✅ **PostGIS Support** - For geospatial data (parcelle geometries)

**NOT Using:**
- ❌ **Supabase Auth** - We use custom JWT with organization_id
- ❌ **Auto-generated APIs** - We use FastAPI
- ❌ **Real-time Subscriptions** - Not needed for our use case

---

## Step 1: Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or log in with GitHub
3. Click **"New Project"**
4. Fill in project details:
   - **Organization:** Create new or select existing
   - **Name:** `ekumen-agri` (or your preferred name)
   - **Database Password:** Generate a strong password (SAVE THIS!)
   - **Region:** Choose closest to your location
   - **Pricing Plan:** Free tier (upgrade later if needed)
5. Click **"Create new project"**
6. Wait 2-3 minutes for provisioning

---

## Step 2: Get Connection Details

### Option A: Connection String (Recommended)

1. Go to **Project Settings** (gear icon in sidebar)
2. Click **Database** in the left menu
3. Scroll to **Connection string** section
4. Select **URI** tab
5. Copy the connection string (looks like this):

```
postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

6. Replace `[YOUR-PASSWORD]` with your actual database password

### Option B: Connection Pooling (For Production)

For better performance with many connections:

1. In the same **Connection string** section
2. Select **Connection pooling** > **Transaction mode**
3. Copy the pooler connection string:

```
postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
```

---

## Step 3: Update Environment Variables

Edit your `.env` file:

```bash
# Supabase Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
DATABASE_URL_SYNC=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# Supabase Storage (for Knowledge Base PDFs)
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_SERVICE_ROLE_KEY=[YOUR-SERVICE-KEY]  # Use SERVICE ROLE, not anon key!

# Custom JWT Authentication (Phase 2)
SECRET_KEY=[GENERATE-WITH-openssl-rand-hex-32]
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**Where to find API keys:**
- Go to **Project Settings** > **API**
- Copy `URL` and `service_role` key (NOT anon key!)
- **IMPORTANT:** Use `service_role` key for backend (bypasses RLS)
- Generate `SECRET_KEY` with: `openssl rand -hex 32`

---

## Step 4: Run Database Migration

### Create Tables

```bash
cd Ekumen-assistant

# Run Alembic migrations to create all tables
alembic upgrade head
```

Or manually create tables:

```bash
python -c "
from app.core.database import Base, sync_engine
from app.models import *

print('Creating all tables in Supabase...')
Base.metadata.create_all(bind=sync_engine)
print('✅ Tables created successfully!')
"
```

### Import Sample Data

```bash
# Import MesParcelles farm data
python scripts/migration/add_simple_farm_data.py
```

---

## Step 5: Enable PostGIS (For Geometry Support)

Supabase has PostGIS pre-installed, but you need to enable it:

1. Go to **SQL Editor** in Supabase dashboard
2. Run this SQL:

```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verify it's enabled
SELECT PostGIS_version();
```

---

## Step 6: Verify Connection

Test your connection:

```bash
cd Ekumen-assistant

python -c "
from app.core.database import SessionLocal
from app.models import User

db = SessionLocal()
try:
    count = db.query(User).count()
    print(f'✅ Connected to Supabase! Found {count} users.')
except Exception as e:
    print(f'❌ Connection failed: {e}')
finally:
    db.close()
"
```

---

## Step 7: Start Your Application

```bash
cd Ekumen-assistant
uvicorn app.main:app --reload
```

Your app should now be connected to Supabase! 🎉

---

## Supabase Dashboard Features

### 1. **Table Editor**
- Visual interface to view/edit data
- Go to **Table Editor** in sidebar
- Browse your tables: `users`, `parcelles`, `interventions`, etc.

### 2. **SQL Editor**
- Run custom SQL queries
- Create views, functions, triggers
- Example: Query all parcelles

```sql
SELECT 
  p.nom,
  p.surface_ha,
  p.culture_code,
  e.nom as exploitation_nom
FROM parcelles p
JOIN exploitations e ON p.siret = e.siret;
```

### 3. **Authentication**
- Manage users
- Configure auth providers (Google, GitHub, etc.)
- Set up email templates

### 4. **Storage**
- Upload files (e.g., parcel photos, documents)
- Automatic CDN distribution

### 5. **Logs**
- View database logs
- Monitor query performance
- Debug connection issues

---

## Migration Checklist

- [ ] Create Supabase project
- [ ] Get connection string
- [ ] Update `.env` file with Supabase credentials
- [ ] Enable PostGIS extension
- [ ] Run database migrations (`alembic upgrade head`)
- [ ] Import sample data
- [ ] Test connection
- [ ] Start application
- [ ] Verify data in Supabase dashboard

---

## Troubleshooting

### Connection Timeout

If you get connection timeouts:

1. Check your IP is allowed:
   - Go to **Project Settings** > **Database**
   - Scroll to **Connection pooling**
   - Add your IP to allowlist (or use `0.0.0.0/0` for development)

### SSL Certificate Error

Add `?sslmode=require` to your connection string:

```
postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres?sslmode=require
```

### Too Many Connections

Use connection pooling URL instead of direct connection.

---

## Next Steps

1. **Set up Row Level Security (RLS)**
   - Protect data by user/farm
   - Example: Users can only see their own parcelles

2. **Enable Real-time**
   - Get live updates when interventions are added
   - Perfect for collaborative features

3. **Use Supabase Client**
   - Alternative to SQLAlchemy for some operations
   - Better integration with Supabase features

4. **Set up Backups**
   - Automatic daily backups (Pro plan)
   - Manual backups via dashboard

---

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [SQLAlchemy with Supabase](https://supabase.com/docs/guides/integrations/sqlalchemy)

