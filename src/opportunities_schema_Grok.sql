-- Schema for opportunities/leads table
CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sam_id TEXT UNIQUE NOT NULL,  -- SAM opportunity ID
    title TEXT NOT NULL,
    description TEXT,
    naics TEXT,  -- Comma-separated NAICS codes
    soc TEXT,    -- Set-Aside (e.g., Small Business)
    point_of_contact TEXT,
    response_deadline DATE,
    days_to_due INTEGER,  -- Computed: days from today
    posted_date DATE,
    link TEXT,
    rev_hash TEXT,  -- For change detection
    fit_score REAL DEFAULT 0,  -- 0-100 relevance to portfolio
    risk_score REAL DEFAULT 0,  -- 0-100 (higher = riskier)
    status_stage TEXT DEFAULT 'new'  -- Sticky: new, review, pursue, ignore
);

-- Index for fast queries
CREATE INDEX IF NOT EXISTS idx_sam_id ON opportunities(sam_id);
CREATE INDEX IF NOT EXISTS idx_deadline ON opportunities(response_deadline);
CREATE INDEX IF NOT EXISTS idx_status ON opportunities(status_stage);