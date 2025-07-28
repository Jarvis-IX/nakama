-- RPC Functions for Jarvis Vector Search
-- Run these in your Supabase SQL Editor

-- Function for cosine similarity search
CREATE OR REPLACE FUNCTION search_documents_cosine(
  query_embedding vector(384),
  similarity_threshold float DEFAULT 0.6,
  max_results int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  content text,
  similarity float,
  created_at timestamptz
)
LANGUAGE sql
AS $$
  SELECT 
    documents.id,
    documents.content,
    1 - (documents.embedding <=> query_embedding) AS similarity,
    documents.created_at
  FROM documents
  WHERE 1 - (documents.embedding <=> query_embedding) > similarity_threshold
  ORDER BY documents.embedding <=> query_embedding
  LIMIT max_results;
$$;

-- Function for L2 distance search (alternative)
CREATE OR REPLACE FUNCTION search_documents_l2(
  query_embedding vector(384),
  distance_threshold float DEFAULT 1.0,
  max_results int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  content text,
  distance float,
  created_at timestamptz
)
LANGUAGE sql
AS $$
  SELECT 
    documents.id,
    documents.content,
    documents.embedding <-> query_embedding AS distance,
    documents.created_at
  FROM documents
  WHERE documents.embedding <-> query_embedding < distance_threshold
  ORDER BY documents.embedding <-> query_embedding
  LIMIT max_results;
$$;

-- Function to get document statistics
CREATE OR REPLACE FUNCTION get_document_stats()
RETURNS TABLE (
  total_documents bigint,
  avg_content_length float,
  latest_document timestamptz
)
LANGUAGE sql
AS $$
  SELECT 
    COUNT(*) as total_documents,
    AVG(LENGTH(content)) as avg_content_length,
    MAX(created_at) as latest_document
  FROM documents;
$$;
