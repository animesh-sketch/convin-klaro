-- ════════════════════════════════════════════════════════
--  Convin Klaro — Supabase Schema
--  Run this in Supabase SQL Editor (Dashboard → SQL Editor)
-- ════════════════════════════════════════════════════════

-- 1. Knowledge-base sources (documents, web links, WhatsApp, crawled pages)
CREATE TABLE IF NOT EXISTS kb_sources (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT        NOT NULL CHECK (source_type IN ('document','link','whatsapp','crawled')),
    name        TEXT,
    url         TEXT,
    title       TEXT,
    content     TEXT,
    file_type   TEXT,
    size        INTEGER     DEFAULT 0,
    added_at    TIMESTAMPTZ DEFAULT NOW(),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast per-type queries
CREATE INDEX IF NOT EXISTS idx_kb_sources_type ON kb_sources (source_type);

-- 2. Auto-generated FAQs
CREATE TABLE IF NOT EXISTS kb_faqs (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    category   TEXT        NOT NULL DEFAULT 'General',
    question   TEXT        NOT NULL,
    answer     TEXT        NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. App preferences (key/value store)
CREATE TABLE IF NOT EXISTS kb_preferences (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL DEFAULT ''
);

-- Seed default preferences
INSERT INTO kb_preferences (key, value)
VALUES ('show_sources', 'false')
ON CONFLICT (key) DO NOTHING;

-- ════════════════════════════════════════════════════════
-- Row Level Security — enable public read/write for anon
-- (Tighten per your auth requirements in production)
-- ════════════════════════════════════════════════════════

ALTER TABLE kb_sources     ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb_faqs        ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb_preferences ENABLE ROW LEVEL SECURITY;

-- Allow all operations for the anon/service role
CREATE POLICY "allow_all_kb_sources"     ON kb_sources     FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_kb_faqs"        ON kb_faqs        FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_kb_preferences" ON kb_preferences FOR ALL USING (true) WITH CHECK (true);
