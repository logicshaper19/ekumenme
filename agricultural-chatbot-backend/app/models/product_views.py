"""
Product database views and functions for agricultural chatbot
Provides optimized queries for French agricultural product data
"""

from sqlalchemy import text
from app.core.database import engine


# Database views for common product queries
PRODUCT_VIEWS = {
    "v_products_actifs": """
    CREATE OR REPLACE VIEW v_products_actifs AS
    SELECT 
        p.numero_amm,
        p.nom_produit,
        p.type_produit,
        p.etat_autorisation,
        STRING_AGG(sa.nom_substance, ', ') as substances_actives,
        STRING_AGG(CONCAT(ps.concentration_value, ps.concentration_unit), ', ') as concentrations
    FROM products p
    LEFT JOIN product_substances ps ON p.id = ps.product_id
    LEFT JOIN substances_actives sa ON ps.substance_id = sa.id
    WHERE p.etat_autorisation = 'AUTORISE'
    GROUP BY p.id, p.numero_amm, p.nom_produit, p.type_produit, p.etat_autorisation;
    """,
    
    "v_products_usage_summary": """
    CREATE OR REPLACE VIEW v_products_usage_summary AS
    SELECT 
        p.numero_amm,
        p.nom_produit,
        COUNT(u.id) as nombre_usages,
        COUNT(CASE WHEN u.etat_usage = 'Autorise' THEN 1 END) as usages_autorises,
        STRING_AGG(DISTINCT u.type_culture_libelle, ', ') as cultures
    FROM products p
    LEFT JOIN usages u ON p.id = u.product_id
    GROUP BY p.id, p.numero_amm, p.nom_produit;
    """,
    
    "v_safety_summary": """
    CREATE OR REPLACE VIEW v_safety_summary AS
    SELECT 
        p.numero_amm,
        p.nom_produit,
        COUNT(DISTINCT cd.libelle_court) as nb_classifications_danger,
        COUNT(DISTINCT pr.code_phrase) as nb_phrases_risque,
        STRING_AGG(DISTINCT cd.libelle_court, ', ') as classifications
    FROM products p
    LEFT JOIN classifications_danger cd ON p.id = cd.product_id
    LEFT JOIN phrases_risque pr ON p.id = pr.product_id
    GROUP BY p.id, p.numero_amm, p.nom_produit;
    """,
    
    "v_products_with_substances": """
    CREATE OR REPLACE VIEW v_products_with_substances AS
    SELECT 
        p.id,
        p.numero_amm,
        p.nom_produit,
        p.type_produit,
        p.etat_autorisation,
        p.titulaire,
        p.date_premiere_autorisation,
        p.date_retrait_produit,
        sa.nom_substance,
        sa.numero_cas,
        ps.concentration_value,
        ps.concentration_unit,
        ps.fonction
    FROM products p
    LEFT JOIN product_substances ps ON p.id = ps.product_id
    LEFT JOIN substances_actives sa ON ps.substance_id = sa.id
    WHERE p.etat_autorisation = 'AUTORISE';
    """,
    
    "v_usage_details": """
    CREATE OR REPLACE VIEW v_usage_details AS
    SELECT 
        p.numero_amm,
        p.nom_produit,
        u.identifiant_usage,
        u.type_culture_libelle,
        u.dose_retenue,
        u.dose_unite,
        u.nombre_max_application,
        u.delai_avant_recolte_jour,
        u.intervalle_minimum_applications_jour,
        u.znt_aquatique_m,
        u.znt_arthropodes_non_cibles_m,
        u.znt_plantes_non_cibles_m,
        u.condition_emploi,
        u.restrictions_usage_libelle,
        u.etat_usage
    FROM products p
    JOIN usages u ON p.id = u.product_id
    WHERE p.etat_autorisation = 'AUTORISE' 
    AND u.etat_usage = 'Autorise';
    """,
    
    "v_products_by_crop": """
    CREATE OR REPLACE VIEW v_products_by_crop AS
    SELECT 
        u.type_culture_libelle as culture,
        COUNT(DISTINCT p.id) as nb_produits,
        STRING_AGG(DISTINCT p.nom_produit, ', ') as produits
    FROM products p
    JOIN usages u ON p.id = u.product_id
    WHERE p.etat_autorisation = 'AUTORISE' 
    AND u.etat_usage = 'Autorise'
    AND u.type_culture_libelle IS NOT NULL
    GROUP BY u.type_culture_libelle
    ORDER BY nb_produits DESC;
    """,
    
    "v_substances_by_function": """
    CREATE OR REPLACE VIEW v_substances_by_function AS
    SELECT 
        ps.fonction,
        sa.nom_substance,
        sa.numero_cas,
        COUNT(DISTINCT p.id) as nb_produits,
        STRING_AGG(DISTINCT p.nom_produit, ', ') as produits
    FROM substances_actives sa
    JOIN product_substances ps ON sa.id = ps.substance_id
    JOIN products p ON ps.product_id = p.id
    WHERE p.etat_autorisation = 'AUTORISE'
    AND sa.etat_autorisation = 'AUTORISE'
    AND ps.fonction IS NOT NULL
    GROUP BY ps.fonction, sa.nom_substance, sa.numero_cas
    ORDER BY ps.fonction, nb_produits DESC;
    """
}


# Database functions for product management
PRODUCT_FUNCTIONS = {
    "update_updated_at_column": """
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """,
    
    "search_products": """
    CREATE OR REPLACE FUNCTION search_products(
        search_term TEXT,
        product_type_filter TEXT DEFAULT NULL,
        crop_filter TEXT DEFAULT NULL
    )
    RETURNS TABLE (
        numero_amm VARCHAR(20),
        nom_produit VARCHAR(200),
        type_produit VARCHAR(10),
        etat_autorisation VARCHAR(20),
        substances_actives TEXT,
        cultures TEXT
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT 
            p.numero_amm,
            p.nom_produit,
            p.type_produit,
            p.etat_autorisation,
            STRING_AGG(DISTINCT sa.nom_substance, ', ') as substances_actives,
            STRING_AGG(DISTINCT u.type_culture_libelle, ', ') as cultures
        FROM products p
        LEFT JOIN product_substances ps ON p.id = ps.product_id
        LEFT JOIN substances_actives sa ON ps.substance_id = sa.id
        LEFT JOIN usages u ON p.id = u.product_id
        WHERE 
            (search_term IS NULL OR 
             p.nom_produit ILIKE '%' || search_term || '%' OR
             p.numero_amm ILIKE '%' || search_term || '%' OR
             sa.nom_substance ILIKE '%' || search_term || '%')
        AND (product_type_filter IS NULL OR p.type_produit = product_type_filter)
        AND (crop_filter IS NULL OR u.type_culture_libelle ILIKE '%' || crop_filter || '%')
        AND p.etat_autorisation = 'AUTORISE'
        GROUP BY p.id, p.numero_amm, p.nom_produit, p.type_produit, p.etat_autorisation
        ORDER BY p.nom_produit;
    END;
    $$ LANGUAGE plpgsql;
    """,
    
    "get_product_usage_for_crop": """
    CREATE OR REPLACE FUNCTION get_product_usage_for_crop(
        product_amm VARCHAR(20),
        crop_name TEXT
    )
    RETURNS TABLE (
        identifiant_usage VARCHAR(50),
        dose_retenue NUMERIC(10,3),
        dose_unite VARCHAR(20),
        nombre_max_application INTEGER,
        delai_avant_recolte_jour INTEGER,
        intervalle_minimum_applications_jour INTEGER,
        znt_aquatique_m INTEGER,
        znt_arthropodes_non_cibles_m INTEGER,
        znt_plantes_non_cibles_m INTEGER,
        condition_emploi TEXT,
        restrictions_usage_libelle TEXT
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT 
            u.identifiant_usage,
            u.dose_retenue,
            u.dose_unite,
            u.nombre_max_application,
            u.delai_avant_recolte_jour,
            u.intervalle_minimum_applications_jour,
            u.znt_aquatique_m,
            u.znt_arthropodes_non_cibles_m,
            u.znt_plantes_non_cibles_m,
            u.condition_emploi,
            u.restrictions_usage_libelle
        FROM products p
        JOIN usages u ON p.id = u.product_id
        WHERE p.numero_amm = product_amm
        AND p.etat_autorisation = 'AUTORISE'
        AND u.etat_usage = 'Autorise'
        AND (crop_name IS NULL OR u.type_culture_libelle ILIKE '%' || crop_name || '%')
        ORDER BY u.dose_retenue DESC;
    END;
    $$ LANGUAGE plpgsql;
    """,
    
    "check_product_compatibility": """
    CREATE OR REPLACE FUNCTION check_product_compatibility(
        product1_amm VARCHAR(20),
        product2_amm VARCHAR(20)
    )
    RETURNS TABLE (
        compatible BOOLEAN,
        conflict_reason TEXT,
        substances_common TEXT
    ) AS $$
    DECLARE
        common_substances TEXT;
        conflict_exists BOOLEAN := FALSE;
    BEGIN
        -- Check for common active substances
        SELECT STRING_AGG(sa.nom_substance, ', ')
        INTO common_substances
        FROM product_substances ps1
        JOIN product_substances ps2 ON ps1.substance_id = ps2.substance_id
        JOIN substances_actives sa ON ps1.substance_id = sa.id
        WHERE ps1.product_id = (SELECT id FROM products WHERE numero_amm = product1_amm)
        AND ps2.product_id = (SELECT id FROM products WHERE numero_amm = product2_amm);
        
        -- Determine compatibility
        IF common_substances IS NOT NULL THEN
            conflict_exists := TRUE;
        END IF;
        
        RETURN QUERY
        SELECT 
            NOT conflict_exists as compatible,
            CASE 
                WHEN conflict_exists THEN 'Substances actives communes: ' || common_substances
                ELSE 'Produits compatibles'
            END as conflict_reason,
            common_substances as substances_common;
    END;
    $$ LANGUAGE plpgsql;
    """
}


# Database triggers
PRODUCT_TRIGGERS = {
    "update_products_updated_at": """
    CREATE TRIGGER update_products_updated_at 
        BEFORE UPDATE ON products 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    """,
    
    "update_substances_actives_updated_at": """
    CREATE TRIGGER update_substances_actives_updated_at 
        BEFORE UPDATE ON substances_actives 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    """,
    
    "audit_products_changes": """
    CREATE OR REPLACE FUNCTION audit_products_changes()
    RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'DELETE' THEN
            INSERT INTO audit_log (table_name, record_id, operation, old_values, changed_at)
            VALUES (TG_TABLE_NAME, OLD.id, TG_OP, row_to_json(OLD), CURRENT_TIMESTAMP);
            RETURN OLD;
        ELSIF TG_OP = 'UPDATE' THEN
            INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values, changed_at)
            VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(OLD), row_to_json(NEW), CURRENT_TIMESTAMP);
            RETURN NEW;
        ELSIF TG_OP = 'INSERT' THEN
            INSERT INTO audit_log (table_name, record_id, operation, new_values, changed_at)
            VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(NEW), CURRENT_TIMESTAMP);
            RETURN NEW;
        END IF;
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
    
    CREATE TRIGGER audit_products_trigger
        AFTER INSERT OR UPDATE OR DELETE ON products
        FOR EACH ROW EXECUTE FUNCTION audit_products_changes();
    """
}


async def create_product_views_and_functions():
    """Create all product database views and functions"""
    async with engine.begin() as conn:
        # Create functions first
        for function_name, function_sql in PRODUCT_FUNCTIONS.items():
            await conn.execute(text(function_sql))
        
        # Create views
        for view_name, view_sql in PRODUCT_VIEWS.items():
            await conn.execute(text(view_sql))
        
        # Create triggers
        for trigger_name, trigger_sql in PRODUCT_TRIGGERS.items():
            await conn.execute(text(trigger_sql))
        
        await conn.commit()


# Indexes for performance optimization
PRODUCT_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_products_numero_amm ON products(numero_amm);",
    "CREATE INDEX IF NOT EXISTS idx_products_nom_produit ON products(nom_produit);",
    "CREATE INDEX IF NOT EXISTS idx_products_type_produit ON products(type_produit);",
    "CREATE INDEX IF NOT EXISTS idx_products_etat_autorisation ON products(etat_autorisation);",
    "CREATE INDEX IF NOT EXISTS idx_products_titulaire ON products(titulaire);",
    "CREATE INDEX IF NOT EXISTS idx_substances_actives_nom ON substances_actives(nom_substance);",
    "CREATE INDEX IF NOT EXISTS idx_substances_actives_numero_cas ON substances_actives(numero_cas);",
    "CREATE INDEX IF NOT EXISTS idx_substances_actives_etat ON substances_actives(etat_autorisation);",
    "CREATE INDEX IF NOT EXISTS idx_product_substances_product_id ON product_substances(product_id);",
    "CREATE INDEX IF NOT EXISTS idx_product_substances_substance_id ON product_substances(substance_id);",
    "CREATE INDEX IF NOT EXISTS idx_usages_product_id ON usages(product_id);",
    "CREATE INDEX IF NOT EXISTS idx_usages_type_culture ON usages(type_culture_libelle);",
    "CREATE INDEX IF NOT EXISTS idx_usages_etat ON usages(etat_usage);",
    "CREATE INDEX IF NOT EXISTS idx_conditions_emploi_product_id ON conditions_emploi(product_id);",
    "CREATE INDEX IF NOT EXISTS idx_classifications_danger_product_id ON classifications_danger(product_id);",
    "CREATE INDEX IF NOT EXISTS idx_phrases_risque_product_id ON phrases_risque(product_id);",
    "CREATE INDEX IF NOT EXISTS idx_phrases_risque_code ON phrases_risque(code_phrase);",
    "CREATE INDEX IF NOT EXISTS idx_phrases_risque_type ON phrases_risque(type_phrase);",
    "CREATE INDEX IF NOT EXISTS idx_permis_importation_numero ON permis_importation(numero_permis);",
    "CREATE INDEX IF NOT EXISTS idx_permis_importation_amm_ref ON permis_importation(numero_amm_reference_francais);",
    "CREATE INDEX IF NOT EXISTS idx_audit_log_table_record ON audit_log(table_name, record_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at ON audit_log(changed_at);"
]


async def create_product_indexes():
    """Create all product database indexes"""
    async with engine.begin() as conn:
        for index_sql in PRODUCT_INDEXES:
            await conn.execute(text(index_sql))
        await conn.commit()
