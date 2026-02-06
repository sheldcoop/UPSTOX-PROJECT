-- PostgreSQL Initialization Script
-- Creates necessary extensions and configurations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create indexes for common queries
-- These will be created after migration, but defined here for reference

-- Note: Actual table creation and indexing happens via migration script
-- This file is for database initialization only

-- Set timezone
SET timezone = 'Asia/Kolkata';

-- Create application user (if not exists)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = 'upstox_app') THEN
      CREATE ROLE upstox_app WITH LOGIN PASSWORD 'change_me_in_production';
   END IF;
END
$do$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE upstox_trading TO upstox;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO upstox;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO upstox;
