"""
EPHY data import service.
"""

import pandas as pd
import zipfile
import os
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.ephy import (
    Produit, SubstanceActive, Titulaire, Formulation, Fonction,
    ProduitSubstance, ProduitFonction, ProduitFormulation,
    UsageProduit, TypeCulture, PhraseRisque, ProduitPhraseRisque,
    CategorieClassification, ProduitClassification, ConditionEmploi,
    CategorieConditionEmploi, CompositionFertilisant
)
from app.core.config import settings
import structlog
from datetime import datetime
import re

logger = structlog.get_logger()


class EPHYImporter:
    """EPHY data importer service."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.import_stats = {
            "produits": 0,
            "substances": 0,
            "titulaires": 0,
            "usages": 0,
            "errors": []
        }
    
    def import_zip_file(self, zip_path: str) -> Dict[str, Any]:
        """Import EPHY data from ZIP file."""
        try:
            logger.info("Starting EPHY import", zip_path=zip_path)
            
            # Extract ZIP file
            extract_path = os.path.join(os.path.dirname(zip_path), "extracted")
            os.makedirs(extract_path, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Import each CSV file
            csv_files = [f for f in os.listdir(extract_path) if f.endswith('.csv')]
            
            for csv_file in csv_files:
                csv_path = os.path.join(extract_path, csv_file)
                self._import_csv_file(csv_path)
            
            # Clean up extracted files
            import shutil
            shutil.rmtree(extract_path)
            
            logger.info("EPHY import completed", stats=self.import_stats)
            return self.import_stats
            
        except Exception as e:
            logger.error("EPHY import failed", error=str(e))
            raise
    
    def _import_csv_file(self, csv_path: str):
        """Import a specific CSV file."""
        filename = os.path.basename(csv_path)
        logger.info("Importing CSV file", filename=filename)
        
        try:
            # Determine encoding and separator
            encoding = self._detect_encoding(csv_path)
            separator = self._detect_separator(csv_path, encoding)
            
            # Read CSV file
            df = pd.read_csv(csv_path, encoding=encoding, sep=separator, low_memory=False)
            
            # Import based on filename
            if "produits_Windows" in filename:
                self._import_produits(df)
            elif "substance_active" in filename:
                self._import_substances(df)
            elif "usages_des_produits_autorises" in filename:
                self._import_usages(df)
            elif "produits_phrases_de_risque" in filename:
                self._import_phrases_risque(df)
            elif "produits_condition_emploi" in filename:
                self._import_conditions_emploi(df)
            elif "mfsc_et_mixte_composition" in filename:
                self._import_compositions_fertilisants(df)
            else:
                logger.warning("Unknown CSV file type", filename=filename)
                
        except Exception as e:
            logger.error("Failed to import CSV file", filename=filename, error=str(e))
            self.import_stats["errors"].append({"file": filename, "error": str(e)})
    
    def _detect_encoding(self, csv_path: str) -> str:
        """Detect CSV file encoding."""
        try:
            # Try Windows-1252 first (common for French files)
            with open(csv_path, 'r', encoding='windows-1252') as f:
                f.read(1000)
            return 'windows-1252'
        except:
            try:
                # Try UTF-8
                with open(csv_path, 'r', encoding='utf-8') as f:
                    f.read(1000)
                return 'utf-8'
            except:
                # Fallback to latin-1
                return 'latin-1'
    
    def _detect_separator(self, csv_path: str, encoding: str) -> str:
        """Detect CSV separator."""
        with open(csv_path, 'r', encoding=encoding) as f:
            first_line = f.readline()
            if ';' in first_line:
                return ';'
            elif ',' in first_line:
                return ','
            else:
                return '\t'
    
    def _import_produits(self, df: pd.DataFrame):
        """Import products data."""
        logger.info("Importing products", count=len(df))
        
        for _, row in df.iterrows():
            try:
                # Get or create titulaire
                titulaire = self._get_or_create_titulaire(row.get('titulaire', ''))
                
                # Create product
                produit = Produit(
                    numero_amm=str(row.get('numero AMM', '')),
                    nom_produit=str(row.get('nom produit', '')),
                    type_produit=self._map_product_type(row.get('type produit', '')),
                    seconds_noms_commerciaux=str(row.get('seconds noms commerciaux', '')),
                    titulaire_id=titulaire.id if titulaire else None,
                    type_commercial=self._map_commercial_type(row.get('type commercial', '')),
                    gamme_usage=self._map_gamme_usage(row.get('gamme usage', '')),
                    mentions_autorisees=str(row.get('mentions autorisees', '')),
                    restrictions_usage=str(row.get('restrictions usage', '')),
                    restrictions_usage_libelle=str(row.get('restrictions usage libelle', '')),
                    etat_autorisation=self._map_etat_autorisation(row.get('Etat d\'autorisation', '')),
                    date_retrait_produit=self._parse_date(row.get('Date de retrait du produit', '')),
                    date_premiere_autorisation=self._parse_date(row.get('Date de première autorisation', '')),
                    numero_amm_reference=str(row.get('Numéro AMM du produit de référence', '')),
                    nom_produit_reference=str(row.get('Nom du produit de référence', ''))
                )
                
                # Check if product already exists
                existing = self.db.query(Produit).filter(
                    Produit.numero_amm == produit.numero_amm
                ).first()
                
                if not existing:
                    self.db.add(produit)
                    self.import_stats["produits"] += 1
                    
                    # Import related data
                    self._import_produit_substances(produit, row.get('Substances actives', ''))
                    self._import_produit_fonctions(produit, row.get('fonctions', ''))
                    self._import_produit_formulations(produit, row.get('formulations', ''))
                
            except Exception as e:
                logger.error("Failed to import product", row=row.to_dict(), error=str(e))
                self.import_stats["errors"].append({"type": "produit", "error": str(e)})
        
        self.db.commit()
    
    def _import_substances(self, df: pd.DataFrame):
        """Import active substances data."""
        logger.info("Importing substances", count=len(df))
        
        for _, row in df.iterrows():
            try:
                substance = SubstanceActive(
                    nom_substance=str(row.get('nom substance', '')),
                    numero_cas=str(row.get('numero cas', '')),
                    etat_autorisation=str(row.get('etat autorisation', '')),
                    variants=str(row.get('variants', ''))
                )
                
                # Check if substance already exists
                existing = self.db.query(SubstanceActive).filter(
                    SubstanceActive.nom_substance == substance.nom_substance
                ).first()
                
                if not existing:
                    self.db.add(substance)
                    self.import_stats["substances"] += 1
                
            except Exception as e:
                logger.error("Failed to import substance", row=row.to_dict(), error=str(e))
                self.import_stats["errors"].append({"type": "substance", "error": str(e)})
        
        self.db.commit()
    
    def _import_usages(self, df: pd.DataFrame):
        """Import product usages data."""
        logger.info("Importing usages", count=len(df))
        
        for _, row in df.iterrows():
            try:
                # Get or create type culture
                type_culture = self._get_or_create_type_culture(row.get('type culture', ''))
                
                usage = UsageProduit(
                    numero_amm=str(row.get('numero AMM', '')),
                    identifiant_usage=str(row.get('identifiant usage', '')),
                    identifiant_usage_lib_court=str(row.get('identifiant usage lib court', '')),
                    type_culture_id=type_culture.id if type_culture else None,
                    culture_commentaire=str(row.get('culture commentaire', '')),
                    dose_min_par_apport=self._parse_decimal(row.get('dose min par apport', '')),
                    dose_min_unite=str(row.get('dose min unite', '')),
                    dose_max_par_apport=self._parse_decimal(row.get('dose max par apport', '')),
                    dose_max_unite=str(row.get('dose max unite', '')),
                    dose_retenue=self._parse_decimal(row.get('dose retenue', '')),
                    dose_retenue_unite=str(row.get('dose retenue unite', '')),
                    stade_cultural_min_bbch=self._parse_int(row.get('stade cultural min bbch', '')),
                    stade_cultural_max_bbch=self._parse_int(row.get('stade cultural max bbch', '')),
                    etat_usage=self._map_etat_autorisation(row.get('etat usage', '')),
                    date_decision=self._parse_date(row.get('date decision', '')),
                    delai_avant_recolte_jour=self._parse_int(row.get('delai avant recolte jour', '')),
                    nombre_max_application=self._parse_int(row.get('nombre max application', '')),
                    condition_emploi=str(row.get('condition emploi', '')),
                    znt_aquatique_m=self._parse_decimal(row.get('znt aquatique m', '')),
                    znt_arthropodes_non_cibles_m=self._parse_decimal(row.get('znt arthropodes non cibles m', '')),
                    znt_plantes_non_cibles_m=self._parse_decimal(row.get('znt plantes non cibles m', '')),
                    mentions_autorisees_usage=str(row.get('mentions autorisees usage', '')),
                    intervalle_minimum_entre_applications_jour=self._parse_int(row.get('intervalle minimum entre applications jour', ''))
                )
                
                self.db.add(usage)
                self.import_stats["usages"] += 1
                
            except Exception as e:
                logger.error("Failed to import usage", row=row.to_dict(), error=str(e))
                self.import_stats["errors"].append({"type": "usage", "error": str(e)})
        
        self.db.commit()
    
    def _import_phrases_risque(self, df: pd.DataFrame):
        """Import risk phrases data."""
        logger.info("Importing risk phrases", count=len(df))
        
        for _, row in df.iterrows():
            try:
                phrase = PhraseRisque(
                    code=str(row.get('code', '')),
                    libelle_court=str(row.get('libelle court', '')),
                    libelle_long=str(row.get('libelle long', '')),
                    type_phrase=str(row.get('type phrase', ''))
                )
                
                # Check if phrase already exists
                existing = self.db.query(PhraseRisque).filter(
                    PhraseRisque.code == phrase.code
                ).first()
                
                if not existing:
                    self.db.add(phrase)
                
            except Exception as e:
                logger.error("Failed to import risk phrase", row=row.to_dict(), error=str(e))
        
        self.db.commit()
    
    def _import_conditions_emploi(self, df: pd.DataFrame):
        """Import usage conditions data."""
        logger.info("Importing usage conditions", count=len(df))
        
        for _, row in df.iterrows():
            try:
                # Get or create category
                categorie = self._get_or_create_categorie_condition_emploi(
                    row.get('categorie', '')
                )
                
                condition = ConditionEmploi(
                    numero_amm=str(row.get('numero AMM', '')),
                    categorie_id=categorie.id if categorie else None,
                    condition_libelle=str(row.get('condition libelle', ''))
                )
                
                self.db.add(condition)
                
            except Exception as e:
                logger.error("Failed to import usage condition", row=row.to_dict(), error=str(e))
        
        self.db.commit()
    
    def _import_compositions_fertilisants(self, df: pd.DataFrame):
        """Import fertilizer compositions data."""
        logger.info("Importing fertilizer compositions", count=len(df))
        
        for _, row in df.iterrows():
            try:
                composition = CompositionFertilisant(
                    numero_amm=str(row.get('numero AMM', '')),
                    element=str(row.get('element', '')),
                    valeur_min=self._parse_decimal(row.get('valeur min', '')),
                    valeur_max=self._parse_decimal(row.get('valeur max', '')),
                    unite=str(row.get('unite', '')),
                    type_element=str(row.get('type element', ''))
                )
                
                self.db.add(composition)
                
            except Exception as e:
                logger.error("Failed to import fertilizer composition", row=row.to_dict(), error=str(e))
        
        self.db.commit()
    
    # Helper methods
    def _get_or_create_titulaire(self, nom: str) -> Optional[Titulaire]:
        """Get or create titulaire."""
        if not nom or nom.strip() == '':
            return None
        
        titulaire = self.db.query(Titulaire).filter(Titulaire.nom == nom).first()
        if not titulaire:
            titulaire = Titulaire(nom=nom)
            self.db.add(titulaire)
            self.db.flush()
            self.import_stats["titulaires"] += 1
        
        return titulaire
    
    def _get_or_create_type_culture(self, libelle: str) -> Optional[TypeCulture]:
        """Get or create type culture."""
        if not libelle or libelle.strip() == '':
            return None
        
        type_culture = self.db.query(TypeCulture).filter(TypeCulture.libelle == libelle).first()
        if not type_culture:
            type_culture = TypeCulture(libelle=libelle)
            self.db.add(type_culture)
            self.db.flush()
        
        return type_culture
    
    def _get_or_create_categorie_condition_emploi(self, libelle: str) -> Optional[CategorieConditionEmploi]:
        """Get or create condition category."""
        if not libelle or libelle.strip() == '':
            return None
        
        categorie = self.db.query(CategorieConditionEmploi).filter(
            CategorieConditionEmploi.libelle == libelle
        ).first()
        if not categorie:
            categorie = CategorieConditionEmploi(libelle=libelle)
            self.db.add(categorie)
            self.db.flush()
        
        return categorie
    
    def _import_produit_substances(self, produit: Produit, substances_str: str):
        """Import product-substance relationships."""
        if not substances_str or substances_str.strip() == '':
            return
        
        # Parse substances string (format: "substance (name) concentration unit | ...")
        substances = substances_str.split('|')
        for substance_info in substances:
            try:
                # Extract substance name and concentration
                match = re.match(r'([^(]+)\s*\(([^)]+)\)\s*([0-9.]+)\s*([^|]*)', substance_info.strip())
                if match:
                    substance_name = match.group(1).strip()
                    concentration = float(match.group(3))
                    unit = match.group(4).strip()
                    
                    # Find substance
                    substance = self.db.query(SubstanceActive).filter(
                        SubstanceActive.nom_substance.ilike(f"%{substance_name}%")
                    ).first()
                    
                    if substance:
                        produit_substance = ProduitSubstance(
                            numero_amm=produit.numero_amm,
                            substance_id=substance.id,
                            concentration=concentration,
                            unite_concentration=unit
                        )
                        self.db.add(produit_substance)
            except Exception as e:
                logger.warning("Failed to parse substance", substance_info=substance_info, error=str(e))
    
    def _import_produit_fonctions(self, produit: Produit, fonctions_str: str):
        """Import product-function relationships."""
        if not fonctions_str or fonctions_str.strip() == '':
            return
        
        fonctions = fonctions_str.split('|')
        for fonction_name in fonctions:
            fonction_name = fonction_name.strip()
            if fonction_name:
                # Get or create fonction
                fonction = self.db.query(Fonction).filter(Fonction.libelle == fonction_name).first()
                if not fonction:
                    fonction = Fonction(libelle=fonction_name)
                    self.db.add(fonction)
                    self.db.flush()
                
                produit_fonction = ProduitFonction(
                    numero_amm=produit.numero_amm,
                    fonction_id=fonction.id
                )
                self.db.add(produit_fonction)
    
    def _import_produit_formulations(self, produit: Produit, formulations_str: str):
        """Import product-formulation relationships."""
        if not formulations_str or formulations_str.strip() == '':
            return
        
        formulations = formulations_str.split('|')
        for formulation_name in formulations:
            formulation_name = formulation_name.strip()
            if formulation_name:
                # Get or create formulation
                formulation = self.db.query(Formulation).filter(
                    Formulation.libelle == formulation_name
                ).first()
                if not formulation:
                    formulation = Formulation(libelle=formulation_name)
                    self.db.add(formulation)
                    self.db.flush()
                
                produit_formulation = ProduitFormulation(
                    numero_amm=produit.numero_amm,
                    formulation_id=formulation.id
                )
                self.db.add(produit_formulation)
    
    def _map_product_type(self, type_str: str) -> Optional[str]:
        """Map product type string to enum."""
        if not type_str:
            return None
        return "PPP" if type_str.strip().upper() == "PPP" else "MFSC"
    
    def _map_commercial_type(self, type_str: str) -> Optional[str]:
        """Map commercial type string to enum."""
        if not type_str:
            return None
        type_str = type_str.strip()
        if "référence" in type_str.lower():
            return "Produit de référence"
        elif "revente" in type_str.lower():
            return "Produit de revente"
        elif "deuxième" in type_str.lower():
            return "Deuxième gamme"
        return None
    
    def _map_gamme_usage(self, gamme_str: str) -> Optional[str]:
        """Map usage range string to enum."""
        if not gamme_str:
            return None
        gamme_str = gamme_str.strip()
        if "professionnel" in gamme_str.lower():
            return "Professionnel"
        elif "amateur" in gamme_str.lower():
            return "Amateur / emploi autorisé dans les jardins"
        return None
    
    def _map_etat_autorisation(self, etat_str: str) -> Optional[str]:
        """Map authorization status string to enum."""
        if not etat_str:
            return None
        etat_str = etat_str.strip().upper()
        if "AUTORISE" in etat_str or "AUTORISÉ" in etat_str:
            return "AUTORISE"
        elif "RETIRE" in etat_str or "RETRAIT" in etat_str:
            return "RETIRE"
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string."""
        if not date_str or date_str.strip() == '':
            return None
        
        try:
            # Try different date formats
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                try:
                    return datetime.strptime(date_str.strip(), fmt).date()
                except ValueError:
                    continue
        except:
            pass
        
        return None
    
    def _parse_decimal(self, value_str: str) -> Optional[float]:
        """Parse decimal value."""
        if not value_str or value_str.strip() == '':
            return None
        
        try:
            # Replace comma with dot for French decimal format
            value_str = value_str.replace(',', '.')
            return float(value_str.strip())
        except:
            return None
    
    def _parse_int(self, value_str: str) -> Optional[int]:
        """Parse integer value."""
        if not value_str or value_str.strip() == '':
            return None
        
        try:
            return int(value_str.strip())
        except:
            return None
    
    def close(self):
        """Close database connection."""
        self.db.close()
