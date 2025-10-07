import sqlite3
from datetime import datetime
from scoring import should_triage

def write_daily_triage(db_path='opps.db', output_dir='Outputs'):
    """Query DB for triagable leads, write Markdown."""
    conn = sqlite3.connect(db_path)
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"{output_dir}/Daily_Triage_{today}.md"
    
    cursor = conn.cursor()
    cursor.execute('''
        SELECT title, description, fit_score, risk_score, days_to_due, link, status_stage
        FROM opportunities 
        WHERE should_triage(fit_score, risk_score, days_to_due) = 1
        ORDER BY fit_score DESC
    ''')  # Note: should_triage as SQL func? Or Python filter
    leads = cursor.fetchall()
    conn.close()
    
    # Python filter if no SQL func
    triaged = [lead for lead in leads if should_triage(lead[2], lead[3], lead[4])]
    
    with open(filename, 'w') as f:
        f.write(f"# Daily Triage - {today}\n\n")
        f.write(f"**{len(triaged)} opportunities for review.**\n\n")
        for lead in triaged:
            f.write(f"## {lead[0]} (Fit: {lead[2]:.0f}, Risk: {lead[3]:.0f}, Days: {lead[4]})\n")
            f.write(f"**Status:** {lead[6]}\n\n")
            f.write(f"{lead[1][:200]}...\n\n")
            f.write(f"[View on SAM]({lead[5]})\n\n---\n")
    
    print(f"Triage written to {filename}")
    return filename