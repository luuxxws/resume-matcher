-- Database initialization script for Resume Matcher
-- This script runs automatically when the PostgreSQL container starts

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the resumes table
CREATE TABLE IF NOT EXISTS resumes (
    id SERIAL PRIMARY KEY,
    file_name TEXT NOT NULL,
    file_path TEXT UNIQUE NOT NULL,
    file_hash TEXT NOT NULL,
    raw_text TEXT,
    cleaned_text TEXT,
    json_data JSONB,
    embedding vector(1024),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index for vector similarity search (cosine similarity)
-- Note: ivfflat index works best with 1000+ rows; for smaller datasets, exact search is used
CREATE INDEX IF NOT EXISTS resumes_embedding_idx ON resumes 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create index for faster file path lookups
CREATE INDEX IF NOT EXISTS resumes_file_path_idx ON resumes (file_path);

-- Create index for faster hash lookups (for duplicate detection)
CREATE INDEX IF NOT EXISTS resumes_file_hash_idx ON resumes (file_hash);
