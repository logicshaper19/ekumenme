# 🌾 EPHY Data Import Guide

## 📋 Overview

The EPHY (phytosanitary products) import system allows you to import French agricultural product data from CSV files into the database. This includes products, active substances, usage conditions, and compliance information.

## 📁 File Structure

Your EPHY ZIP file contains 10 CSV files:

```
decisionamm-intrant-format-csv-20250923-windows-1252.zip
├── produits_Windows-1252.csv                    # Main products (29.9 MB)
├── substance_active_Windows-1252.csv            # Active substances (90 KB)
├── usages_des_produits_autorises_Windows-1252.csv # Product usages (7.5 MB)
├── produits_usages_Windows-1252.csv             # Detailed usages (10.9 MB)
├── produits_condition_emploi_Windows-1252.csv   # Usage conditions (11.5 MB)
├── produits_phrases_de_risque_Windows-1252.csv  # Risk phrases (751 KB)
├── produits_classe_et_mention_danger_Windows-1252.csv # Classifications (812 KB)
├── mfsc_et_mixte_composition_Windows-1252.csv   # Fertilizer compositions (342 KB)
├── mfsc_et_mixte_usage_Windows-1252.csv         # Fertilizer usages (1.1 MB)
└── permis_de_commerce_parallele_Windows-1252.csv # Import permits (345 KB)
```

## 🚀 Quick Start

### 1. Start the Backend
```bash
cd /Users/elisha/ekumenme/agricultural-backend
make up
```

### 2. Import EPHY Data
```bash
# Import via API
make import-ephy

# Or manually
curl -X POST "http://localhost:8000/api/v1/tasks/ephy/import-zip" \
  -H "Content-Type: application/json" \
  -d '{"zip_path": "/app/data/ephy/decisionamm-intrant-format-csv-20250923-windows-1252.zip"}'
```

### 3. Monitor Progress
```bash
# Get task status (replace {task_id} with actual task ID)
curl "http://localhost:8000/api/v1/tasks/status/{task_id}"

# View active tasks
curl "http://localhost:8000/api/v1/tasks/active"
```

## 🧪 Testing

### Test Import Functionality
```bash
# Run comprehensive test
make test-ephy

# Or manually
docker-compose exec api python scripts/test_ephy_import.py
```

### Test Individual Components
```bash
# Test direct import (without API)
docker-compose exec api python -c "
from app.services.ephy_import import EPHYImporter
importer = EPHYImporter()
result = importer.import_zip_file('/app/data/ephy/decisionamm-intrant-format-csv-20250923-windows-1252.zip')
print(result)
importer.close()
"
```

## 📊 Data Import Details

### Products (produits_Windows-1252.csv)
- **Size**: ~30,000 products
- **Fields**: AMM number, product name, manufacturer, authorization status, etc.
- **Relationships**: Links to substances, functions, formulations

### Active Substances (substance_active_Windows-1252.csv)
- **Size**: ~1,000 substances
- **Fields**: Substance name, CAS number, authorization status
- **Usage**: Referenced by products for composition

### Product Usages (usages_des_produits_autorises_Windows-1252.csv)
- **Size**: ~50,000 usage records
- **Fields**: Crop types, dosages, application conditions, safety measures
- **Critical**: Contains ZNT (buffer zones), harvest delays, application limits

### Risk Phrases (produits_phrases_de_risque_Windows-1252.csv)
- **Size**: ~10,000 risk phrases
- **Fields**: H-codes, P-codes, hazard descriptions
- **Usage**: Safety information for products

## 🔧 API Endpoints

### Import ZIP File
```http
POST /api/v1/tasks/ephy/import-zip
Content-Type: application/json

{
  "zip_path": "/app/data/ephy/decisionamm-intrant-format-csv-20250923-windows-1252.zip"
}
```

### Import Individual CSV
```http
POST /api/v1/tasks/ephy/import-csv
Content-Type: application/json

{
  "file_path": "/app/data/ephy/produits_Windows-1252.csv",
  "csv_type": "products"
}
```

### Get Task Status
```http
GET /api/v1/tasks/status/{task_id}
```

### Search Products
```http
GET /api/v1/ephy/search?q=KARATE
```

### Get Product Details
```http
GET /api/v1/ephy/produits/{numero_amm}
```

## 📈 Expected Results

After successful import, you should see:

```
✅ Import completed successfully!
📊 Import Statistics:
   • Products imported: ~30,000
   • Substances imported: ~1,000
   • Titulaires imported: ~500
   • Usages imported: ~50,000
   • Errors: 0
```

## 🛠️ Troubleshooting

### Common Issues

**1. Encoding Problems**
```bash
# The system automatically detects Windows-1252 encoding
# If issues persist, check file encoding:
file -i data/ephy/produits_Windows-1252.csv
```

**2. Memory Issues**
```bash
# Increase Docker memory allocation
# Or process files individually:
curl -X POST "http://localhost:8000/api/v1/tasks/ephy/import-csv" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/app/data/ephy/produits_Windows-1252.csv", "csv_type": "products"}'
```

**3. Database Connection**
```bash
# Check database health
make db-shell
# In PostgreSQL shell:
SELECT COUNT(*) FROM produits;
SELECT COUNT(*) FROM substances_actives;
```

**4. Task Monitoring**
```bash
# Check Celery worker logs
docker-compose logs worker

# Check Redis connection
docker-compose exec redis redis-cli ping
```

### Performance Optimization

**1. Batch Processing**
- The importer processes data in batches
- Large files are automatically chunked
- Progress is tracked and reported

**2. Database Optimization**
- Indexes are created for fast lookups
- Foreign key relationships are maintained
- Duplicate detection prevents re-imports

**3. Error Handling**
- Individual record errors don't stop the import
- Detailed error logging for debugging
- Rollback capability for failed imports

## 🔍 Data Validation

### Product Validation
- AMM numbers are validated for format
- Authorization status is mapped correctly
- Manufacturer information is normalized

### Usage Validation
- Dosage ranges are validated
- Crop types are standardized
- Safety conditions are parsed

### Substance Validation
- CAS numbers are validated
- Concentration units are normalized
- Active ingredient names are cleaned

## 📚 Database Schema

### Key Tables
- `produits` - Main product information
- `substances_actives` - Active ingredients
- `usages_produits` - Product usage conditions
- `phrases_risque` - Risk and safety phrases
- `conditions_emploi` - Usage conditions
- `compositions_fertilisants` - Fertilizer compositions

### Relationships
- Products → Substances (many-to-many)
- Products → Usages (one-to-many)
- Products → Risk Phrases (many-to-many)
- Products → Usage Conditions (one-to-many)

## 🎯 Next Steps

1. **Verify Import**: Check data quality and completeness
2. **Test Queries**: Ensure API endpoints work correctly
3. **Integration**: Connect with MesParcelles data
4. **Compliance**: Set up automated compliance checking
5. **Monitoring**: Implement data freshness monitoring

## 📞 Support

For issues or questions:
1. Check the logs: `docker-compose logs api worker`
2. Test individual components: `make test-ephy`
3. Verify database: `make db-shell`
4. Check API health: `make health`

The EPHY import system is now ready to handle your French agricultural product data! 🌾✨
