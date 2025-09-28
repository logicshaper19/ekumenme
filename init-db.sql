-- Initialize Agricultural Chatbot Database
-- Enable PostGIS extension for geographic data
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database if not exists (handled by Docker)
-- CREATE DATABASE agricultural_chatbot;

-- Set timezone
SET timezone = 'Europe/Paris';

-- Create initial admin user (will be handled by application)
-- This is just for reference
