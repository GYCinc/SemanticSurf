-- Supabase Schema: Source of Truth
CREATE TABLE IF NOT EXISTS word_frequencies (
    word TEXT PRIMARY KEY,
    rank INTEGER,
    frequency REAL
);

CREATE TABLE IF NOT EXISTS student_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id TEXT,
    transcript TEXT,
    metrics JSONB,
    is_gold_standard BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE TABLE IF NOT EXISTS corpus_phenomena (
    phenomenon_id TEXT PRIMARY KEY,
    item_name TEXT,
    trigger_pattern TEXT,
    category TEXT,
    explanation TEXT
);
