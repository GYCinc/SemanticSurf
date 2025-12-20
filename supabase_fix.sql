-- Supabase Fix: Force Refresh & Migration
-- 1. Ensure word_frequencies is indexed for fast lookup
CREATE INDEX IF NOT EXISTS idx_word_frequencies_rank ON word_frequencies(rank);

-- 2. Ensure session metrics are queryable for analysis
CREATE INDEX IF NOT EXISTS idx_student_sessions_student_id ON student_sessions(student_id);

-- 3. Enable UUID extension if not already active
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
