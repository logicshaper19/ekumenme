# Scripts

This directory contains utility and migration scripts for the Ekumen Agricultural AI Assistant.

## 📁 Directory Structure

```
scripts/
├── migration/          # Database migration and data import scripts
├── utilities/          # Development and maintenance utilities
└── README.md          # This file
```

## 🗄️ Migration Scripts (scripts/migration/)

Database setup, migration, and data import scripts.

### Schema Creation

- **create_mesparcelles_schema.py**
  - Creates the MesParcelles database schema
  - Sets up regions, exploitations, parcelles, interventions tables
  - Includes SIRET-based multi-tenancy

- **check_schema.py**
  - Verifies database schema structure
  - Checks table existence and relationships

### Data Import

- **import_ephy_data.py**
  - Imports EPHY regulatory database
  - 15,005+ products, substances, autorisations
  - AMM codes for regulatory compliance

- **import_mesparcelles_json.py**
  - Imports MesParcelles data from JSON files
  - Handles regions, exploitations, parcelles, interventions
  - Supports millesime (vintage year) tracking

- **simple_ephy_import.py**
  - Simplified EPHY import script
  - Alternative to full import_ephy_data.py

### Data Migration

- **migrate_ephy_to_agri_db.py**
  - Migrates EPHY data to unified agricultural database
  - Consolidates regulatory data

- **migrate_mesparcelles_to_agri_db.py**
  - Migrates MesParcelles data to unified database
  - Preserves relationships and constraints

- **run_phase2_migration.py**
  - Executes Phase 2 migration
  - See `docs/deployment/PHASE_2_COMPLETE.md` for details

### Sample Data

- **create_sample_farm_data.py**
  - Creates sample farm data for testing
  - Generates realistic agricultural scenarios

### Data Management

- **delete_mesparcelles_data.py**
  - Safely deletes MesParcelles data
  - Preserves schema structure
  - See `docs/archive/MESPARCELLES_DATA_DELETION_GUIDE.md`

- **check_mesparcelles_data.py**
  - Verifies MesParcelles data integrity
  - Checks relationships and constraints

### Performance

- **add_performance_indexes.py**
  - Adds database indexes for performance
  - Optimizes query execution

## 🔧 Utility Scripts (scripts/utilities/)

Development and maintenance utilities for agent development.

### Agent Development

- **replicate_agent_pattern.py**
  - Replicates the 10/10 production-ready pattern across agents
  - Used to upgrade all 6 agents with sophisticated prompts
  - Usage: `python replicate_agent_pattern.py <agent_name>`
  - Example: `python replicate_agent_pattern.py planning`

- **add_react_prompts.py**
  - Adds ReAct-compatible prompts to agent prompt files
  - Creates `get_X_react_prompt()` functions
  - Includes few-shot examples and ReAct format

### Usage Examples

#### Replicate Agent Pattern
```bash
cd Ekumen-assistant/scripts/utilities
python replicate_agent_pattern.py planning
```

This will:
1. Copy the sophisticated implementation from a template agent
2. Adapt it for the target agent (planning)
3. Preserve agent-specific tools and configuration
4. Add all production-ready features

#### Add ReAct Prompts
```bash
cd Ekumen-assistant/scripts/utilities
python add_react_prompts.py
```

This will add `get_X_react_prompt()` functions to all agent prompt files.

## 🚀 Running Migration Scripts

### Initial Setup

1. **Create Schema**
   ```bash
   cd Ekumen-assistant/scripts/migration
   python create_mesparcelles_schema.py
   ```

2. **Import EPHY Data**
   ```bash
   python import_ephy_data.py
   ```

3. **Import MesParcelles Data**
   ```bash
   python import_mesparcelles_json.py
   ```

4. **Add Performance Indexes**
   ```bash
   python add_performance_indexes.py
   ```

### Migration

1. **Migrate EPHY Data**
   ```bash
   python migrate_ephy_to_agri_db.py
   ```

2. **Migrate MesParcelles Data**
   ```bash
   python migrate_mesparcelles_to_agri_db.py
   ```

3. **Run Phase 2 Migration**
   ```bash
   python run_phase2_migration.py
   ```

### Verification

```bash
python check_schema.py
python check_mesparcelles_data.py
```

## ⚠️ Important Notes

### Database Connections

All migration scripts require:
- PostgreSQL database connection
- Environment variables in `.env` file:
  - `DATABASE_URL` or individual `DB_*` variables
  - `AGRI_DB_*` variables for unified database

### Data Safety

- **Always backup before running migration scripts**
- Use `delete_mesparcelles_data.py` carefully (preserves schema but deletes data)
- Test migrations on development database first

### Agent Development

- Use `replicate_agent_pattern.py` to maintain consistency across agents
- All agents should follow the 10/10 production-ready pattern
- See `docs/AGENT_REPLICATION_COMPLETE.md` for details

## 📊 Script Status

### Migration Scripts
- ✅ All migration scripts tested and working
- ✅ EPHY database: 15,005+ products imported
- ✅ MesParcelles schema: Complete with multi-tenancy
- ✅ Performance indexes: Added and optimized

### Utility Scripts
- ✅ Agent replication: Successfully replicated across all 6 agents
- ✅ ReAct prompts: Added to all agent prompt files
- ✅ All agents: 10/10 production-ready

## 🔗 Related Documentation

- **Migration Guides:** `docs/deployment/`
- **Agent Development:** `docs/AGENT_REPLICATION_COMPLETE.md`
- **Database Architecture:** `docs/architecture/DATABASE_ARCHITECTURE_ANALYSIS.md`
- **Deployment:** `docs/deployment/DEPLOYMENT_CHECKLIST.md`

## 📝 Adding New Scripts

When adding new scripts:

1. Place in appropriate directory (migration/ or utilities/)
2. Add clear docstring explaining purpose
3. Include usage examples
4. Update this README
5. Test thoroughly before committing

---

**All scripts are production-ready and tested!** ✅

