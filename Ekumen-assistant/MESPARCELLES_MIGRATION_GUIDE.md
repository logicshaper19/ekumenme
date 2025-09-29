# MesParcelles to AgriDB Migration Guide

## 🎯 **Migration Objective**

Consolidate all agricultural data into a single `agri_db` database with proper schema organization, enabling seamless integration between farm operations (MesParcelles) and regulatory data (EPHY).

## 📊 **Current State Analysis**

### ✅ **AgriDB Ready State**
- **Database**: `agri_db` (PostgreSQL with PostGIS)
- **EPHY Data**: ✅ **15,005 products** + **1,335 substances** migrated
- **Schemas**: Currently using `public` schema
- **Integration Points**: AMM codes ready for cross-referencing

### 🔍 **EPHY Data Summary**
```
📈 Product Distribution:
   - PPP (Plant Protection): 13,471 products
   - MFSC (Fertilizers): 1,032 products  
   - ADJUVANT: 303 products
   - PRODUIT_MIXTE: 185 products
   - MELANGE: 13 products

🎯 Integration Ready:
   - 1,256 products authorized for gardens
   - 524 products authorized for organic farming
   - All products have AMM codes for cross-referencing
```

## 🏗️ **Target Architecture**

### **Schema Organization**
```sql
agri_db/
├── regulatory/          -- EPHY regulatory data (already migrated)
│   ├── produits
│   ├── substances_actives
│   └── titulaires
├── farm_operations/     -- MesParcelles operational data (to migrate)
│   ├── exploitations
│   ├── parcelles
│   ├── interventions
│   ├── intervention_intrants
│   ├── succession_cultures
│   ├── varietes_cultures_cepages
│   ├── consommateurs_services
│   ├── valorisation_services
│   └── service_permissions
└── reference/           -- Shared lookup tables (to migrate)
    ├── regions
    ├── cultures
    ├── types_intervention
    ├── types_intrant
    └── intrants (with AMM links)
```

### **Key Integration Points**
- `reference.intrants.code_amm` ↔ `regulatory.produits.numero_amm`
- Cross-schema foreign keys for data integrity
- Unified views for common queries

## 🚀 **Migration Process**

### **Step 1: Pre-Migration Verification**
```bash
cd Ekumen-assistant
python test_agri_db_structure.py
```

**Expected Output:**
- ✅ EPHY tables confirmed (15,005 products)
- ✅ No existing MesParcelles tables
- ✅ Integration readiness confirmed

### **Step 2: Run Migration**
```bash
python migrate_mesparcelles_to_agri_db.py <source_database_url>
```

**Example:**
```bash
# If MesParcelles is in a separate database
python migrate_mesparcelles_to_agri_db.py postgresql+asyncpg://user:pass@localhost:5432/mesparcelles

# If MesParcelles is in the same PostgreSQL instance but different database
python migrate_mesparcelles_to_agri_db.py postgresql+asyncpg://agri_user:agri_password@localhost:5432/mesparcelles_db
```

### **Step 3: Verify Migration**
The script will automatically:
1. ✅ Create schema organization (`farm_operations`, `reference`)
2. ✅ Create all MesParcelles tables with proper foreign keys
3. ✅ Migrate data in dependency order
4. ✅ Create integration views
5. ✅ Generate migration summary

## 🔗 **Integration Features**

### **Unified Views Created**

#### 1. **Product Usage with Regulatory Context**
```sql
SELECT * FROM farm_operations.product_usage_with_regulatory
WHERE date_debut >= '2024-01-01'
AND mentions_autorisees LIKE '%jardins%';
```

#### 2. **Compliance Dashboard**
```sql
SELECT * FROM farm_operations.compliance_dashboard
WHERE unknown_amm > 0;  -- Find exploitations using unregistered products
```

### **Cross-Schema Queries**
```sql
-- Find all interventions using organic-authorized products
SELECT 
    e.nom as exploitation,
    COUNT(*) as organic_interventions
FROM farm_operations.exploitations e
JOIN farm_operations.interventions i ON e.siret = i.siret_exploitation
JOIN farm_operations.intervention_intrants ii ON i.uuid_intervention = ii.uuid_intervention
JOIN reference.intrants inp ON ii.id_intrant = inp.id_intrant
JOIN regulatory.produits p ON inp.code_amm = p.numero_amm
WHERE p.mentions_autorisees LIKE '%biologique%'
GROUP BY e.siret, e.nom
ORDER BY organic_interventions DESC;
```

## 📈 **Benefits Achieved**

### **For Semantic Agricultural Agents**
- ✅ **Single Database Connection** - Better performance, simpler configuration
- ✅ **ACID Transactions** - Data consistency across farm operations and regulatory data
- ✅ **Unified Queries** - No cross-database joins needed
- ✅ **Real-time Compliance** - Instant AMM validation against EPHY data

### **For Development & Operations**
- ✅ **Simplified Architecture** - One database to maintain
- ✅ **Better Query Performance** - Optimized joins within single database
- ✅ **Unified Backup/Recovery** - Single backup strategy
- ✅ **Consistent Security Model** - One set of database permissions

### **For Business Intelligence**
- ✅ **Integrated Reporting** - Farm operations with regulatory context
- ✅ **Compliance Analytics** - Track authorization compliance across exploitations
- ✅ **Trend Analysis** - Product usage patterns with regulatory changes

## 🔧 **Post-Migration Tasks**

### **1. Update Application Connections**
```python
# Update all MesParcelles service connections to use agri_db
DATABASE_URL = "postgresql+asyncpg://agri_user:agri_password@localhost:5432/agri_db"

# Update schema references in queries
# OLD: SELECT * FROM parcelles
# NEW: SELECT * FROM farm_operations.parcelles
```

### **2. Update Semantic Tool Configurations**
```python
# Tools can now query across domains
class IntegratedComplianceTool(BaseTool):
    async def check_intervention_compliance(self, intervention_id: str):
        query = """
        SELECT p.mentions_autorisees, p.restrictions_usage
        FROM farm_operations.interventions i
        JOIN farm_operations.intervention_intrants ii ON i.uuid_intervention = ii.uuid_intervention
        JOIN reference.intrants inp ON ii.id_intrant = inp.id_intrant
        JOIN regulatory.produits p ON inp.code_amm = p.numero_amm
        WHERE i.uuid_intervention = :intervention_id
        """
```

### **3. Performance Optimization**
```sql
-- Create indexes for common cross-schema queries
CREATE INDEX idx_intrants_code_amm ON reference.intrants(code_amm);
CREATE INDEX idx_interventions_date ON farm_operations.interventions(date_debut);
CREATE INDEX idx_produits_mentions ON regulatory.produits USING gin(to_tsvector('french', mentions_autorisees));
```

## 🎉 **Success Metrics**

After migration, you should have:
- ✅ **~15,000 EPHY products** in `regulatory.produits`
- ✅ **MesParcelles operational data** in `farm_operations.*`
- ✅ **Reference data** in `reference.*` with AMM links
- ✅ **Integration views** for common queries
- ✅ **Cross-schema relationships** working correctly

## 🆘 **Troubleshooting**

### **Common Issues**

1. **Connection Errors**
   ```bash
   # Verify source database accessibility
   psql -h localhost -U user -d mesparcelles_db -c "SELECT COUNT(*) FROM exploitations;"
   ```

2. **Foreign Key Violations**
   - Migration script handles dependency order automatically
   - Check for data integrity issues in source database

3. **Schema Conflicts**
   ```sql
   -- Check for existing schema conflicts
   SELECT schema_name FROM information_schema.schemata 
   WHERE schema_name IN ('farm_operations', 'reference');
   ```

### **Rollback Strategy**
```sql
-- If migration needs to be rolled back
DROP SCHEMA IF EXISTS farm_operations CASCADE;
DROP SCHEMA IF EXISTS reference CASCADE;
-- EPHY data in regulatory schema remains intact
```

## 📞 **Support**

For migration issues:
1. Check migration logs for specific error messages
2. Verify source database structure matches expected schema
3. Ensure sufficient disk space for data duplication during migration
4. Test with a subset of data first if dealing with large datasets

---

**Ready to migrate? Run the test script first, then execute the migration!** 🚀
