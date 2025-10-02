-- EPHY (French Agricultural Product Database) Tables for Supabase
-- Run this in Supabase SQL Editor

-- Create ENUM types for EPHY
DO $$ BEGIN
    CREATE TYPE producttype AS ENUM ('PPP', 'MFSC', 'MELANGE', 'ADJUVANT', 'PRODUIT_MIXTE');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE commercialtype AS ENUM ('Produit de référence', 'Produit de revente', 'Deuxième gamme');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE gammeusage AS ENUM ('Professionnel', 'Amateur / emploi autorisé dans les jardins');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE etatautorisation AS ENUM ('AUTORISE', 'RETIRE', 'Autorisé', 'Retrait');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Titulaires (Product Holders/Manufacturers)
CREATE TABLE IF NOT EXISTS titulaires (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(300) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Substances Actives (Active Substances)
CREATE TABLE IF NOT EXISTS substances_actives (
    id SERIAL PRIMARY KEY,
    nom_substance VARCHAR(300) NOT NULL,
    numero_cas VARCHAR(50),
    etat_autorisation VARCHAR(50),
    variants TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Produits (Products)
CREATE TABLE IF NOT EXISTS produits (
    numero_amm VARCHAR(20) PRIMARY KEY,
    nom_produit VARCHAR(300) NOT NULL,
    type_produit producttype,
    seconds_noms_commerciaux TEXT,
    titulaire_id INTEGER REFERENCES titulaires(id),
    type_commercial commercialtype,
    gamme_usage gammeusage,
    mentions_autorisees TEXT,
    restrictions_usage TEXT,
    restrictions_usage_libelle TEXT,
    etat_autorisation etatautorisation,
    date_retrait_produit DATE,
    date_premiere_autorisation DATE,
    numero_amm_reference TEXT,
    nom_produit_reference TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Produit-Substance relationship (many-to-many)
CREATE TABLE IF NOT EXISTS produit_substances (
    id SERIAL PRIMARY KEY,
    numero_amm VARCHAR(20) REFERENCES produits(numero_amm) ON DELETE CASCADE,
    substance_id INTEGER REFERENCES substances_actives(id) ON DELETE CASCADE,
    concentration DECIMAL(10, 4),
    unite_concentration VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(numero_amm, substance_id)
);

-- Usages des Produits (Product Usages)
CREATE TABLE IF NOT EXISTS usages_produits (
    id SERIAL PRIMARY KEY,
    numero_amm VARCHAR(20) REFERENCES produits(numero_amm) ON DELETE CASCADE,
    identifiant_usage VARCHAR(100),
    identifiant_usage_lib_court VARCHAR(200),
    type_culture_libelle VARCHAR(200),
    culture_commentaire TEXT,
    dose_min_par_apport DECIMAL(10, 4),
    dose_min_par_apport_unite VARCHAR(20),
    dose_max_par_apport DECIMAL(10, 4),
    dose_max_par_apport_unite VARCHAR(20),
    dose_retenue DECIMAL(10, 4),
    dose_retenue_unite VARCHAR(20),
    stade_cultural_min_bbch INTEGER,
    stade_cultural_max_bbch INTEGER,
    etat_usage VARCHAR(50),
    date_decision DATE,
    saison_application_min VARCHAR(50),
    saison_application_max VARCHAR(50),
    saison_application_min_commentaire TEXT,
    saison_application_max_commentaire TEXT,
    delai_avant_recolte_jour INTEGER,
    delai_avant_recolte_bbch INTEGER,
    nombre_max_application INTEGER,
    date_fin_distribution DATE,
    date_fin_utilisation DATE,
    condition_emploi TEXT,
    znt_aquatique_m DECIMAL(6, 2),
    znt_arthropodes_non_cibles_m DECIMAL(6, 2),
    znt_plantes_non_cibles_m DECIMAL(6, 2),
    mentions_autorisees TEXT,
    intervalle_minimum_entre_applications_jour INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Phrases de Risque (Risk Phrases)
CREATE TABLE IF NOT EXISTS phrases_risque (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    libelle_court VARCHAR(100),
    libelle_long TEXT,
    type_phrase VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Produit-Phrase de Risque relationship
CREATE TABLE IF NOT EXISTS produit_phrases_risque (
    id SERIAL PRIMARY KEY,
    numero_amm VARCHAR(20) REFERENCES produits(numero_amm) ON DELETE CASCADE,
    phrase_id INTEGER REFERENCES phrases_risque(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(numero_amm, phrase_id)
);

-- Conditions d'Emploi (Usage Conditions)
CREATE TABLE IF NOT EXISTS produit_conditions_emploi (
    id SERIAL PRIMARY KEY,
    numero_amm VARCHAR(20) REFERENCES produits(numero_amm) ON DELETE CASCADE,
    condition_emploi TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Fonctions (Product Functions)
CREATE TABLE IF NOT EXISTS produit_fonctions (
    id SERIAL PRIMARY KEY,
    numero_amm VARCHAR(20) REFERENCES produits(numero_amm) ON DELETE CASCADE,
    fonction VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Formulations (Product Formulations)
CREATE TABLE IF NOT EXISTS produit_formulations (
    id SERIAL PRIMARY KEY,
    numero_amm VARCHAR(20) REFERENCES produits(numero_amm) ON DELETE CASCADE,
    formulation VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Permis de Commerce Parallèle (Parallel Trade Permits)
CREATE TABLE IF NOT EXISTS permis_commerce_parallele (
    id SERIAL PRIMARY KEY,
    numero_permis VARCHAR(50) UNIQUE NOT NULL,
    numero_amm_reference VARCHAR(20) REFERENCES produits(numero_amm),
    nom_produit VARCHAR(300),
    titulaire_permis VARCHAR(300),
    pays_origine VARCHAR(100),
    date_delivrance DATE,
    date_expiration DATE,
    etat_permis VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_produits_nom ON produits(nom_produit);
CREATE INDEX IF NOT EXISTS idx_produits_titulaire ON produits(titulaire_id);
CREATE INDEX IF NOT EXISTS idx_produits_etat ON produits(etat_autorisation);
CREATE INDEX IF NOT EXISTS idx_substances_nom ON substances_actives(nom_substance);
CREATE INDEX IF NOT EXISTS idx_usages_amm ON usages_produits(numero_amm);
CREATE INDEX IF NOT EXISTS idx_usages_culture ON usages_produits(type_culture_libelle);
CREATE INDEX IF NOT EXISTS idx_produit_substances_amm ON produit_substances(numero_amm);
CREATE INDEX IF NOT EXISTS idx_produit_substances_substance ON produit_substances(substance_id);

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ EPHY tables created successfully!';
END $$;

-- Show created tables
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name LIKE '%produit%' OR table_name LIKE '%substance%' OR table_name = 'titulaires'
ORDER BY table_name;

