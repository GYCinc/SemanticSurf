-- Run this in your Supabase Dashboard > SQL Editor

-- 1. Add the metadata column if it doesn't exist
ALTER TABLE public.transcripts 
ADD COLUMN IF NOT EXISTS metadata jsonb;

-- 2. Force Supabase API to refresh its cache (Crucial!)
NOTIFY pgrst, 'reload config';

