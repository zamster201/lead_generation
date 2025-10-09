CREATE TABLE IF NOT EXISTS opportunities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  opportunity_id TEXT NOT NULL,
  title TEXT,
  summary_text TEXT
  summary_url TEXT
  url TEXT
  agency TEXT,
  due_date TEXT,
  posted_date TEXT,
  est_value INTEGER,
  naics TEXT,
  set_aside TEXT,
  contract_type TEXT,
  vehicle TEXT,
  keywords TEXT,
  url TEXT,
  attachments_count INTEGER DEFAULT 0,
  compliance_sections INTEGER DEFAULT 0,
  fit_score REAL DEFAULT 0.0,
  risk_score REAL DEFAULT 0.0,
  status_stage TEXT DEFAULT 'new',
  rev_hash TEXT,
  revision INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),

  UNIQUE(source, opportunity_id) ON CONFLICT IGNORE
);
CREATE INDEX IF NOT EXISTS idx_opps_dates ON opportunities (posted_date, due_date);
CREATE INDEX IF NOT EXISTS idx_opps_fit ON opportunities (fit_score DESC);
CREATE INDEX IF NOT EXISTS idx_opps_stage ON opportunities (status_stage);
