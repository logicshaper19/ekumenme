#!/usr/bin/env python3
"""
Import EPHY data from CSV files to Supabase
"""

import csv
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from datetime import datetime
import re

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
    
    # Try different date formats
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except:
            continue
    return None

def import_titulaires(engine, csv_path):
    """Import titulaires (product holders) - using simplified ephy_products table."""
    print(f'\n📦 Extracting titulaires from {csv_path.name}...')

    # For simplified schema, we'll just track unique titulaires
    # They're stored directly in ephy_products table
    titulaires = set()

    with open(csv_path, 'r', encoding='windows-1252') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            nom = clean_value(row.get('nom titulaire AMM'))
            if nom:
                titulaires.add(nom)

    print(f'  ✅ Found {len(titulaires)} unique titulaires')
    return len(titulaires)

def import_substances(engine, csv_path):
    """Import substances actives."""
    print(f'\n🧪 Importing substances from {csv_path.name}...')
    
    count = 0
    
    with open(csv_path, 'r', encoding='windows-1252') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        with engine.connect() as conn:
            for row in reader:
                nom = clean_value(row.get('nom substance active'))
                if not nom:
                    continue
                
                try:
                    conn.execute(text("""
                        INSERT INTO substances_actives (
                            nom_substance, numero_cas, etat_autorisation
                        ) VALUES (
                            :nom, :cas, :etat
                        )
                        ON CONFLICT DO NOTHING
                    """), {
                        "nom": nom,
                        "cas": clean_value(row.get('numéro CAS')),
                        "etat": clean_value(row.get('état autorisation'))
                    })
                    count += 1
                except Exception as e:
                    print(f'  ⚠️  Error inserting substance {nom}: {e}')
            
            conn.commit()
    
    print(f'  ✅ Imported {count} substances')
    return count

def import_produits(engine, csv_path):
    """Import products."""
    print(f'\n📦 Importing products from {csv_path.name}...')
    
    count = 0
    errors = 0
    
    with open(csv_path, 'r', encoding='windows-1252') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        with engine.connect() as conn:
            for row in reader:
                numero_amm = clean_value(row.get('numéro AMM'))
                nom_produit = clean_value(row.get('nom produit'))
                
                if not numero_amm or not nom_produit:
                    continue
                
                # Get titulaire_id
                nom_titulaire = clean_value(row.get('nom titulaire AMM'))
                titulaire_id = None
                
                if nom_titulaire:
                    result = conn.execute(text(
                        "SELECT id FROM titulaires WHERE nom = :nom"
                    ), {"nom": nom_titulaire})
                    row_result = result.fetchone()
                    if row_result:
                        titulaire_id = row_result[0]
                
                # Map type_produit
                type_produit_raw = clean_value(row.get('type produit'))
                type_produit = None
                if type_produit_raw:
                    type_map = {
                        'PPP': 'PPP',
                        'MFSC': 'MFSC',
                        'Mélange': 'MELANGE',
                        'Adjuvant': 'ADJUVANT',
                        'Produit mixte': 'PRODUIT_MIXTE'
                    }
                    type_produit = type_map.get(type_produit_raw)
                
                try:
                    conn.execute(text("""
                        INSERT INTO produits (
                            numero_amm, nom_produit, type_produit, titulaire_id,
                            etat_autorisation, date_premiere_autorisation
                        ) VALUES (
                            :amm, :nom, :type::producttype, :titulaire,
                            :etat::etatautorisation, :date_auth
                        )
                        ON CONFLICT (numero_amm) DO NOTHING
                    """), {
                        "amm": numero_amm,
                        "nom": nom_produit,
                        "type": type_produit,
                        "titulaire": titulaire_id,
                        "etat": clean_value(row.get('état autorisation')),
                        "date_auth": parse_date(clean_value(row.get('date première autorisation')))
                    })
                    count += 1
                except Exception as e:
                    errors += 1
                    if errors < 5:  # Only show first 5 errors
                        print(f'  ⚠️  Error inserting product {numero_amm}: {e}')
            
            conn.commit()
    
    print(f'  ✅ Imported {count} products ({errors} errors)')
    return count

def import_usages(engine, csv_path):
    """Import product usages."""
    print(f'\n🌾 Importing usages from {csv_path.name}...')
    
    count = 0
    errors = 0
    
    with open(csv_path, 'r', encoding='windows-1252') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        with engine.connect() as conn:
            for row in reader:
                numero_amm = clean_value(row.get('numéro AMM'))
                if not numero_amm:
                    continue
                
                try:
                    conn.execute(text("""
                        INSERT INTO usages_produits (
                            numero_amm, identifiant_usage, type_culture_libelle,
                            dose_retenue, dose_retenue_unite,
                            stade_cultural_min_bbch, stade_cultural_max_bbch,
                            etat_usage, nombre_max_application
                        ) VALUES (
                            :amm, :usage, :culture,
                            :dose, :unite,
                            :bbch_min, :bbch_max,
                            :etat, :nb_max
                        )
                    """), {
                        "amm": numero_amm,
                        "usage": clean_value(row.get('identifiant usage')),
                        "culture": clean_value(row.get('libellé type culture')),
                        "dose": clean_value(row.get('dose retenue')),
                        "unite": clean_value(row.get('unité dose retenue')),
                        "bbch_min": clean_value(row.get('stade cultural min BBCH')),
                        "bbch_max": clean_value(row.get('stade cultural max BBCH')),
                        "etat": clean_value(row.get('état usage')),
                        "nb_max": clean_value(row.get('nombre max application'))
                    })
                    count += 1
                except Exception as e:
                    errors += 1
                    if errors < 5:
                        print(f'  ⚠️  Error inserting usage: {e}')
            
            conn.commit()
    
    print(f'  ✅ Imported {count} usages ({errors} errors)')
    return count

def main():
    """Main import function."""
    print('🌾 EPHY Data Import to Supabase')
    print('=' * 60)
    
    if not EPHY_DIR.exists():
        print(f'❌ EPHY directory not found: {EPHY_DIR}')
        return
    
    print(f'📁 EPHY directory: {EPHY_DIR}')
    
    engine = create_engine(SUPABASE_URL)
    
    stats = {}
    
    # Import in order (respecting foreign keys)
    csv_files = {
        'produits': 'produits_Windows-1252.csv',
        'substances': 'substance_active_Windows-1252.csv',
        'usages': 'usages_des_produits_autorises_Windows-1252.csv'
    }
    
    # 1. Import titulaires first (from products CSV)
    produits_path = EPHY_DIR / csv_files['produits']
    if produits_path.exists():
        stats['titulaires'] = import_titulaires(engine, produits_path)
    
    # 2. Import substances
    substances_path = EPHY_DIR / csv_files['substances']
    if substances_path.exists():
        stats['substances'] = import_substances(engine, substances_path)
    
    # 3. Import products
    if produits_path.exists():
        stats['produits'] = import_produits(engine, produits_path)
    
    # 4. Import usages
    usages_path = EPHY_DIR / csv_files['usages']
    if usages_path.exists():
        stats['usages'] = import_usages(engine, usages_path)
    
    # Summary
    print('\n' + '=' * 60)
    print('📊 IMPORT SUMMARY')
    print('=' * 60)
    for key, value in stats.items():
        print(f'  {key}: {value:,}')
    print('\n✅ EPHY import complete!')

if __name__ == '__main__':
    main()

