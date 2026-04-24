-- Create the primary papers table to hold both Phase 1 and Phase 2 data
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id TEXT UNIQUE NOT NULL, -- OpenAlex/ArXiv ID
    title TEXT,
    authors TEXT,
    abstract TEXT,
    url TEXT,
    publication_year TEXT,
    
    -- Phase 1: Discovery & Insight
    relevance_score INTEGER,
    insight TEXT,
    
    -- Phase 2: Deep Analysis
    analysis_status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
    markdown_report TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger to automatically update updated_at on modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_papers_modtime
BEFORE UPDATE ON papers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Create the chunk_cache table to store intermediate LLM analysis
CREATE TABLE chunk_cache (
    chunk_hash TEXT PRIMARY KEY,
    analysis_result TEXT
);

-- Disable Row Level Security on both tables for seamless backend access
ALTER TABLE papers DISABLE ROW LEVEL SECURITY;
ALTER TABLE chunk_cache DISABLE ROW LEVEL SECURITY;
