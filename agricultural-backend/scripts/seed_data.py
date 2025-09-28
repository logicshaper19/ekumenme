"""
Seed database with initial data.
"""

import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, create_tables
from app.models.mesparcelles import (
    Region, Exploitation, Culture, TypeIntervention, 
    TypeIntrant, Intrant, ServiceActivation
)
import structlog

logger = structlog.get_logger()


def seed_regions(db: Session):
    """Seed regions data."""
    regions_data = [
        (1, 'APCA', 'apca'),
        (2, 'Alsace-Lorraine', 'caal'),
        (3, 'Aquitaine', 'caaquitaine'),
        (4, 'Auvergne', 'caauvergne'),
        (5, 'Bourgogne', 'cabourgogne'),
        (6, 'Bretagne', 'cabzh'),
        (7, 'Centre-Ile de France', 'cacentre'),
        (8, 'Champagne-Ardenne', 'cachampagne'),
        (9, 'Franche-Comté', 'cafc'),
        (10, 'Hauts-de-France', 'cahdf'),
        (11, 'Limousin', 'calimousin'),
        (12, 'Languedoc-Roussillon', 'calr'),
        (13, 'Midi-Pyrénées', 'camidipy'),
        (14, 'Normandie', 'canormandie'),
        (15, 'Provence-Alpes-Côte d\'Azur', 'capaca'),
        (16, 'Poitou-Charentes', 'capcharentes'),
        (17, 'Pays de la Loire', 'capdl'),
        (18, 'Rhône-Alpes', 'caralpes'),
        (19, 'Luxembourg', 'calux'),
    ]
    
    for id_region, libelle, code in regions_data:
        existing = db.query(Region).filter(Region.id_region == id_region).first()
        if not existing:
            region = Region(id_region=id_region, libelle=libelle, code=code)
            db.add(region)
    
    db.commit()
    logger.info("Regions seeded", count=len(regions_data))


def seed_cultures(db: Session):
    """Seed cultures data."""
    cultures_data = [
        (17, 'fleurs pérennes'),
        (35, 'blé tendre hiver'),
        (71, 'colza hiver'),
        (178, 'orge printemps'),
        (214, 'prairie temp de 5 ans ou moins'),
    ]
    
    for id_culture, libelle in cultures_data:
        existing = db.query(Culture).filter(Culture.id_culture == id_culture).first()
        if not existing:
            culture = Culture(id_culture=id_culture, libelle=libelle)
            db.add(culture)
    
    db.commit()
    logger.info("Cultures seeded", count=len(cultures_data))


def seed_intervention_types(db: Session):
    """Seed intervention types data."""
    types_data = [
        (1, 'Fertilisation et amendement mineral - foliaire inclus'),
        (29, 'Plantation'),
        (30, 'Traitement et protection des cultures'),
    ]
    
    for id_type, libelle in types_data:
        existing = db.query(TypeIntervention).filter(
            TypeIntervention.id_type_intervention == id_type
        ).first()
        if not existing:
            intervention_type = TypeIntervention(
                id_type_intervention=id_type, 
                libelle=libelle
            )
            db.add(intervention_type)
    
    db.commit()
    logger.info("Intervention types seeded", count=len(types_data))


def seed_intrant_types(db: Session):
    """Seed intrant types data."""
    types_data = [
        (6, 'Insecticides', 'P'),
    ]
    
    for id_type, libelle, categorie in types_data:
        existing = db.query(TypeIntrant).filter(
            TypeIntrant.id_type_intrant == id_type
        ).first()
        if not existing:
            intrant_type = TypeIntrant(
                id_type_intrant=id_type,
                libelle=libelle,
                categorie=categorie
            )
            db.add(intrant_type)
    
    db.commit()
    logger.info("Intrant types seeded", count=len(types_data))


def seed_intrants(db: Session):
    """Seed intrants data."""
    intrants_data = [
        (139785, 'KARATE AVEC TECHNOLOGIE ZEON', 6, '9800336'),
    ]
    
    for id_intrant, libelle, type_intrant_id, numero_amm_ephy in intrants_data:
        existing = db.query(Intrant).filter(Intrant.id_intrant == id_intrant).first()
        if not existing:
            intrant = Intrant(
                id_intrant=id_intrant,
                libelle=libelle,
                type_intrant_id=type_intrant_id,
                numero_amm_ephy=numero_amm_ephy
            )
            db.add(intrant)
    
    db.commit()
    logger.info("Intrants seeded", count=len(intrants_data))


def seed_exploitations(db: Session):
    """Seed exploitations data."""
    exploitations_data = [
        '80240331100029',
    ]
    
    for siret in exploitations_data:
        existing = db.query(Exploitation).filter(Exploitation.siret == siret).first()
        if not existing:
            exploitation = Exploitation(siret=siret)
            db.add(exploitation)
    
    db.commit()
    logger.info("Exploitations seeded", count=len(exploitations_data))


def seed_service_activations(db: Session):
    """Seed service activations data."""
    activations_data = [
        ('80240331100029', [2024], [2023, 2022]),
    ]
    
    for siret, millesime_active, millesime_deja_actif in activations_data:
        existing = db.query(ServiceActivation).filter(
            ServiceActivation.siret == siret
        ).first()
        if not existing:
            activation = ServiceActivation(
                siret=siret,
                millesime_active=millesime_active,
                millesime_deja_actif=millesime_deja_actif
            )
            db.add(activation)
    
    db.commit()
    logger.info("Service activations seeded", count=len(activations_data))


def main():
    """Main seeding function."""
    logger.info("Starting database seeding")
    
    # Create tables
    create_tables()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Seed all data
        seed_regions(db)
        seed_cultures(db)
        seed_intervention_types(db)
        seed_intrant_types(db)
        seed_intrants(db)
        seed_exploitations(db)
        seed_service_activations(db)
        
        logger.info("Database seeding completed successfully")
        
    except Exception as e:
        logger.error("Database seeding failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
