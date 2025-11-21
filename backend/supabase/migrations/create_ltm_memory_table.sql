-- Create chat_ltm_memory table for storing Long-Term Memory embeddings and NER
-- This table stores semantic embeddings and named entities from chat messages
-- for retrieval-augmented context in multi-turn conversations

CREATE TABLE IF NOT EXISTS chat_ltm_memory (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  message_id UUID REFERENCES chat_messages(id) ON DELETE CASCADE,
  semantic_embedding vector(1536), -- OpenAI text-embedding-3-large produces 1536-dim vectors
  ner_entities JSONB DEFAULT '{}'::jsonb, -- Stores extracted entities: {skills: [], companies: [], roles: [], etc.}
  message_content TEXT, -- Store original message content for reference
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_chat_ltm_memory_user_id ON chat_ltm_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_ltm_memory_created_at ON chat_ltm_memory(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_ltm_memory_message_id ON chat_ltm_memory(message_id);

-- Create index on semantic_embedding for vector similarity search (requires vector extension)
-- Note: This requires the vector extension to be enabled in Supabase
CREATE INDEX IF NOT EXISTS idx_chat_ltm_memory_embedding ON chat_ltm_memory 
USING ivfflat (semantic_embedding vector_cosine_ops);

-- Enable Row Level Security (RLS)
ALTER TABLE chat_ltm_memory ENABLE ROW LEVEL SECURITY;

-- Create policy: Users can only see their own LTM entries
CREATE POLICY "Users can view their own LTM memory"
  ON chat_ltm_memory
  FOR SELECT
  USING (auth.uid() = user_id);

-- Create policy: Users can insert their own LTM entries
CREATE POLICY "Users can insert their own LTM memory"
  ON chat_ltm_memory
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Create policy: Users can update their own LTM entries
CREATE POLICY "Users can update their own LTM memory"
  ON chat_ltm_memory
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Create policy: Users can delete their own LTM entries
CREATE POLICY "Users can delete their own LTM memory"
  ON chat_ltm_memory
  FOR DELETE
  USING (auth.uid() = user_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_ltm_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_chat_ltm_memory_updated_at
  BEFORE UPDATE ON chat_ltm_memory
  FOR EACH ROW
  EXECUTE FUNCTION update_ltm_updated_at_column();

-- Create RPC function for vector similarity search using pgvector
CREATE OR REPLACE FUNCTION match_ltm_memories(
  query_embedding vector(1536),
  match_user_id uuid,
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  message_id uuid,
  message_content text,
  ner_entities jsonb,
  similarity float,
  created_at timestamptz
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    chat_ltm_memory.id,
    chat_ltm_memory.message_id,
    chat_ltm_memory.message_content,
    chat_ltm_memory.ner_entities,
    1 - (chat_ltm_memory.semantic_embedding <=> query_embedding) as similarity,
    chat_ltm_memory.created_at
  FROM chat_ltm_memory
  WHERE chat_ltm_memory.user_id = match_user_id
    AND 1 - (chat_ltm_memory.semantic_embedding <=> query_embedding) >= match_threshold
  ORDER BY chat_ltm_memory.semantic_embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

