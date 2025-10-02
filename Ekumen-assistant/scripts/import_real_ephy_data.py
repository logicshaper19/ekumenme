#!/usr/bin/env python3
"""
Import real EPHY data from CSV files to Supabase (simplified schema)
Works with the ephy_products, ephy_substances, ephy_usages tables
"""

import csv
from pathlib import Path
from sqlalchemy import create_engine, text
from datetime import datetime

# Supabase connection
SUPABASE_URL = 'postgresql://postgres:slp225khayegA!@db.ghsfhuekuebwnrjhlitr.supabase.co:5432/postgres'

# EPHY data directory
EPHY_DIR = Path('../Ekumenbackend/data/ephy')

def clean_value(value):
    """Clean CSV value."""
    if value is None or value == '':
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == '' or value.lower() == 'null':
            return None
    return value

def parse_date(date_str):
    """Parse date from various formats."""
    if not date_str or date_str.lower() == 'null':
        return None
    
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except:
            continue
    return None

def parse_decimal(value):
    """Parse decimal value."""
    if not value:
        return None
    try:
        # Remove spaces and replace comma with dot
        value = str(value).strip().replace(' ', '').replace(',', '.')
        return float(value)
    except:
        return None

def import_products(engine, csv_path, limit=100):
    """Import products from CSV."""
    print(f'\n📦 Importing products from {csv_path.name}...')
    
    count = 0
    errors = 0
    
    with open(csv_path, 'r', encoding='windows-1252') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        with engine.connect() as conn:
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    print(f'  ⏸️  Reached limit of {limit} products')
                    break
                
                numero_amm = clean_value(row.get('numero AMM'))
                nom_produit = clean_value(row.get('nom produit'))

                if not numero_amm or not nom_produit:
                    continue

                try:
                    conn.execute(text("""
                        INSERT INTO ephy_products (
                            numero_amm, nom_produit, type_produit,
                            titulaire, etat_autorisation, date_autorisation
                        ) VALUES (
                            :amm, :nom, :type,
                            :titulaire, :etat, :date_auth
                        )
                        ON CONFLICT (numero_amm) DO UPDATE SET
                            nom_produit = EXCLUDED.nom_produit,
                            type_produit = EXCLUDED.type_produit,
                            titulaire = EXCLUDED.titulaire,
                            etat_autorisation = EXCLUDED.etat_autorisation
                    """), {
                        "amm": numero_amm,
                        "nom": nom_produit,
                        "type": clean_value(row.get('type produit')),
                        "titulaire": clean_value(row.get('titulaire')),
                        "etat": clean_value(row.get("Etat d'autorisation")),
                        "date_auth": parse_date(clean_value(row.get("Date de première autorisation")))
                    })
                    count += 1
                    
                    if count % 10 == 0:
                        print(f'  📊 Imported {count} products...', end='\r')
                        
                except Exception as e:
                    errors += 1
                    if errors < 3:
                        print(f'\n  ⚠️  Error: {e}')
            
            conn.commit()
    
    print(f'\n  ✅ Imported {count} products ({errors} errors)')
    return count

def import_substances(engine, csv_path, limit=100):
    """Import substances from CSV."""
    print(f'\n🧪 Importing substances from {csv_path.name}...')
    
    count = 0
    errors = 0
    
    with open(csv_path, 'r', encoding='windows-1252') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        with engine.connect() as conn:
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    print(f'  ⏸️  Reached limit of {limit} substances')
                    break
                
                nom = clean_value(row.get('Nom substance active'))
                if not nom:
                    continue

                try:
                    conn.execute(text("""
                        INSERT INTO ephy_substances (
                            nom_substance, numero_cas, etat_autorisation
                        ) VALUES (
                            :nom, :cas, :etat
                        )
                        ON CONFLICT DO NOTHING
                    """), {
                        "nom": nom,
                        "cas": clean_value(row.get('Numero CAS')),
                        "etat": clean_value(row.get("Etat d'autorisation"))
                    })
                    count += 1
                    
                    if count % 10 == 0:
                        print(f'  📊 Imported {count} substances...', end='\r')
                        
                except Exception as e:
                    errors += 1
                    if errors < 3:
                        print(f'\n  ⚠️  Error: {e}')
            
            conn.commit()
    
    print(f'\n  ✅ Imported {count} substances ({errors} errors)')
    return count

def import_usages(engine, csv_path, limit=500):
    """Import usages from CSV."""
    print(f'\n🌾 Importing usages from {csv_path.name}...')
    
    count = 0
    errors = 0
    
    with open(csv_path, 'r', encoding='windows-1252') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        with engine.connect() as conn:
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    print(f'  ⏸️  Reached limit of {limit} usages')
                    break
                
                numero_amm = clean_value(row.get('numero AMM'))
                if not numero_amm:
                    continue

                # Check if product exists
                result = conn.execute(text(
                    "SELECT numero_amm FROM ephy_products WHERE numero_amm = :amm"
                ), {"amm": numero_amm})

                if not result.fetchone():
                    continue  # Skip if product doesn't exist

                try:
                    conn.execute(text("""
                        INSERT INTO ephy_usages (
                            numero_amm, culture, dose_retenue, dose_unite,
                            bbch_min, bbch_max, nb_max_applications
                        ) VALUES (
                            :amm, :culture, :dose, :unite,
                            :bbch_min, :bbch_max, :nb_max
                        )
                    """), {
                        "amm": numero_amm,
                        "culture": clean_value(row.get('identifiant usage lib court')),
                        "dose": parse_decimal(clean_value(row.get('dose retenue'))),
                        "unite": clean_value(row.get('dose retenue unite')),
                        "bbch_min": clean_value(row.get('stade cultural min (BBCH)')),
                        "bbch_max": clean_value(row.get('stade cultural max (BBCH)')),
                        "nb_max": clean_value(row.get("nombre max d'application"))
                    })
                    count += 1
                    
                    if count % 50 == 0:
                        print(f'  📊 Imported {count} usages...', end='\r')
                        
                except Exception as e:
                    errors += 1
                    if errors < 3:
                        print(f'\n  ⚠️  Error: {e}')
            
            conn.commit()
    
    print(f'\n  ✅ Imported {count} usages ({errors} errors)')
    return count

def main():
    """Main import function."""
    print('🌾 Real EPHY Data Import to Supabase')
    print('=' * 60)
    
    if not EPHY_DIR.exists():
        print(f'❌ EPHY directory not found: {EPHY_DIR}')
        print('   Please check the path')
        return
    
    print(f'📁 EPHY directory: {EPHY_DIR}')
    
    engine = create_engine(SUPABASE_URL, echo=False)
    
    stats = {}
    
    # CSV files
    csv_files = {
        'produits': 'produits_Windows-1252.csv',
        'substances': 'substance_active_Windows-1252.csv',
        'usages': 'usages_des_produits_autorises_Windows-1252.csv'
    }
    
    # Import with limits (remove limits to import all)
    LIMIT_PRODUCTS = None  # Set to None to import all
    LIMIT_SUBSTANCES = None
    LIMIT_USAGES = None
    
    # 1. Import products
    produits_path = EPHY_DIR / csv_files['produits']
    if produits_path.exists():
        stats['produits'] = import_products(engine, produits_path, LIMIT_PRODUCTS)
    else:
        print(f'❌ File not found: {produits_path}')
    
    # 2. Import substances
    substances_path = EPHY_DIR / csv_files['substances']
    if substances_path.exists():
        stats['substances'] = import_substances(engine, substances_path, LIMIT_SUBSTANCES)
    else:
        print(f'❌ File not found: {substances_path}')
    
    # 3. Import usages
    usages_path = EPHY_DIR / csv_files['usages']
    if usages_path.exists():
        stats['usages'] = import_usages(engine, usages_path, LIMIT_USAGES)
    else:
        print(f'❌ File not found: {usages_path}')
    
    # Summary
    print('\n' + '=' * 60)
    print('📊 IMPORT SUMMARY')
    print('=' * 60)
    for key, value in stats.items():
        print(f'  ✅ {key}: {value:,}')
    print('\n🎉 EPHY import complete!')
    print('\nTo import ALL data, edit the script and set limits to None')

if __name__ == '__main__':
    main()

