-- Initialize database with sample data
-- This script runs when the PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Insert sample regions
INSERT INTO regions (id_region, libelle, code) VALUES 
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
(15, 'Provence-Alpes-Côte d''Azur', 'capaca'),
(16, 'Poitou-Charentes', 'capcharentes'),
(17, 'Pays de la Loire', 'capdl'),
(18, 'Rhône-Alpes', 'caralpes'),
(19, 'Luxembourg', 'calux')
ON CONFLICT (id_region) DO NOTHING;

-- Insert sample valorisation services
INSERT INTO valorisation_services (code_national, libelle, libelle_court, description) VALUES
('ECHANGE_DONNEES_VALORISATION_EXTERNE', 'Echange de données Valorisation Externe', 'Echange de données', 'Echange de données avec Valorisation Externe')
ON CONFLICT (code_national) DO NOTHING;

-- Insert sample cultures
INSERT INTO cultures (id_culture, libelle) VALUES
(17, 'fleurs pérennes'),
(35, 'blé tendre hiver'),
(71, 'colza hiver'),
(178, 'orge printemps'),
(214, 'prairie temp de 5 ans ou moins')
ON CONFLICT (id_culture) DO NOTHING;

-- Insert sample intervention types
INSERT INTO types_intervention (id_type_intervention, libelle) VALUES
(1, 'Fertilisation et amendement mineral - foliaire inclus'),
(29, 'Plantation'),
(30, 'Traitement et protection des cultures')
ON CONFLICT (id_type_intervention) DO NOTHING;

-- Insert sample intrant types
INSERT INTO types_intrant (id_type_intrant, libelle, categorie) VALUES
(6, 'Insecticides', 'P')
ON CONFLICT (id_type_intrant) DO NOTHING;

-- Insert sample intrants
INSERT INTO intrants (id_intrant, libelle, type_intrant_id, numero_amm_ephy) VALUES
(139785, 'KARATE AVEC TECHNOLOGIE ZEON', 6, '9800336')
ON CONFLICT (id_intrant) DO NOTHING;

-- Insert sample exploitation
INSERT INTO exploitations (siret) VALUES
('80240331100029')
ON CONFLICT (siret) DO NOTHING;

-- Insert sample service activation
INSERT INTO service_activation (siret, millesime_active, millesime_deja_actif) VALUES
('80240331100029', ARRAY[2024], ARRAY[2023, 2022])
ON CONFLICT (siret) DO NOTHING;
