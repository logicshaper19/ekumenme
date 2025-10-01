# MesParcelles Data Deletion Guide

## 🎯 Purpose

This guide explains how to safely delete all MesParcelles data from the database while preserving EPHY regulatory data.

## ⚠️ Important Notes

- **This operation is IRREVERSIBLE** - all MesParcelles data will be permanently deleted
- **EPHY regulatory data is preserved** - only MesParcelles farm operations and reference data is deleted
- **Database structure is preserved** - only data is deleted, not tables or schemas

## 📊 What Gets Deleted

### Farm Operations Data (farm_operations schema)
- ✅ Interventions and related data (intrants, extrants, prestataires, materiels)
- ✅ Parcelles (plots/fields)
- ✅ Succession cultures (crop rotations)
- ✅ Cultures intermediaires (intermediate crops)
- ✅ Exploitations (farms/enterprises)
- ✅ Service activations and permissions
- ✅ Conformité réglementaire (regulatory compliance records)

### Reference Data (reference schema)
- ✅ Intrants (agricultural inputs)
- ✅ Phyto details (phytosanitary product details)
- ✅ Fertilisant details (fertilizer details)
- ✅ Types d'intervention (intervention types)
- ✅ Types d'intrant (input types)
- ✅ Cultures (crops)
- ✅ Variétés cultures cépages (crop varieties)
- ✅ Regions

### What is NOT Deleted
- ❌ EPHY regulatory data (produits, substances_actives, titulaires)
- ❌ Database schemas (farm_operations, reference, regulatory)
- ❌ Table structures
- ❌ User accounts or authentication data

## 🚀 How to Use

### Step 1: Navigate to the Ekumen-assistant directory
```bash
cd /Users/elisha/ekumenme/Ekumen-assistant
```

### Step 2: Run the deletion script
```bash
python delete_mesparcelles_data.py
```

### Step 3: Review the data to be deleted
The script will show you:
- How many rows exist in each table
- Total number of rows to be deleted
- Which tables contain data

Example output:
```
🔍 Checking existing MesParcelles data...
============================================================
  📊 farm_operations.interventions: 150 rows
  📊 farm_operations.parcelles: 45 rows
  📊 farm_operations.exploitations: 10 rows
  📊 reference.cultures: 200 rows
  ...

✅ Found data in 15 tables

⚠️  WARNING: About to delete 1,234 rows from 15 tables
This action cannot be undone!
```

### Step 4: Confirm deletion
Type exactly `DELETE` (in uppercase) to confirm:
```
Type 'DELETE' to confirm deletion: DELETE
```

### Step 5: Wait for completion
The script will:
1. Delete data from all tables in the correct order (respecting foreign key constraints)
2. Verify EPHY regulatory data is still intact
3. Show a summary of what was deleted

Example output:
```
🗑️  Deleting MesParcelles data...
============================================================
  ✅ farm_operations.intervention_intrants: Deleted 300 rows
  ✅ farm_operations.interventions: Deleted 150 rows
  ✅ farm_operations.parcelles: Deleted 45 rows
  ...

🔍 Verifying EPHY regulatory data is intact...
============================================================
  ✅ regulatory.produits: 15005 rows (intact)
  ✅ regulatory.substances_actives: 1335 rows (intact)
  ✅ regulatory.titulaires: 500 rows (intact)

✅ All EPHY regulatory data is intact

📊 DELETION SUMMARY
============================================================
✅ Tables cleared: 15
   - farm_operations.intervention_intrants: 300 rows deleted
   - farm_operations.interventions: 150 rows deleted
   ...

✅ No errors encountered

🎉 MesParcelles data deletion complete!
```

## 🔄 After Deletion

Once deletion is complete, you can:

1. **Add new MesParcelles data** using the migration script:
   ```bash
   python migrate_mesparcelles_to_agri_db.py <source_database_url>
   ```

2. **Create sample data** for testing:
   ```bash
   python create_sample_farm_data.py
   ```

3. **Import data from CSV/JSON files** (provide the files and we'll create an import script)

## 🛡️ Safety Features

The script includes several safety features:

1. **Preview before deletion** - Shows exactly what will be deleted
2. **Confirmation required** - Must type 'DELETE' to proceed
3. **Correct deletion order** - Respects foreign key constraints
4. **EPHY data verification** - Confirms regulatory data is intact
5. **Error reporting** - Shows any issues encountered
6. **Transaction safety** - Uses database transactions for consistency

## ❌ Cancelling Deletion

To cancel the deletion:
- Press `Ctrl+C` at any time before confirming
- Type anything other than 'DELETE' when prompted
- The script will exit without deleting any data

## 🐛 Troubleshooting

### "Table does not exist" errors
- This is normal if some tables haven't been created yet
- The script will skip non-existent tables

### Foreign key constraint errors
- The script deletes in the correct order to avoid this
- If you see this error, please report it

### Connection errors
- Make sure PostgreSQL is running
- Check your database credentials in `env.local`
- Verify the database URL is correct

### EPHY data missing after deletion
- This should NOT happen - the script only touches MesParcelles tables
- If this occurs, restore from backup immediately

## 📝 Next Steps

After deleting the data, you mentioned you'll provide new data to add. Please provide:

1. **Data format**: CSV, JSON, SQL dump, or API endpoint?
2. **Data structure**: What tables/entities are included?
3. **Data volume**: How many records approximately?
4. **Special requirements**: Any specific transformations or validations needed?

I'll create a custom import script based on your data format.

## 🔗 Related Scripts

- `migrate_mesparcelles_to_agri_db.py` - Migrate data from another database
- `create_mesparcelles_schema.py` - Create MesParcelles schema structure
- `create_sample_farm_data.py` - Generate sample farm data for testing
- `check_mesparcelles_data.py` - Check existing MesParcelles data

## 📞 Support

If you encounter any issues:
1. Check the error messages in the script output
2. Verify database connection settings
3. Ensure PostgreSQL is running
4. Check database logs for more details

