import hashlib
import sqlite3
from scoring import compute_days_to_due

def compute_rev_hash(lead):
    """Hash for change detection (title + desc + deadline)."""
    content = f"{lead['title']}{lead['description']}{lead['response_deadline']}"
    return hashlib.md5(content.encode()).hexdigest()

def upsert_lead(conn, lead, scores):
    """UPSERT into DB, update if hash changed."""
    rev_hash = compute_rev_hash(lead)
    lead['days_to_due'] = compute_days_to_due(lead['response_deadline'])
    lead['fit_score'] = scores['fit']
    lead['risk_score'] = scores['risk']
    lead['rev_hash'] = rev_hash
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO opportunities 
        (sam_id, title, description, naics, soc, point_of_contact, response_deadline, 
         days_to_due, posted_date, link, rev_hash, fit_score, risk_score, status_stage)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT status_stage FROM opportunities WHERE sam_id = ?), 'new'))
    ''', (lead['sam_id'], lead['title'], lead['description'], lead['naics'], lead['soc'],
          lead['point_of_contact'], lead['response_deadline'], lead['days_to_due'],
          lead['posted_date'], lead['link'], rev_hash, scores['fit'], scores['risk'],
          lead['sam_id']))  # Sticky status
    conn.commit()
    return cursor.rowcount > 0  # Updated or inserted