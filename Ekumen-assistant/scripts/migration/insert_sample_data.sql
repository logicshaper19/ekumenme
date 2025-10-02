-- Insert sample MesParcelles data into Supabase
-- Run this in Supabase SQL Editor

-- Insert Exploitation
INSERT INTO exploitations (siret, nom, commune_insee)
VALUES ('93429231900019', 'Ferme Tuferes', '75120')
ON CONFLICT (siret) DO NOTHING;

-- Insert Parcelle
INSERT INTO parcelles (
    siret, uuid_parcelle, millesime, nom, commune_insee,
    surface_ha, surface_mesuree_ha, id_culture, culture_code,
    variete, id_variete, geometrie_vide
) VALUES (
    '93429231900019',
    '60dff7b9-3183-412b-b7a2-dd6d895f181c',
    2024,
    'Tuferes',
    '75120',
    228.54,
    228.54,
    1438,
    'BLÉ',
    'Hiver',
    11438,
    false
)
ON CONFLICT (uuid_parcelle) DO NOTHING;

-- Get the parcelle ID for interventions
DO $$
DECLARE
    v_parcelle_id UUID;
BEGIN
    SELECT id INTO v_parcelle_id 
    FROM parcelles 
    WHERE uuid_parcelle = '60dff7b9-3183-412b-b7a2-dd6d895f181c';
    
    -- Insert Interventions
    INSERT INTO interventions (
        parcelle_id, siret, uuid_intervention, type_intervention,
        id_type_intervention, date_intervention, date_debut,
        surface_travaillee_ha, id_culture
    ) VALUES
    (
        v_parcelle_id,
        '93429231900019',
        '65889c18-8df3-45a0-8cf2-975037537dcb',
        'fertilisation',
        2,
        '2024-03-15',
        '2024-03-15',
        182.832,
        1438
    ),
    (
        v_parcelle_id,
        '93429231900019',
        'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
        'traitement_phytosanitaire',
        3,
        '2024-04-10',
        '2024-04-10',
        228.54,
        1438
    ),
    (
        v_parcelle_id,
        '93429231900019',
        'b2c3d4e5-f6a7-8901-bcde-f12345678901',
        'traitement_phytosanitaire',
        3,
        '2024-05-20',
        '2024-05-20',
        228.54,
        1438
    ),
    (
        v_parcelle_id,
        '93429231900019',
        'c3d4e5f6-a7b8-9012-cdef-123456789012',
        'traitement_phytosanitaire',
        3,
        '2024-06-05',
        '2024-06-05',
        228.54,
        1438
    )
    ON CONFLICT (uuid_intervention) DO NOTHING;
END $$;

-- Verify the data
SELECT 
    'exploitations' as table_name, 
    COUNT(*) as count 
FROM exploitations
UNION ALL
SELECT 
    'parcelles' as table_name, 
    COUNT(*) as count 
FROM parcelles
UNION ALL
SELECT 
    'interventions' as table_name, 
    COUNT(*) as count 
FROM interventions;

-- Show the imported data
SELECT 
    e.nom as exploitation,
    p.nom as parcelle,
    p.surface_ha,
    p.culture_code,
    p.variete,
    COUNT(i.id) as nb_interventions
FROM exploitations e
JOIN parcelles p ON e.siret = p.siret
LEFT JOIN interventions i ON p.id = i.parcelle_id
GROUP BY e.nom, p.nom, p.surface_ha, p.culture_code, p.variete;

