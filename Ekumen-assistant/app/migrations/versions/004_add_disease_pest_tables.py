"""Add disease and pest knowledge base tables

Revision ID: 004_add_disease_pest_tables
Revises: 003_add_ephy_tables
Create Date: 2024-09-28 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_disease_pest_tables'
down_revision = '003_add_ephy_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create disease and pest knowledge base tables."""
    
    # Create diseases table
    op.create_table('diseases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('scientific_name', sa.String(length=300), nullable=True),
        sa.Column('common_names', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('disease_type', sa.String(length=100), nullable=False),
        sa.Column('pathogen_name', sa.String(length=200), nullable=True),
        sa.Column('severity_level', sa.String(length=50), nullable=False),
        sa.Column('affected_crops', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('primary_crop', sa.String(length=100), nullable=False),
        sa.Column('symptoms', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('visual_indicators', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('damage_patterns', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('favorable_conditions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('seasonal_occurrence', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('geographic_distribution', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('treatment_options', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('prevention_methods', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('organic_treatments', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('chemical_treatments', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('yield_impact', sa.String(length=50), nullable=True),
        sa.Column('economic_threshold', sa.Float(), nullable=True),
        sa.Column('resistance_management', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('data_source', sa.String(length=200), nullable=True),
        sa.Column('last_verified', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('keywords', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('search_vector', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for diseases table
    op.create_index(op.f('ix_diseases_id'), 'diseases', ['id'], unique=False)
    op.create_index(op.f('ix_diseases_name'), 'diseases', ['name'], unique=False)
    op.create_index(op.f('ix_diseases_disease_type'), 'diseases', ['disease_type'], unique=False)
    op.create_index(op.f('ix_diseases_severity_level'), 'diseases', ['severity_level'], unique=False)
    op.create_index(op.f('ix_diseases_primary_crop'), 'diseases', ['primary_crop'], unique=False)
    
    # Create pests table
    op.create_table('pests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('scientific_name', sa.String(length=300), nullable=True),
        sa.Column('common_names', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('pest_type', sa.String(length=100), nullable=False),
        sa.Column('pest_family', sa.String(length=200), nullable=True),
        sa.Column('life_cycle', sa.String(length=100), nullable=True),
        sa.Column('severity_level', sa.String(length=50), nullable=False),
        sa.Column('affected_crops', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('primary_crop', sa.String(length=100), nullable=False),
        sa.Column('damage_patterns', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('pest_indicators', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('visual_identification', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('behavioral_signs', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('development_stages', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('reproduction_rate', sa.String(length=50), nullable=True),
        sa.Column('overwintering_strategy', sa.String(length=200), nullable=True),
        sa.Column('host_range', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('favorable_conditions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('seasonal_activity', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('geographic_distribution', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('treatment_options', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('prevention_methods', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('biological_control', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('chemical_control', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('cultural_control', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('yield_impact', sa.String(length=50), nullable=True),
        sa.Column('economic_threshold', sa.Float(), nullable=True),
        sa.Column('action_threshold', sa.Float(), nullable=True),
        sa.Column('resistance_management', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('monitoring_methods', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('trap_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('scouting_frequency', sa.String(length=100), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('data_source', sa.String(length=200), nullable=True),
        sa.Column('last_verified', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('keywords', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('search_vector', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for pests table
    op.create_index(op.f('ix_pests_id'), 'pests', ['id'], unique=False)
    op.create_index(op.f('ix_pests_name'), 'pests', ['name'], unique=False)
    op.create_index(op.f('ix_pests_pest_type'), 'pests', ['pest_type'], unique=False)
    op.create_index(op.f('ix_pests_severity_level'), 'pests', ['severity_level'], unique=False)
    op.create_index(op.f('ix_pests_primary_crop'), 'pests', ['primary_crop'], unique=False)


def downgrade():
    """Drop disease and pest knowledge base tables."""
    
    # Drop indexes first
    op.drop_index(op.f('ix_pests_primary_crop'), table_name='pests')
    op.drop_index(op.f('ix_pests_severity_level'), table_name='pests')
    op.drop_index(op.f('ix_pests_pest_type'), table_name='pests')
    op.drop_index(op.f('ix_pests_name'), table_name='pests')
    op.drop_index(op.f('ix_pests_id'), table_name='pests')
    
    op.drop_index(op.f('ix_diseases_primary_crop'), table_name='diseases')
    op.drop_index(op.f('ix_diseases_severity_level'), table_name='diseases')
    op.drop_index(op.f('ix_diseases_disease_type'), table_name='diseases')
    op.drop_index(op.f('ix_diseases_name'), table_name='diseases')
    op.drop_index(op.f('ix_diseases_id'), table_name='diseases')
    
    # Drop tables
    op.drop_table('pests')
    op.drop_table('diseases')
