"""
Local EPHY import test without Docker dependencies.
"""

import os
import sys
import zipfile
import csv
import json
from pathlib import Path
from datetime import datetime
import re


def test_ephy_import_local():
    """Test EPHY import functionality locally."""
    print("🧪 Local EPHY Import Test")
    print("=" * 50)
    
    # Path to the EPHY ZIP file
    zip_path = "/Users/elisha/ekumenme/agricultural-backend/data/ephy/decisionamm-intrant-format-csv-20250923-windows-1252.zip"
    
    if not os.path.exists(zip_path):
        print(f"❌ ZIP file not found: {zip_path}")
        return
    
    print(f"📁 Found EPHY ZIP file: {os.path.basename(zip_path)}")
    print(f"📊 File size: {os.path.getsize(zip_path) / (1024*1024):.1f} MB")
    
    # Extract and analyze
    extract_path = "/Users/elisha/ekumenme/agricultural-backend/data/ephy/extracted"
    os.makedirs(extract_path, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"\n📋 Files in ZIP ({len(file_list)}):")
            
            for file_name in file_list:
                file_info = zip_ref.getinfo(file_name)
                size_mb = file_info.file_size / (1024*1024)
                print(f"   • {file_name} ({size_mb:.1f} MB)")
            
            # Extract files
            print("\n📥 Extracting files...")
            zip_ref.extractall(extract_path)
            
            # Test import logic on main files
            test_import_logic(extract_path)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Clean up
        import shutil
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)


def test_import_logic(extract_path):
    """Test the import logic on extracted files."""
    print("\n🔍 Testing Import Logic")
    print("=" * 50)
    
    # Test products file
    products_file = os.path.join(extract_path, "produits_Windows-1252.csv")
    if os.path.exists(products_file):
        print(f"\n📄 Testing products file: {os.path.basename(products_file)}")
        test_products_import(products_file)
    
    # Test substances file
    substances_file = os.path.join(extract_path, "substance_active_Windows-1252.csv")
    if os.path.exists(substances_file):
        print(f"\n📄 Testing substances file: {os.path.basename(substances_file)}")
        test_substances_import(substances_file)
    
    # Test usages file
    usages_file = os.path.join(extract_path, "usages_des_produits_autorises_Windows-1252.csv")
    if os.path.exists(usages_file):
        print(f"\n📄 Testing usages file: {os.path.basename(usages_file)}")
        test_usages_import(usages_file)


def test_products_import(csv_path):
    """Test products import logic."""
    try:
        # Read first few lines
        with open(csv_path, 'r', encoding='windows-1252') as f:
            lines = [f.readline().strip() for _ in range(5)]
        
        header = lines[0]
        print(f"   📋 Header: {header[:100]}...")
        
        # Parse header
        columns = header.split(';')
        print(f"   📊 Columns: {len(columns)}")
        print(f"   🏷️  First columns: {', '.join(columns[:5])}")
        
        # Test data parsing
        if len(lines) > 1:
            sample_row = lines[1]
            print(f"   📝 Sample row: {sample_row[:100]}...")
            
            # Parse sample row
            values = sample_row.split(';')
            if len(values) >= len(columns):
                print(f"   ✅ Row parsing successful")
                
                # Test specific fields
                test_field_parsing(values, columns)
            else:
                print(f"   ⚠️  Row has {len(values)} values, expected {len(columns)}")
        
        # Count total rows
        with open(csv_path, 'r', encoding='windows-1252') as f:
            row_count = sum(1 for _ in f) - 1  # Subtract header
            print(f"   📈 Total rows: {row_count:,}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


def test_substances_import(csv_path):
    """Test substances import logic."""
    try:
        with open(csv_path, 'r', encoding='windows-1252') as f:
            lines = [f.readline().strip() for _ in range(3)]
        
        header = lines[0]
        print(f"   📋 Header: {header}")
        
        columns = header.split(';')
        print(f"   📊 Columns: {len(columns)}")
        
        if len(lines) > 1:
            sample_row = lines[1]
            print(f"   📝 Sample: {sample_row}")
            
            values = sample_row.split(';')
            if len(values) >= 2:
                substance_name = values[0].strip()
                cas_number = values[1].strip()
                print(f"   ✅ Substance: {substance_name}")
                print(f"   ✅ CAS: {cas_number}")
        
        # Count rows
        with open(csv_path, 'r', encoding='windows-1252') as f:
            row_count = sum(1 for _ in f) - 1
            print(f"   📈 Total substances: {row_count:,}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


def test_usages_import(csv_path):
    """Test usages import logic."""
    try:
        with open(csv_path, 'r', encoding='windows-1252') as f:
            lines = [f.readline().strip() for _ in range(3)]
        
        header = lines[0]
        print(f"   📋 Header: {header[:100]}...")
        
        columns = header.split(';')
        print(f"   📊 Columns: {len(columns)}")
        
        if len(lines) > 1:
            sample_row = lines[1]
            print(f"   📝 Sample: {sample_row[:100]}...")
            
            values = sample_row.split(';')
            if len(values) >= 5:
                amm_number = values[1].strip()
                crop_type = values[3].strip()
                dose_min = values[5].strip()
                print(f"   ✅ AMM: {amm_number}")
                print(f"   ✅ Crop: {crop_type}")
                print(f"   ✅ Dose min: {dose_min}")
        
        # Count rows
        with open(csv_path, 'r', encoding='windows-1252') as f:
            row_count = sum(1 for _ in f) - 1
            print(f"   📈 Total usages: {row_count:,}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


def test_field_parsing(values, columns):
    """Test parsing of specific fields."""
    print(f"   🔍 Testing field parsing:")
    
    # Find key columns
    column_map = {col.strip(): i for i, col in enumerate(columns)}
    
    # Test AMM number
    if 'numero AMM' in column_map:
        amm_idx = column_map['numero AMM']
        if amm_idx < len(values):
            amm_value = values[amm_idx].strip()
            print(f"      • AMM: {amm_value}")
    
    # Test product name
    if 'nom produit' in column_map:
        name_idx = column_map['nom produit']
        if name_idx < len(values):
            name_value = values[name_idx].strip()
            print(f"      • Name: {name_value}")
    
    # Test substances
    if 'Substances actives' in column_map:
        substances_idx = column_map['Substances actives']
        if substances_idx < len(values):
            substances_value = values[substances_idx].strip()
            print(f"      • Substances: {substances_value[:50]}...")
            
            # Test substance parsing
            if substances_value:
                substances = substances_value.split('|')
                print(f"      • Found {len(substances)} substances")
                for i, substance in enumerate(substances[:2]):  # Show first 2
                    match = re.match(r'([^(]+)\s*\(([^)]+)\)\s*([0-9.]+)\s*([^|]*)', substance.strip())
                    if match:
                        name = match.group(1).strip()
                        concentration = float(match.group(3))
                        unit = match.group(4).strip()
                        print(f"        {i+1}. {name} - {concentration} {unit}")
    
    # Test authorization status
    if 'Etat d\'autorisation' in column_map:
        status_idx = column_map['Etat d\'autorisation']
        if status_idx < len(values):
            status_value = values[status_idx].strip()
            print(f"      • Status: {status_value}")
            
            # Test status mapping
            if status_value.upper() in ['AUTORISE', 'AUTORISÉ']:
                mapped_status = 'AUTORISE'
            elif status_value.upper() in ['RETIRE', 'RETRAIT']:
                mapped_status = 'RETIRE'
            else:
                mapped_status = None
            print(f"      • Mapped: {mapped_status}")


def simulate_database_import():
    """Simulate what the database import would look like."""
    print("\n🗄️  Simulating Database Import")
    print("=" * 50)
    
    # Simulate import statistics
    stats = {
        "produits": 15004,
        "substances": 1335,
        "titulaires": 500,
        "usages": 18539,
        "phrases_risque": 9034,
        "conditions_emploi": 28116,
        "errors": []
    }
    
    print("📊 Simulated Import Results:")
    for key, value in stats.items():
        if key != "errors":
            print(f"   • {key.title()}: {value:,}")
    
    print(f"   • Errors: {len(stats['errors'])}")
    
    # Simulate processing time
    total_records = sum(v for k, v in stats.items() if k != "errors")
    estimated_time = total_records / 1000  # Assume 1000 records per second
    
    print(f"\n⏱️  Estimated processing time: {estimated_time:.1f} seconds")
    print(f"📈 Total records to process: {total_records:,}")


def main():
    """Main test function."""
    print("🚀 Local EPHY Import Test Suite")
    print("=" * 60)
    
    # Test file analysis
    test_ephy_import_local()
    
    # Simulate database import
    simulate_database_import()
    
    print("\n🎉 Local test completed!")
    print("\n📋 Next steps:")
    print("   1. Fix Docker issues (storage/containerd)")
    print("   2. Start backend: make up")
    print("   3. Import data: make import-ephy")
    print("   4. Test API: make test-ephy")


if __name__ == "__main__":
    main()
