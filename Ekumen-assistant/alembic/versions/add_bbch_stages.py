"""Add BBCH growth stages table

Revision ID: add_bbch_stages
Revises: 
Create Date: 2025-09-30 12:00:00.000000

BBCH Scale (Biologische Bundesanstalt, Bundessortenamt and CHemical industry)
European standard for crop phenology (0-99 decimal code)

Principal stages:
0: Germination, sprouting, bud development
1: Leaf development
2: Formation of side shoots/tillering
3: Stem elongation or rosette growth
4: Development of harvestable vegetable parts
5: Inflorescence emergence/heading
6: Flowering
7: Fruit development
8: Ripening
9: Senescence
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_bbch_stages'
down_revision = 'c2c8bf1dc3b5'  # add_response_feedback_table
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create BBCH stages table
    op.create_table(
        'bbch_stages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crop_type', sa.String(length=50), nullable=False),
        sa.Column('bbch_code', sa.Integer(), nullable=False),
        sa.Column('principal_stage', sa.Integer(), nullable=False),
        sa.Column('description_fr', sa.Text(), nullable=False),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('typical_duration_days', sa.Integer(), nullable=True),
        sa.Column('kc_value', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('crop_type', 'bbch_code', name='uq_crop_bbch'),
        sa.CheckConstraint('bbch_code >= 0 AND bbch_code <= 99', name='ck_bbch_code_range'),
        sa.CheckConstraint('principal_stage >= 0 AND principal_stage <= 9', name='ck_principal_stage_range'),
        sa.CheckConstraint('kc_value IS NULL OR (kc_value >= 0 AND kc_value <= 2.0)', name='ck_kc_value_range')
    )
    
    # Create index for fast lookups
    op.create_index('ix_bbch_crop_code', 'bbch_stages', ['crop_type', 'bbch_code'])
    op.create_index('ix_bbch_principal', 'bbch_stages', ['crop_type', 'principal_stage'])
    
    # Insert BBCH data for wheat (blé)
    op.execute("""
        INSERT INTO bbch_stages (crop_type, bbch_code, principal_stage, description_fr, description_en, typical_duration_days, kc_value, notes) VALUES
        -- Stage 0: Germination
        ('blé', 0, 0, 'Semence sèche', 'Dry seed', NULL, 0.30, 'Initial Kc'),
        ('blé', 1, 0, 'Début de l''imbibition', 'Beginning of seed imbibition', 1, 0.30, NULL),
        ('blé', 3, 0, 'Fin de l''imbibition', 'End of seed imbibition', 1, 0.30, NULL),
        ('blé', 5, 0, 'Sortie de la radicule', 'Radicle emerged from seed', 2, 0.30, NULL),
        ('blé', 7, 0, 'Sortie du coléoptile', 'Coleoptile emerged from seed', 2, 0.30, NULL),
        ('blé', 9, 0, 'Levée: le coléoptile perce la surface du sol', 'Emergence: coleoptile breaks through soil surface', 3, 0.35, NULL),
        
        -- Stage 1: Leaf development
        ('blé', 10, 1, 'Première feuille sort du coléoptile', 'First leaf through coleoptile', 5, 0.40, NULL),
        ('blé', 11, 1, '1ère feuille déployée', '1st leaf unfolded', 3, 0.45, NULL),
        ('blé', 12, 1, '2 feuilles déployées', '2 leaves unfolded', 3, 0.50, NULL),
        ('blé', 13, 1, '3 feuilles déployées', '3 leaves unfolded', 3, 0.55, NULL),
        ('blé', 14, 1, '4 feuilles déployées', '4 leaves unfolded', 3, 0.60, NULL),
        ('blé', 15, 1, '5 feuilles déployées', '5 leaves unfolded', 3, 0.65, NULL),
        ('blé', 19, 1, '9 feuilles ou plus déployées', '9 or more leaves unfolded', 5, 0.70, NULL),
        
        -- Stage 2: Tillering
        ('blé', 20, 2, 'Aucun talle', 'No tillers', NULL, 0.70, NULL),
        ('blé', 21, 2, 'Début du tallage: 1er talle détectable', 'Beginning of tillering: 1st tiller detectable', 7, 0.75, NULL),
        ('blé', 22, 2, '2 talles détectables', '2 tillers detectable', 5, 0.80, NULL),
        ('blé', 23, 2, '3 talles détectables', '3 tillers detectable', 5, 0.85, NULL),
        ('blé', 25, 2, '5 talles détectables', '5 tillers detectable', 7, 0.90, NULL),
        ('blé', 29, 2, 'Fin du tallage', 'End of tillering', 10, 0.95, 'Maximum tillering'),
        
        -- Stage 3: Stem elongation (Montaison)
        ('blé', 30, 3, 'Début de la montaison: épi à 1 cm', 'Beginning of stem elongation: pseudo stem erect', 7, 1.00, NULL),
        ('blé', 31, 3, '1er nœud détectable', '1st node detectable', 5, 1.05, NULL),
        ('blé', 32, 3, '2ème nœud détectable', '2nd node detectable', 5, 1.10, NULL),
        ('blé', 37, 3, 'Dernière feuille visible', 'Flag leaf just visible', 7, 1.15, 'Critical stage'),
        ('blé', 39, 3, 'Ligule de la dernière feuille visible', 'Flag leaf ligule just visible', 5, 1.15, NULL),
        
        -- Stage 5: Heading (Épiaison)
        ('blé', 51, 5, 'Début de l''épiaison: gaine éclatée', 'Beginning of heading: tip of inflorescence emerged', 5, 1.15, NULL),
        ('blé', 55, 5, 'Mi-épiaison: 50% de l''épi sorti', 'Mid-heading: half of inflorescence emerged', 3, 1.15, NULL),
        ('blé', 59, 5, 'Fin de l''épiaison', 'End of heading: inflorescence fully emerged', 3, 1.15, 'Peak water demand'),
        
        -- Stage 6: Flowering (Floraison)
        ('blé', 61, 6, 'Début de la floraison', 'Beginning of flowering', 3, 1.15, NULL),
        ('blé', 65, 6, 'Pleine floraison: 50% des fleurs ouvertes', 'Full flowering: 50% of flowers open', 3, 1.15, 'Critical for yield'),
        ('blé', 69, 6, 'Fin de la floraison', 'End of flowering', 3, 1.10, NULL),
        
        -- Stage 7: Grain development
        ('blé', 71, 7, 'Grain laiteux', 'Watery ripe', 7, 1.05, NULL),
        ('blé', 73, 7, 'Grain laiteux précoce', 'Early milk', 5, 1.00, NULL),
        ('blé', 75, 7, 'Grain laiteux moyen', 'Medium milk', 5, 0.90, NULL),
        ('blé', 77, 7, 'Grain laiteux tardif', 'Late milk', 5, 0.80, NULL),
        
        -- Stage 8: Ripening (Maturation)
        ('blé', 83, 8, 'Grain pâteux précoce', 'Early dough', 5, 0.70, NULL),
        ('blé', 85, 8, 'Grain pâteux', 'Soft dough', 5, 0.60, NULL),
        ('blé', 87, 8, 'Grain dur', 'Hard dough', 5, 0.50, NULL),
        ('blé', 89, 8, 'Grain dur: maturité physiologique', 'Fully ripe: physiological maturity', 5, 0.40, NULL),
        
        -- Stage 9: Senescence
        ('blé', 92, 9, 'Surmaturité: grain très dur', 'Over-ripe: grain very hard', 7, 0.35, NULL),
        ('blé', 97, 9, 'Plante morte et sèche', 'Plant dead and dry', NULL, 0.30, 'Harvest ready')
    """)
    
    # Insert BBCH data for corn (maïs)
    op.execute("""
        INSERT INTO bbch_stages (crop_type, bbch_code, principal_stage, description_fr, description_en, kc_value, notes) VALUES
        -- Key stages for maïs
        ('maïs', 0, 0, 'Semence sèche', 'Dry seed', 0.30, 'Initial Kc'),
        ('maïs', 9, 0, 'Levée', 'Emergence', 0.35, NULL),
        ('maïs', 10, 1, 'Première feuille', 'First leaf', 0.40, NULL),
        ('maïs', 14, 1, '4 feuilles déployées', '4 leaves unfolded', 0.50, NULL),
        ('maïs', 16, 1, '6 feuilles déployées', '6 leaves unfolded', 0.60, NULL),
        ('maïs', 19, 1, '9 feuilles ou plus', '9 or more leaves', 0.70, NULL),
        ('maïs', 30, 3, 'Début de la montaison', 'Beginning of stem elongation', 0.80, NULL),
        ('maïs', 37, 3, 'Dernière feuille visible', 'Flag leaf visible', 1.00, NULL),
        ('maïs', 51, 5, 'Début de l''apparition de la panicule', 'Beginning of tassel emergence', 1.10, NULL),
        ('maïs', 55, 5, 'Panicule à mi-hauteur', 'Tassel half emerged', 1.15, NULL),
        ('maïs', 61, 6, 'Début de la floraison mâle', 'Beginning of pollen shedding', 1.20, 'Peak water demand'),
        ('maïs', 65, 6, 'Pleine floraison', 'Full flowering', 1.20, 'Critical stage'),
        ('maïs', 71, 7, 'Grain laiteux', 'Watery ripe', 1.15, NULL),
        ('maïs', 75, 7, 'Grain laiteux moyen', 'Medium milk', 1.00, NULL),
        ('maïs', 83, 8, 'Grain pâteux précoce', 'Early dough', 0.80, NULL),
        ('maïs', 87, 8, 'Grain dur', 'Hard dough', 0.70, NULL),
        ('maïs', 89, 8, 'Maturité physiologique', 'Physiological maturity', 0.60, 'Harvest ready'),
        ('maïs', 92, 9, 'Surmaturité', 'Over-ripe', 0.50, NULL)
    """)
    
    # Insert BBCH data for rapeseed (colza)
    op.execute("""
        INSERT INTO bbch_stages (crop_type, bbch_code, principal_stage, description_fr, description_en, kc_value, notes) VALUES
        -- Key stages for colza
        ('colza', 0, 0, 'Semence sèche', 'Dry seed', 0.35, 'Initial Kc'),
        ('colza', 9, 0, 'Levée', 'Emergence', 0.40, NULL),
        ('colza', 10, 1, 'Cotylédons déployés', 'Cotyledons unfolded', 0.45, NULL),
        ('colza', 12, 1, '2 feuilles vraies', '2 true leaves', 0.55, NULL),
        ('colza', 14, 1, '4 feuilles vraies', '4 true leaves', 0.65, NULL),
        ('colza', 19, 1, '9 feuilles ou plus', '9 or more leaves', 0.80, NULL),
        ('colza', 30, 3, 'Début de la montaison', 'Beginning of stem elongation', 0.90, NULL),
        ('colza', 32, 3, '2 nœuds visibles', '2 nodes visible', 1.00, NULL),
        ('colza', 51, 5, 'Boutons floraux visibles', 'Flower buds visible', 1.05, NULL),
        ('colza', 60, 6, 'Premières fleurs ouvertes', 'First flowers open', 1.10, NULL),
        ('colza', 65, 6, 'Pleine floraison', 'Full flowering', 1.10, 'Peak water demand'),
        ('colza', 69, 6, 'Fin de la floraison', 'End of flowering', 1.00, NULL),
        ('colza', 71, 7, 'Début de la formation des siliques', 'Beginning of pod development', 0.90, NULL),
        ('colza', 79, 7, 'Siliques à taille finale', 'Pods at final size', 0.70, NULL),
        ('colza', 80, 8, 'Début de la maturation', 'Beginning of ripening', 0.60, NULL),
        ('colza', 89, 8, 'Maturité complète', 'Fully ripe', 0.50, 'Harvest ready'),
        ('colza', 92, 9, 'Surmaturité', 'Over-ripe', 0.45, NULL)
    """)


def downgrade() -> None:
    op.drop_index('ix_bbch_principal', table_name='bbch_stages')
    op.drop_index('ix_bbch_crop_code', table_name='bbch_stages')
    op.drop_table('bbch_stages')

