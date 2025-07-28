-- Add HNSW index for pgvector performance
-- This will dramatically speed up both vector similarity searches and inserts.
-- Run this command in your Supabase SQL Editor.

CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);

-- Note: For very large datasets (millions of rows), you might want to tune
-- the HNSW parameters (m, ef_construction), but for most use cases,
-- the defaults are excellent.
