-- Ekumen Agricultural Database Schema for Supabase
-- Run this in Supabase SQL Editor to create all tables

-- Enable PostGIS (if not already enabled)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create ENUM types
DO $$ BEGIN
    CREATE TYPE userrole AS ENUM ('farmer', 'advisor', 'admin', 'researcher');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE userstatus AS ENUM ('active', 'inactive', 'suspended', 'pending');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE agenttype AS ENUM ('orchestrator', 'farm_data', 'weather', 'crop_health', 'regulatory', 'planning', 'sustainability');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Exploitations (Farms)
CREATE TABLE IF NOT EXISTS exploitations (
    siret VARCHAR(14) PRIMARY KEY,
    nom VARCHAR(255),
    region_code VARCHAR(2),
    department_code VARCHAR(3),
    commune_insee VARCHAR(5),
    surface_totale_ha NUMERIC(10, 2),
    type_exploitation VARCHAR(100),
    bio BOOLEAN DEFAULT FALSE,
    certification_bio VARCHAR(50),
    date_certification_bio DATE,
    extra_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Parcelles (Fields/Parcels)
CREATE TABLE IF NOT EXISTS parcelles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    siret VARCHAR(14) REFERENCES exploitations(siret) ON DELETE CASCADE,
    uuid_parcelle UUID UNIQUE,
    millesime INTEGER NOT NULL,
    nom VARCHAR(255) NOT NULL,
    numero_ilot VARCHAR(50),
    numero_parcelle VARCHAR(50),
    commune_insee VARCHAR(5),
    surface_ha NUMERIC(10, 2) NOT NULL,
    surface_mesuree_ha NUMERIC(10, 2),
    culture_code VARCHAR(10),
    id_culture INTEGER,
    variete VARCHAR(255),
    id_variete INTEGER,
    date_semis DATE,
    bbch_stage INTEGER,
    geometrie JSONB,
    geometrie_vide BOOLEAN DEFAULT FALSE,
    succession_cultures JSONB,
    culture_intermediaire JSONB,
    link_parcelle_millesime_precedent VARCHAR(500),
    uuid_parcelle_millesime_precedent UUID,
    extra_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Interventions (Field Operations)
CREATE TABLE IF NOT EXISTS interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parcelle_id UUID REFERENCES parcelles(id) ON DELETE CASCADE,
    siret VARCHAR(14) REFERENCES exploitations(siret) ON DELETE CASCADE,
    uuid_intervention UUID UNIQUE,
    type_intervention VARCHAR(100) NOT NULL,
    id_type_intervention INTEGER,
    date_intervention DATE NOT NULL,
    date_debut DATE,
    date_fin DATE,
    surface_ha NUMERIC(10, 2),
    surface_travaillee_ha NUMERIC(10, 2),
    id_culture INTEGER,
    description TEXT,
    produit_utilise VARCHAR(255),
    dose_ha VARCHAR(100),
    materiel_utilise VARCHAR(255),
    intrants JSONB,
    extra_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Intrants (Agricultural Inputs)
CREATE TABLE IF NOT EXISTS intrants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    libelle VARCHAR(255) NOT NULL,
    id_intrant INTEGER UNIQUE,
    type_intrant VARCHAR(100),
    id_type_intrant INTEGER,
    code_amm VARCHAR(20),
    extra_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    role userrole DEFAULT 'farmer',
    status userstatus DEFAULT 'active',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    farm_siret VARCHAR(14) REFERENCES exploitations(siret) ON DELETE SET NULL,
    title VARCHAR(500),
    agent_type agenttype DEFAULT 'orchestrator',
    status VARCHAR(20) DEFAULT 'active',
    context_data JSONB,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE
);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sender VARCHAR(20) NOT NULL,
    agent_type agenttype,
    thread_id VARCHAR(255),
    parent_message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    message_metadata JSONB,
    processing_time_ms INTEGER,
    token_count INTEGER,
    cost_usd NUMERIC(10, 6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crops
CREATE TABLE IF NOT EXISTS crops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    scientific_name VARCHAR(255),
    category VARCHAR(100),
    growth_cycle_days INTEGER,
    water_requirements VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Diseases
CREATE TABLE IF NOT EXISTS diseases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    scientific_name VARCHAR(255),
    affected_crops JSONB,
    symptoms JSONB,
    treatment_options JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pests
CREATE TABLE IF NOT EXISTS pests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    scientific_name VARCHAR(255),
    affected_crops JSONB,
    damage_description TEXT,
    control_methods JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_parcelles_siret ON parcelles(siret);
CREATE INDEX IF NOT EXISTS idx_parcelles_millesime ON parcelles(millesime);
CREATE INDEX IF NOT EXISTS idx_interventions_parcelle ON interventions(parcelle_id);
CREATE INDEX IF NOT EXISTS idx_interventions_date ON interventions(date_intervention);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ All tables created successfully!';
END $$;

