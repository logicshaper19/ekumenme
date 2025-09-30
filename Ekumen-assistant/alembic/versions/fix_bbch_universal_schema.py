"""Fix BBCH schema - Universal stages (not crop-specific)

Revision ID: fix_bbch_universal_schema
Revises: add_bbch_stages
Create Date: 2025-09-30 18:30:00.000000

BBCH Scale: Universal growth stage codes (0-99) used across all crops
Zadoks Scale: Cereal-specific codes that map to BBCH equivalents

Key insight: BBCH codes are like a calendar - everyone uses the same codes,
not crop-specific versions. The crop-specific part is the Kc values, which
stay in code as a simple dict.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_bbch_universal_schema'
down_revision = 'add_bbch_stages'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old crop-specific table
    op.drop_table('bbch_stages')
    
    # Create universal BBCH stages table
    op.create_table(
        'bbch_stages',
        sa.Column('bbch_code', sa.Integer(), nullable=False),
        sa.Column('principal_stage', sa.Integer(), nullable=False),
        sa.Column('description_fr', sa.Text(), nullable=False),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('bbch_code'),
        sa.CheckConstraint('bbch_code >= 0 AND bbch_code <= 99', name='ck_bbch_code_range'),
        sa.CheckConstraint('principal_stage >= 0 AND principal_stage <= 9', name='ck_principal_stage_range')
    )
    
    # Create index
    op.create_index('ix_bbch_principal', 'bbch_stages', ['principal_stage'])
    
    # Create Zadoks stages table (cereals)
    op.create_table(
        'zadoks_stages',
        sa.Column('zadoks_code', sa.Integer(), nullable=False),
        sa.Column('bbch_equivalent', sa.Integer(), nullable=True),
        sa.Column('description_fr', sa.Text(), nullable=False),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('applies_to', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('zadoks_code'),
        sa.ForeignKeyConstraint(['bbch_equivalent'], ['bbch_stages.bbch_code'], ),
        sa.CheckConstraint('zadoks_code >= 0 AND zadoks_code <= 99', name='ck_zadoks_code_range')
    )
    
    # Create index
    op.create_index('ix_zadoks_bbch', 'zadoks_stages', ['bbch_equivalent'])
    
    # Insert universal BBCH stages (0-99)
    op.execute("""
        INSERT INTO bbch_stages (bbch_code, principal_stage, description_fr, description_en, notes) VALUES
        -- Stage 0: Germination, sprouting, bud development
        (0, 0, 'Semence sèche', 'Dry seed', 'Universal'),
        (1, 0, 'Début de l''imbibition', 'Beginning of seed imbibition', 'Universal'),
        (3, 0, 'Fin de l''imbibition', 'End of seed imbibition', 'Universal'),
        (5, 0, 'Sortie de la radicule', 'Radicle emerged from seed', 'Universal'),
        (7, 0, 'Sortie de l''hypocotyle/coléoptile', 'Hypocotyle/coleoptile emerged', 'Universal'),
        (9, 0, 'Levée: percée de la surface du sol', 'Emergence: breakthrough soil surface', 'Universal'),
        
        -- Stage 1: Leaf development
        (10, 1, 'Première feuille déployée', 'First leaf unfolded', 'Universal'),
        (11, 1, '1ère feuille vraie déployée', '1st true leaf unfolded', 'Universal'),
        (12, 1, '2 feuilles déployées', '2 leaves unfolded', 'Universal'),
        (13, 1, '3 feuilles déployées', '3 leaves unfolded', 'Universal'),
        (14, 1, '4 feuilles déployées', '4 leaves unfolded', 'Universal'),
        (15, 1, '5 feuilles déployées', '5 leaves unfolded', 'Universal'),
        (16, 1, '6 feuilles déployées', '6 leaves unfolded', 'Universal'),
        (17, 1, '7 feuilles déployées', '7 leaves unfolded', 'Universal'),
        (18, 1, '8 feuilles déployées', '8 leaves unfolded', 'Universal'),
        (19, 1, '9 feuilles ou plus déployées', '9 or more leaves unfolded', 'Universal'),
        
        -- Stage 2: Formation of side shoots/tillering
        (20, 2, 'Aucun talle/ramification', 'No tillers/side shoots', 'Universal'),
        (21, 2, 'Début du tallage: 1er talle/ramification', 'Beginning of tillering: 1st tiller', 'Universal'),
        (22, 2, '2 talles/ramifications', '2 tillers/side shoots', 'Universal'),
        (23, 2, '3 talles/ramifications', '3 tillers/side shoots', 'Universal'),
        (25, 2, '5 talles/ramifications', '5 tillers/side shoots', 'Universal'),
        (27, 2, '7 talles/ramifications', '7 tillers/side shoots', 'Universal'),
        (29, 2, 'Fin du tallage/ramification', 'End of tillering', 'Universal'),
        
        -- Stage 3: Stem elongation or rosette growth
        (30, 3, 'Début de la montaison/élongation', 'Beginning of stem elongation', 'Universal'),
        (31, 3, '1er nœud détectable', '1st node detectable', 'Universal'),
        (32, 3, '2ème nœud détectable', '2nd node detectable', 'Universal'),
        (33, 3, '3ème nœud détectable', '3rd node detectable', 'Universal'),
        (35, 3, '5ème nœud détectable', '5th node detectable', 'Universal'),
        (37, 3, 'Dernière feuille visible', 'Flag leaf just visible', 'Universal'),
        (39, 3, 'Ligule de la dernière feuille visible', 'Flag leaf ligule visible', 'Universal'),
        
        -- Stage 4: Development of harvestable vegetable parts
        (40, 4, 'Début du développement des organes', 'Beginning of development', 'Universal'),
        (41, 4, '10% de développement', '10% of development', 'Universal'),
        (43, 4, '30% de développement', '30% of development', 'Universal'),
        (45, 4, '50% de développement', '50% of development', 'Universal'),
        (47, 4, '70% de développement', '70% of development', 'Universal'),
        (49, 4, 'Organes à taille finale', 'Organs at final size', 'Universal'),
        
        -- Stage 5: Inflorescence emergence/heading
        (51, 5, 'Début de l''apparition de l''inflorescence', 'Beginning of inflorescence emergence', 'Universal'),
        (53, 5, '30% de l''inflorescence visible', '30% of inflorescence emerged', 'Universal'),
        (55, 5, '50% de l''inflorescence visible', '50% of inflorescence emerged', 'Universal'),
        (57, 5, '70% de l''inflorescence visible', '70% of inflorescence emerged', 'Universal'),
        (59, 5, 'Fin de l''émergence de l''inflorescence', 'End of inflorescence emergence', 'Universal'),
        
        -- Stage 6: Flowering
        (60, 6, 'Premières fleurs ouvertes', 'First flowers open', 'Universal'),
        (61, 6, 'Début de la floraison: 10%', 'Beginning of flowering: 10%', 'Universal'),
        (63, 6, '30% des fleurs ouvertes', '30% of flowers open', 'Universal'),
        (65, 6, 'Pleine floraison: 50% des fleurs ouvertes', 'Full flowering: 50% open', 'Universal'),
        (67, 6, '70% des fleurs ouvertes', '70% of flowers open', 'Universal'),
        (69, 6, 'Fin de la floraison', 'End of flowering', 'Universal'),
        
        -- Stage 7: Fruit development
        (71, 7, 'Début du développement du fruit', 'Beginning of fruit development', 'Universal'),
        (73, 7, '30% de taille finale', '30% of final size', 'Universal'),
        (75, 7, '50% de taille finale', '50% of final size', 'Universal'),
        (77, 7, '70% de taille finale', '70% of final size', 'Universal'),
        (79, 7, 'Fruit à taille finale', 'Fruit at final size', 'Universal'),
        
        -- Stage 8: Ripening
        (81, 8, 'Début de la maturation', 'Beginning of ripening', 'Universal'),
        (83, 8, 'Maturation précoce', 'Early ripening', 'Universal'),
        (85, 8, 'Maturation avancée', 'Advanced ripening', 'Universal'),
        (87, 8, 'Maturation complète', 'Fully ripe', 'Universal'),
        (89, 8, 'Surmaturité', 'Over-ripe', 'Universal'),
        
        -- Stage 9: Senescence
        (92, 9, 'Surmaturité avancée', 'Advanced over-ripeness', 'Universal'),
        (95, 9, 'Début de la sénescence', 'Beginning of senescence', 'Universal'),
        (97, 9, 'Plante morte', 'Plant dead', 'Universal'),
        (99, 9, 'Parties récoltées', 'Harvested product', 'Universal')
    """)
    
    # Insert Zadoks stages for cereals (wheat, barley, rye)
    op.execute("""
        INSERT INTO zadoks_stages (zadoks_code, bbch_equivalent, description_fr, description_en, applies_to, notes) VALUES
        -- Stage 0: Germination
        (0, 0, 'Semence sèche', 'Dry seed', ARRAY['blé', 'orge', 'seigle'], NULL),
        (1, 1, 'Début de l''imbibition', 'Start of imbibition', ARRAY['blé', 'orge', 'seigle'], NULL),
        (3, 3, 'Imbibition complète', 'Imbibition complete', ARRAY['blé', 'orge', 'seigle'], NULL),
        (5, 5, 'Radicule sortie', 'Radicle emerged', ARRAY['blé', 'orge', 'seigle'], NULL),
        (7, 7, 'Coléoptile sorti', 'Coleoptile emerged', ARRAY['blé', 'orge', 'seigle'], NULL),
        (9, 9, 'Levée', 'Leaf at soil surface', ARRAY['blé', 'orge', 'seigle'], NULL),
        
        -- Stage 1: Seedling growth
        (10, 10, 'Première feuille', 'First leaf through coleoptile', ARRAY['blé', 'orge', 'seigle'], NULL),
        (11, 11, '1ère feuille déployée', '1st leaf unfolded', ARRAY['blé', 'orge', 'seigle'], NULL),
        (12, 12, '2 feuilles déployées', '2 leaves unfolded', ARRAY['blé', 'orge', 'seigle'], NULL),
        (13, 13, '3 feuilles déployées', '3 leaves unfolded', ARRAY['blé', 'orge', 'seigle'], NULL),
        (14, 14, '4 feuilles déployées', '4 leaves unfolded', ARRAY['blé', 'orge', 'seigle'], NULL),
        (15, 15, '5 feuilles déployées', '5 leaves unfolded', ARRAY['blé', 'orge', 'seigle'], NULL),
        (19, 19, '9 feuilles ou plus', '9 or more leaves', ARRAY['blé', 'orge', 'seigle'], NULL),
        
        -- Stage 2: Tillering (Tallage)
        (20, 20, 'Tallage principal seulement', 'Main shoot only', ARRAY['blé', 'orge', 'seigle'], NULL),
        (21, 21, 'Tallage principal + 1 talle', 'Main shoot + 1 tiller', ARRAY['blé', 'orge', 'seigle'], 'Début tallage'),
        (22, 22, 'Tallage principal + 2 talles', 'Main shoot + 2 tillers', ARRAY['blé', 'orge', 'seigle'], NULL),
        (23, 23, 'Tallage principal + 3 talles', 'Main shoot + 3 tillers', ARRAY['blé', 'orge', 'seigle'], NULL),
        (25, 25, 'Tallage principal + 5 talles', 'Main shoot + 5 tillers', ARRAY['blé', 'orge', 'seigle'], NULL),
        (29, 29, 'Fin du tallage', 'End of tillering', ARRAY['blé', 'orge', 'seigle'], NULL),
        
        -- Stage 3: Stem elongation (Montaison)
        (30, 30, 'Épi à 1 cm', 'Pseudo stem erection', ARRAY['blé', 'orge', 'seigle'], 'Début montaison'),
        (31, 31, '1er nœud détectable', '1st node detectable', ARRAY['blé', 'orge', 'seigle'], NULL),
        (32, 32, '2ème nœud détectable', '2nd node detectable', ARRAY['blé', 'orge', 'seigle'], NULL),
        (33, 33, '3ème nœud détectable', '3rd node detectable', ARRAY['blé', 'orge', 'seigle'], NULL),
        (37, 37, 'Dernière feuille visible', 'Flag leaf just visible', ARRAY['blé', 'orge', 'seigle'], NULL),
        (39, 39, 'Ligule dernière feuille visible', 'Flag leaf ligule visible', ARRAY['blé', 'orge', 'seigle'], NULL),
        
        -- Stage 4: Booting (Gonflement)
        (41, 41, 'Gaine de la dernière feuille s''allonge', 'Flag leaf sheath extending', ARRAY['blé', 'orge', 'seigle'], NULL),
        (43, 43, 'Gaine gonflée', 'Boots just visibly swollen', ARRAY['blé', 'orge', 'seigle'], NULL),
        (45, 45, 'Gaine gonflée, épi visible', 'Boots swollen, ear visible', ARRAY['blé', 'orge', 'seigle'], NULL),
        (47, 47, 'Gaine ouverte', 'Flag leaf sheath opening', ARRAY['blé', 'orge', 'seigle'], NULL),
        (49, 49, 'Premières barbes visibles', 'First awns visible', ARRAY['blé', 'orge', 'seigle'], NULL),
        
        -- Stage 5: Ear emergence (Épiaison)
        (51, 51, 'Début de l''épiaison', 'Beginning of heading', ARRAY['blé', 'orge', 'seigle'], NULL),
        (53, 53, '30% de l''épi sorti', '30% of ear emerged', ARRAY['blé', 'orge', 'seigle'], NULL),
        (55, 55, 'Mi-épiaison: 50%', 'Half of ear emerged', ARRAY['blé', 'orge', 'seigle'], NULL),
        (57, 57, '70% de l''épi sorti', '70% of ear emerged', ARRAY['blé', 'orge', 'seigle'], NULL),
        (59, 59, 'Fin de l''épiaison', 'End of heading', ARRAY['blé', 'orge', 'seigle'], NULL),
        
        -- Stage 6: Flowering/Anthesis (Floraison)
        (61, 61, 'Début de la floraison', 'Beginning of flowering', ARRAY['blé', 'orge', 'seigle'], NULL),
        (65, 65, 'Pleine floraison: 50%', 'Full flowering: 50%', ARRAY['blé', 'orge', 'seigle'], 'Floraison'),
        (69, 69, 'Fin de la floraison', 'End of flowering', ARRAY['blé', 'orge', 'seigle'], NULL),
        
        -- Stage 7: Grain development
        (71, 71, 'Grain laiteux', 'Watery ripe', ARRAY['blé', 'orge', 'seigle'], NULL),
        (73, 73, 'Grain laiteux précoce', 'Early milk', ARRAY['blé', 'orge', 'seigle'], NULL),
        (75, 75, 'Grain laiteux moyen', 'Medium milk', ARRAY['blé', 'orge', 'seigle'], NULL),
        (77, 77, 'Grain laiteux tardif', 'Late milk', ARRAY['blé', 'orge', 'seigle'], NULL),
        
        -- Stage 8: Ripening (Maturation)
        (83, 83, 'Grain pâteux précoce', 'Early dough', ARRAY['blé', 'orge', 'seigle'], NULL),
        (85, 85, 'Grain pâteux', 'Soft dough', ARRAY['blé', 'orge', 'seigle'], NULL),
        (87, 87, 'Grain dur', 'Hard dough', ARRAY['blé', 'orge', 'seigle'], NULL),
        (89, 89, 'Maturité physiologique', 'Fully ripe', ARRAY['blé', 'orge', 'seigle'], 'Maturité'),
        
        -- Stage 9: Senescence
        (92, 92, 'Surmaturité', 'Over-ripe', ARRAY['blé', 'orge', 'seigle'], NULL),
        (99, 99, 'Récolté', 'Harvested', ARRAY['blé', 'orge', 'seigle'], NULL)
    """)


def downgrade() -> None:
    op.drop_table('zadoks_stages')
    op.drop_table('bbch_stages')

