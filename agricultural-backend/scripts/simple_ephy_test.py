"""
Simple EPHY import test without full backend dependencies.
"""

import os
import zipfile
import csv
import json
from pathlib import Path


def analyze_ephy_zip():
    """Analyze the EPHY ZIP file structure and content."""
    print("🔍 EPHY ZIP File Analysis")
    print("=" * 50)
    
    zip_path = "/Users/elisha/ekumenme/agricultural-backend/data/ephy/decisionamm-intrant-format-csv-20250923-windows-1252.zip"
    
    if not os.path.exists(zip_path):
        print(f"❌ ZIP file not found: {zip_path}")
        return
    
    print(f"📁 ZIP file: {os.path.basename(zip_path)}")
    print(f"📊 File size: {os.path.getsize(zip_path) / (1024*1024):.1f} MB")
    
    # Extract and analyze
    extract_path = "/Users/elisha/ekumenme/agricultural-backend/data/ephy/extracted"
    os.makedirs(extract_path, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"\n📋 Files in ZIP ({len(file_list)}):")
            
            total_size = 0
            for file_name in file_list:
                file_info = zip_ref.getinfo(file_name)
                size_mb = file_info.file_size / (1024*1024)
                total_size += file_info.file_size
                print(f"   • {file_name} ({size_mb:.1f} MB)")
            
            print(f"\n📊 Total extracted size: {total_size / (1024*1024):.1f} MB")
            
            # Extract files
            print("\n📥 Extracting files...")
            zip_ref.extractall(extract_path)
            
            # Analyze main files
            analyze_csv_files(extract_path)
            
    except Exception as e:
        print(f"❌ Error analyzing ZIP: {str(e)}")
    finally:
        # Clean up
        import shutil
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)


def analyze_csv_files(extract_path):
    """Analyze CSV files content."""
    print("\n🔍 CSV Files Analysis")
    print("=" * 50)
    
    csv_files = [f for f in os.listdir(extract_path) if f.endswith('.csv')]
    
    for csv_file in csv_files:
        csv_path = os.path.join(extract_path, csv_file)
        print(f"\n📄 {csv_file}")
        
        try:
            # Try different encodings
            encodings = ['windows-1252', 'utf-8', 'latin-1']
            df_data = None
            
            for encoding in encodings:
                try:
                    with open(csv_path, 'r', encoding=encoding) as f:
                        # Read first few lines to test encoding
                        lines = [f.readline() for _ in range(3)]
                        if lines[0]:  # Successfully read
                            print(f"   ✅ Encoding: {encoding}")
                            df_data = lines
                            break
                except UnicodeDecodeError:
                    continue
            
            if df_data:
                # Analyze structure
                header = df_data[0].strip()
                print(f"   📋 Header: {header[:100]}...")
                
                # Count columns
                separator = ';' if ';' in header else ','
                columns = header.split(separator)
                print(f"   📊 Columns: {len(columns)}")
                
                # Show first few column names
                print(f"   🏷️  First columns: {', '.join(columns[:5])}")
                
                # Count rows (approximate)
                with open(csv_path, 'r', encoding=encoding) as f:
                    row_count = sum(1 for _ in f) - 1  # Subtract header
                    print(f"   📈 Rows: ~{row_count:,}")
                
                # Show sample data
                if len(df_data) > 1:
                    sample_row = df_data[1].strip()
                    print(f"   📝 Sample: {sample_row[:100]}...")
            else:
                print(f"   ❌ Could not read file with any encoding")
                
        except Exception as e:
            print(f"   ❌ Error analyzing {csv_file}: {str(e)}")


def test_import_logic():
    """Test the import logic without database."""
    print("\n🧪 Import Logic Test")
    print("=" * 50)
    
    # Test data parsing functions
    test_data = {
        "date": "01/02/2016",
        "decimal": "400.0",
        "int": "5",
        "substances": "diméthoate (Dimethoate) 400.0 g/L | diméthoate (Dimethoate) 400.0 g/L",
        "etat": "RETIRE"
    }
    
    print("📝 Testing data parsing:")
    
    # Test date parsing
    from datetime import datetime
    try:
        date_obj = datetime.strptime(test_data["date"], '%d/%m/%Y').date()
        print(f"   ✅ Date parsing: {test_data['date']} → {date_obj}")
    except:
        print(f"   ❌ Date parsing failed: {test_data['date']}")
    
    # Test decimal parsing
    try:
        decimal_val = float(test_data["decimal"])
        print(f"   ✅ Decimal parsing: {test_data['decimal']} → {decimal_val}")
    except:
        print(f"   ❌ Decimal parsing failed: {test_data['decimal']}")
    
    # Test int parsing
    try:
        int_val = int(test_data["int"])
        print(f"   ✅ Integer parsing: {test_data['int']} → {int_val}")
    except:
        print(f"   ❌ Integer parsing failed: {test_data['int']}")
    
    # Test substance parsing
    import re
    substances = test_data["substances"].split('|')
    print(f"   📊 Substances found: {len(substances)}")
    for i, substance in enumerate(substances):
        match = re.match(r'([^(]+)\s*\(([^)]+)\)\s*([0-9.]+)\s*([^|]*)', substance.strip())
        if match:
            name = match.group(1).strip()
            concentration = float(match.group(3))
            unit = match.group(4).strip()
            print(f"      {i+1}. {name} - {concentration} {unit}")
    
    # Test status mapping
    etat_mapping = {
        "RETIRE": "RETIRE",
        "AUTORISE": "AUTORISE",
        "AUTORISÉ": "AUTORISE"
    }
    mapped_etat = etat_mapping.get(test_data["etat"], None)
    print(f"   ✅ Status mapping: {test_data['etat']} → {mapped_etat}")


def main():
    """Main test function."""
    print("🚀 Simple EPHY Import Test")
    print("=" * 60)
    
    # Analyze ZIP file
    analyze_ephy_zip()
    
    # Test import logic
    test_import_logic()
    
    print("\n🎉 Test completed!")
    print("\n📋 Next steps:")
    print("   1. Start Docker: docker-compose --profile development up -d")
    print("   2. Run full test: make test-ephy")
    print("   3. Import data: make import-ephy")


if __name__ == "__main__":
    main()
