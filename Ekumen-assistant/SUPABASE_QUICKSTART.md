# Supabase Quick Start for Ekumen

Get up and running with Supabase in 5 minutes! 🚀

---

## Option 1: Automated Setup (Recommended)

```bash
cd Ekumen-assistant
./scripts/setup_supabase.sh
```

The script will guide you through:
1. Creating a Supabase project
2. Entering your credentials
3. Creating database tables
4. Importing sample data
5. Testing the connection

---

## Option 2: Manual Setup

### Step 1: Create Supabase Project (2 minutes)

1. Go to [https://supabase.com](https://supabase.com)
2. Click **"New Project"**
3. Fill in:
   - Name: `ekumen-agri`
   - Password: (generate and save!)
   - Region: Choose closest
4. Wait for provisioning

### Step 2: Get Connection String (1 minute)

1. **Project Settings** > **Database**
2. Copy **Connection string** (URI format)
3. Replace `[YOUR-PASSWORD]` with your actual password

Example:
```
postgresql://postgres:your_password@db.xxxxx.supabase.co:5432/postgres
```

### Step 3: Update .env File (1 minute)

```bash
# Edit Ekumen-assistant/.env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres
DATABASE_URL_SYNC=postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres

# Optional: Add Supabase API keys
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
```

### Step 4: Enable PostGIS (30 seconds)

In Supabase **SQL Editor**, run:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Step 5: Create Tables (1 minute)

```bash
cd Ekumen-assistant

# Create all tables
python -c "
from app.core.database import Base, sync_engine
from app.models import *
Base.metadata.create_all(bind=sync_engine)
print('✅ Tables created!')
"
```

### Step 6: Import Sample Data (30 seconds)

```bash
python scripts/migration/add_simple_farm_data.py
```

### Step 7: Test Connection (10 seconds)

```bash
python -c "
from app.core.database import SessionLocal
from app.models import Exploitation

db = SessionLocal()
count = db.query(Exploitation).count()
print(f'✅ Connected! Found {count} farms.')
db.close()
"
```

### Step 8: Start Your App

```bash
uvicorn app.main:app --reload
```

---

## Verify in Supabase Dashboard

1. Go to **Table Editor**
2. You should see tables:
   - `exploitations`
   - `parcelles`
   - `interventions`
   - `users`
   - `conversations`
   - etc.

3. Click on `parcelles` to see your farm data!

---

## Troubleshooting

### "Connection timeout"
- Check your IP is allowed in **Project Settings** > **Database** > **Connection pooling**
- Or add `0.0.0.0/0` for development

### "SSL certificate error"
Add `?sslmode=require` to your connection string:
```
postgresql://...postgres?sslmode=require
```

### "Too many connections"
Use the connection pooling URL instead (Transaction mode)

---

## What's Next?

### 1. **Explore Supabase Dashboard**
- **Table Editor**: View/edit data visually
- **SQL Editor**: Run custom queries
- **Authentication**: Set up user auth
- **Storage**: Upload files (parcel photos, etc.)

### 2. **Enable Real-time Updates**
Get live updates when data changes:

```python
# In your frontend or backend
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Subscribe to interventions table
def on_intervention_change(payload):
    print(f"New intervention: {payload}")

supabase.table('interventions').on('INSERT', on_intervention_change).subscribe()
```

### 3. **Set Up Row Level Security (RLS)**
Protect data so users only see their own farms:

```sql
-- Enable RLS on parcelles table
ALTER TABLE parcelles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see parcelles from their farms
CREATE POLICY "Users see own parcelles"
ON parcelles
FOR SELECT
USING (
  siret IN (
    SELECT siret FROM organization_farm_access
    WHERE user_id = auth.uid()
  )
);
```

### 4. **Use Supabase Storage**
Store parcel photos, intervention reports, etc.:

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Upload a file
with open('parcel_photo.jpg', 'rb') as f:
    supabase.storage.from_('parcels').upload('photos/tuferes.jpg', f)

# Get public URL
url = supabase.storage.from_('parcels').get_public_url('photos/tuferes.jpg')
```

---

## Migration from Local PostgreSQL

If you have existing data in local PostgreSQL:

```bash
# Export local data to JSON (backup)
python scripts/migration/migrate_to_supabase.py

# Choose option 3 (export + migrate)
```

---

## Useful Supabase SQL Queries

### View all parcelles with farm info
```sql
SELECT 
  p.nom as parcelle,
  p.surface_ha,
  p.culture_code,
  e.nom as exploitation
FROM parcelles p
JOIN exploitations e ON p.siret = e.siret;
```

### Count interventions by type
```sql
SELECT 
  type_intervention,
  COUNT(*) as count,
  SUM(surface_travaillee_ha) as total_surface_ha
FROM interventions
GROUP BY type_intervention
ORDER BY count DESC;
```

### Recent interventions
```sql
SELECT 
  i.date_intervention,
  i.type_intervention,
  i.produit_utilise,
  p.nom as parcelle
FROM interventions i
JOIN parcelles p ON i.parcelle_id = p.id
ORDER BY i.date_intervention DESC
LIMIT 10;
```

---

## Resources

- 📚 [Full Setup Guide](docs/SUPABASE_SETUP.md)
- 🌐 [Supabase Documentation](https://supabase.com/docs)
- 🐍 [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- 🗺️ [PostGIS Documentation](https://postgis.net/documentation/)

---

## Support

If you run into issues:

1. Check [docs/SUPABASE_SETUP.md](docs/SUPABASE_SETUP.md) for detailed troubleshooting
2. Visit [Supabase Discord](https://discord.supabase.com)
3. Check Supabase logs in dashboard

---

**Ready to go? Run the setup script:**

```bash
./scripts/setup_supabase.sh
```

🎉 Happy farming with Supabase!

