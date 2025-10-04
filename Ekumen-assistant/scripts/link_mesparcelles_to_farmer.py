#!/usr/bin/env python3
"""
Link MesParcelles data to farmer@test.com - Dourdan Farm
This script will:
1. Update the exploitation SIRET to match the farmer's organization
2. Update all related parcelles and interventions
3. Ensure the farmer has proper access to the data
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from sqlalchemy import text

def link_mesparcelles_to_farmer():
    """Link MesParcelles data to farmer@test.com"""
    
    db = SessionLocal()
    
    try:
        print("🚀 Linking MesParcelles data to farmer@test.com...")
        print("=" * 60)
        
        # Current SIRETs
        old_siret = "93429231900019"  # Current MesParcelles SIRET
        new_siret = "12345678901234"  # Farmer's organization SIRET
        
        # Update in correct order to avoid foreign key constraints
        # 1. First, create the new exploitation record
        print(f"📝 Creating new exploitation record for SIRET {new_siret}...")
        
        # Check if new exploitation already exists
        result = db.execute(text("SELECT COUNT(*) FROM exploitations WHERE siret = :siret"), {'siret': new_siret})
        if result.scalar() == 0:
            # Get the old exploitation data
            result = db.execute(text("SELECT * FROM exploitations WHERE siret = :siret"), {'siret': old_siret})
            old_exploitation = result.first()
            
            if old_exploitation:
                # Create new exploitation with farmer's SIRET
                db.execute(text("""
                    INSERT INTO exploitations (siret, nom, region_code, department_code, commune_insee, 
                                             surface_totale_ha, type_exploitation, bio, certification_bio, 
                                             date_certification_bio, extra_data, created_at, updated_at)
                    VALUES (:siret, 'Dourdan Farm', :region_code, :department_code, :commune_insee,
                            :surface_totale_ha, :type_exploitation, :bio, :certification_bio,
                            :date_certification_bio, :extra_data, NOW(), NOW())
                """), {
                    'siret': new_siret,
                    'region_code': old_exploitation.region_code,
                    'department_code': old_exploitation.department_code,
                    'commune_insee': old_exploitation.commune_insee,
                    'surface_totale_ha': old_exploitation.surface_totale_ha,
                    'type_exploitation': old_exploitation.type_exploitation,
                    'bio': old_exploitation.bio,
                    'certification_bio': old_exploitation.certification_bio,
                    'date_certification_bio': old_exploitation.date_certification_bio,
                    'extra_data': old_exploitation.extra_data
                })
                print(f"✅ Created new exploitation: Dourdan Farm (SIRET: {new_siret})")
            else:
                print("⚠️  No old exploitation found to copy from")
        else:
            print(f"✅ Exploitation with SIRET {new_siret} already exists")
        
        # 2. Update parcelles SIRET
        print(f"📝 Updating parcelles SIRET from {old_siret} to {new_siret}...")
        result = db.execute(text("""
            UPDATE parcelles 
            SET siret = :new_siret
            WHERE siret = :old_siret
        """), {'new_siret': new_siret, 'old_siret': old_siret})
        
        if result.rowcount > 0:
            print(f"✅ Updated parcelles: {result.rowcount} record(s)")
        else:
            print("⚠️  No parcelles found to update")
        
        # 3. Update interventions SIRET
        print(f"📝 Updating interventions SIRET from {old_siret} to {new_siret}...")
        result = db.execute(text("""
            UPDATE interventions 
            SET siret = :new_siret
            WHERE siret = :old_siret
        """), {'new_siret': new_siret, 'old_siret': old_siret})
        
        if result.rowcount > 0:
            print(f"✅ Updated interventions: {result.rowcount} record(s)")
        else:
            print("⚠️  No interventions found to update")
        
        # 4. Delete old exploitation (now that all references are updated)
        print(f"📝 Deleting old exploitation SIRET {old_siret}...")
        result = db.execute(text("DELETE FROM exploitations WHERE siret = :siret"), {'siret': old_siret})
        
        if result.rowcount > 0:
            print(f"✅ Deleted old exploitation: {result.rowcount} record(s)")
        else:
            print("⚠️  No old exploitation found to delete")
        
        # 4. Ensure farmer has access to the farm
        print(f"📝 Ensuring farmer has access to farm SIRET {new_siret}...")
        
        # Check if access already exists
        result = db.execute(text("""
            SELECT COUNT(*) FROM organization_farm_access ofa
            JOIN organizations o ON ofa.organization_id = o.id
            JOIN organization_memberships om ON o.id = om.organization_id
            JOIN users u ON om.user_id = u.id
            WHERE u.email = 'farmer@test.com' AND ofa.farm_siret = :farm_siret
        """), {'farm_siret': new_siret})
        
        access_exists = result.scalar() > 0
        
        if not access_exists:
            # Get farmer's organization ID
            result = db.execute(text("""
                SELECT o.id FROM organizations o
                JOIN organization_memberships om ON o.id = om.organization_id
                JOIN users u ON om.user_id = u.id
                WHERE u.email = 'farmer@test.com' AND om.role = 'OWNER'
                LIMIT 1
            """))
            
            org_id = result.scalar()
            if org_id:
                # Create farm access
                db.execute(text("""
                    INSERT INTO organization_farm_access (id, organization_id, farm_siret, access_type, is_active, granted_at)
                    VALUES (gen_random_uuid(), :org_id, :farm_siret, 'OWNER', true, NOW())
                """), {'org_id': org_id, 'farm_siret': new_siret})
                
                print(f"✅ Created farm access for farmer's organization")
            else:
                print("⚠️  Could not find farmer's organization")
        else:
            print(f"✅ Farmer already has access to farm SIRET {new_siret}")
        
        # Commit all changes
        db.commit()
        
        # 5. Verify the changes
        print("\n" + "=" * 60)
        print("🔍 Verifying changes...")
        print("=" * 60)
        
        # Check exploitation
        result = db.execute(text("SELECT nom FROM exploitations WHERE siret = :siret"), {'siret': new_siret})
        exploitation = result.first()
        if exploitation:
            print(f"✅ Exploitation: {exploitation.nom} (SIRET: {new_siret})")
        
        # Check parcelles
        result = db.execute(text("SELECT COUNT(*) FROM parcelles WHERE siret = :siret"), {'siret': new_siret})
        parcelle_count = result.scalar()
        print(f"✅ Parcelles: {parcelle_count} found")
        
        # Check interventions
        result = db.execute(text("SELECT COUNT(*) FROM interventions WHERE siret = :siret"), {'siret': new_siret})
        intervention_count = result.scalar()
        print(f"✅ Interventions: {intervention_count} found")
        
        # Check farmer access
        result = db.execute(text("""
            SELECT o.name, ofa.access_type
            FROM organization_farm_access ofa
            JOIN organizations o ON ofa.organization_id = o.id
            JOIN organization_memberships om ON o.id = om.organization_id
            JOIN users u ON om.user_id = u.id
            WHERE u.email = 'farmer@test.com' AND ofa.farm_siret = :farm_siret
        """), {'farm_siret': new_siret})
        
        access = result.first()
        if access:
            print(f"✅ Farmer access: {access.access_type} access to {access.name}")
        
        print("\n" + "=" * 60)
        print("🎉 MesParcelles data successfully linked to farmer@test.com!")
        print("=" * 60)
        print(f"Farm: Dourdan Farm (SIRET: {new_siret})")
        print(f"Parcelles: {parcelle_count}")
        print(f"Interventions: {intervention_count}")
        print(f"Access: {access.access_type if access else 'None'}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error linking data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    link_mesparcelles_to_farmer()
