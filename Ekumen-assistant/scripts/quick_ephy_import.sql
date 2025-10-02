-- Quick EPHY Import - Essential Data Only
-- This creates simplified EPHY tables and imports sample data
-- Run this in Supabase SQL Editor

-- Create simplified EPHY tables
CREATE TABLE IF NOT EXISTS ephy_products (
    id SERIAL PRIMARY KEY,
    numero_amm VARCHAR(20) UNIQUE NOT NULL,
    nom_produit VARCHAR(300) NOT NULL,
    type_produit VARCHAR(50),
    titulaire VARCHAR(300),
    etat_autorisation VARCHAR(50),
    date_autorisation DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ephy_substances (
    id SERIAL PRIMARY KEY,
    nom_substance VARCHAR(300) NOT NULL,
    numero_cas VARCHAR(50),
    etat_autorisation VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ephy_usages (
    id SERIAL PRIMARY KEY,
    numero_amm VARCHAR(20) REFERENCES ephy_products(numero_amm),
    culture VARCHAR(200),
    dose_retenue DECIMAL(10, 4),
    dose_unite VARCHAR(20),
    bbch_min INTEGER,
    bbch_max INTEGER,
    nb_max_applications INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ephy_products_amm ON ephy_products(numero_amm);
CREATE INDEX IF NOT EXISTS idx_ephy_products_nom ON ephy_products(nom_produit);
CREATE INDEX IF NOT EXISTS idx_ephy_substances_nom ON ephy_substances(nom_substance);
CREATE INDEX IF NOT EXISTS idx_ephy_usages_amm ON ephy_usages(numero_amm);

-- Insert sample EPHY data (common French agricultural products)
INSERT INTO ephy_products (numero_amm, nom_produit, type_produit, titulaire, etat_autorisation, date_autorisation)
VALUES
    ('2000001', 'ROUNDUP FLEX', 'PPP', 'BAYER', 'Autorisé', '2020-01-15'),
    ('2000002', 'KARATE ZEON', 'PPP', 'SYNGENTA', 'Autorisé', '2019-06-20'),
    ('2000003', 'OPUS', 'PPP', 'BASF', 'Autorisé', '2021-03-10'),
    ('2000004', 'DECIS EXPERT', 'PPP', 'BAYER', 'Autorisé', '2020-09-05'),
    ('2000005', 'CALYPSO', 'PPP', 'BAYER', 'Autorisé', '2019-11-12')
ON CONFLICT (numero_amm) DO NOTHING;

INSERT INTO ephy_substances (nom_substance, numero_cas, etat_autorisation)
VALUES
    ('Glyphosate', '1071-83-6', 'Autorisé'),
    ('Lambda-cyhalothrine', '91465-08-6', 'Autorisé'),
    ('Epoxiconazole', '106325-08-0', 'Autorisé'),
    ('Deltamethrine', '52918-63-5', 'Autorisé'),
    ('Thiaclopride', '111988-49-9', 'Autorisé')
ON CONFLICT DO NOTHING;

INSERT INTO ephy_usages (numero_amm, culture, dose_retenue, dose_unite, bbch_min, bbch_max, nb_max_applications)
VALUES
    ('2000001', 'Blé', 3.0, 'L/ha', 0, 30, 1),
    ('2000002', 'Blé', 0.2, 'L/ha', 30, 60, 2),
    ('2000003', 'Blé', 1.0, 'L/ha', 30, 60, 2),
    ('2000004', 'Blé', 0.3, 'L/ha', 30, 60, 2),
    ('2000005', 'Blé', 0.2, 'L/ha', 30, 60, 1)
ON CONFLICT DO NOTHING;

-- Verify import
SELECT 
    'ephy_products' as table_name,
    COUNT(*) as count
FROM ephy_products
UNION ALL
SELECT 
    'ephy_substances' as table_name,
    COUNT(*) as count
FROM ephy_substances
UNION ALL
SELECT 
    'ephy_usages' as table_name,
    COUNT(*) as count
FROM ephy_usages;

-- Show sample data
SELECT 
    p.nom_produit,
    p.titulaire,
    p.etat_autorisation,
    COUNT(u.id) as nb_usages
FROM ephy_products p
LEFT JOIN ephy_usages u ON p.numero_amm = u.numero_amm
GROUP BY p.nom_produit, p.titulaire, p.etat_autorisation;

SELECT '✅ EPHY tables created and sample data imported!' as status;

