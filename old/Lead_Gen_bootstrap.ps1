param(
[string]$Root = "C:\CTS\Lead_Generation",
[switch]$Overwrite,
[switch]$NoBackup
)

$src = Join-Path $Root "src\leads"
$DoOverwrite = $Overwrite.IsPresent
$DoBackup = -not $NoBackup.IsPresent

function Ensure-Dir {
param([string]$Path)
if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }
}

function Write-Info { param([string]$Msg) Write-Host $Msg -ForegroundColor Cyan }
function Write-Skip { param([string]$Msg) Write-Host $Msg -ForegroundColor DarkYellow }
function Write-OK { param([string]$Msg) Write-Host $Msg -ForegroundColor Green }

function Write-File {
param([string]$Path, [string]$Content)
$dir = Split-Path -Parent $Path
Ensure-Dir $dir
if (Test-Path $Path) {
if (-not $DoOverwrite) { Write-Skip "SKIP $Path (exists)"; return }
if ($DoBackup) { try { Copy-Item $Path "$Path.bak" -ErrorAction Stop } catch {} }
}
$Content | Set-Content -Path $Path -Encoding UTF8
Write-OK "WROTE $Path"
}

--- create dirs ---
Ensure-Dir $Root
Ensure-Dir $src

requirements.txt
Write-File (Join-Path $Root "requirements.txt") @"
requests
python-dotenv
rich
click
tenacity
pydantic
"@

.env.example (we do NOT write .env)
Write-File (Join-Path $Root ".env.example") @"
SAM_API_KEY=YOUR_SAM_KEY
SAM_BASE_URL=https://api.sam.gov/opportunities/v2/search
DB_PATH=opportunities.sqlite
"@

product_metadata.json
Write-File (Join-Path $Root "product_metadata.json") @"
{
"DarkTrace Federal": { "keywords": ["zero trust","siem","soar","email security","phishing","threat detection","ai","ndrp","network detection","endpoint","behavioral analytics","insider threat"] },
"Kove SDM": { "keywords": ["hpc","high performance computing","storage","throughput","iops","data pipeline","parallel file system","low latency"] },
"Audivi Voice": { "keywords": ["voice","contact center","call center","transcription","speech to text","ivr","twilio","voip","recording"] },
"Available Networks":{ "keywords": ["network","wan","sd-wan","vpn","zero trust","sase","redundancy","failover","latency","bandwidth"] }
}
"@

src/leads/init.py
Write-File (Join-Path $src "init.py") @"
all = ['config','fetch','match','persist']
"@

src/leads/config.py
Write-File (Join-Path $src "config.py") @"
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class Settings(BaseModel):
sam_api_key: str = Field(default_factory=lambda: os.getenv('SAM_API_KEY',''))
sam_base_url: str = Field(default_factory=lambda: os.getenv('SAM_BASE_URL','https://api.sam.gov/opportunities/v2/search'))
db_path: str = Field(default_factory=lambda: os.getenv('DB_PATH','opportunities.sqlite'))

settings = Settings()
"@

src/leads/fetch.py
Write-File (Join-Path $src "fetch.py") @"
from typing import Dict, Any, List
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import settings

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def fetch_sam(keywords: str, limit: int = 20, extra_params: Dict[str, Any] = None) -> Dict[str, Any]:
params = {'keywords': keywords, 'limit': limit, 'api_key': settings.sam_api_key}
if extra_params: params.update(extra_params)
r = requests.get(settings.sam_base_url, params=params, timeout=30)
r.raise_for_status()
return r.json()

def flatten_opps(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
data = resp.get('opportunitiesData', []) or resp.get('data', [])
out = []
for opp in data:
out.append({
'id': opp.get('solicitationNumber') or opp.get('noticeId') or opp.get('id'),
'title': opp.get('title') or opp.get('noticeTitle'),
'description': opp.get('description') or '',
'agency': opp.get('department') or (opp.get('organizationHierarchy') or {}).get('department'),
'response_date': opp.get('responseDate') or opp.get('responseDueDate'),
'raw': opp,
})
return out
"@

src/leads/match.py
Write-File (Join-Path $src "match.py") @"
from typing import Dict, List

def keyword_score(text: str, keywords: List[str]) -> int:
t = (text or '').lower()
return sum(1 for kw in keywords if kw.lower() in t)

def score_opportunity(opp: Dict, product_keywords: List[str]) -> Dict:
score = keyword_score(opp.get('description','') + ' ' + (opp.get('title','')), product_keywords)
return {**opp, 'score': score}
"@

src/leads/persist.py
Write-File (Join-Path $src "persist.py") @"
import sqlite3
from typing import Iterable, Dict
from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunities (
id TEXT PRIMARY KEY,
title TEXT,
agency TEXT,
response_date TEXT,
product TEXT,
score INTEGER,
created_at TEXT DEFAULT (datetime('now'))
);
"""

def init_db():
con = sqlite3.connect(settings.db_path); con.execute(SCHEMA); con.commit(); con.close()

def upsert_opportunities(rows: Iterable[Dict]):
con = sqlite3.connect(settings.db_path); con.execute(SCHEMA); cur = con.cursor()
for r in rows:
cur.execute(
"""INSERT INTO opportunities (id,title,agency,response_date,product,score)
VALUES (?,?,?,?,?,?)
ON CONFLICT(id) DO UPDATE SET
title=excluded.title,
agency=excluded.agency,
response_date=excluded.response_date,
product=excluded.product,
score=excluded.score""",
(r.get('id'), r.get('title'), r.get('agency'), r.get('response_date'), r.get('product'), int(r.get('score',0)))
)
con.commit(); con.close()
"@

src/leads/main.py
Write-File (Join-Path $src "main.py") @"
import json, click
from rich import print
from .config import settings
from .fetch import fetch_sam, flatten_opps
from .match import score_opportunity
from .persist import init_db, upsert_opportunities

@click.group()
def cli(): pass

@cli.command(help='Fetch from SAM.gov, score, and persist')
@click.option('--keywords', required=True)
@click.option('--limit', default=25, show_default=True, type=int)
@click.option('--product', required=True)
@click.option('--metadata-path', default='product_metadata.json', show_default=True)
def fetch(keywords, limit, product, metadata_path):
with open(metadata_path, 'r', encoding='utf-8') as f:
meta = json.load(f)
if product not in meta: raise SystemExit(f"Product '{product}' not in {metadata_path}")
product_keywords = meta[product].get('keywords', [])
if not settings.sam_api_key: raise SystemExit('SAM_API_KEY not set. Put it in .env')
resp = fetch_sam(keywords=keywords, limit=limit)
opps = flatten_opps(resp)
scored = [{**score_opportunity(o, product_keywords), 'product': product} for o in opps]
init_db(); upsert_opportunities(scored)
top = sorted(scored, key=lambda x: x.get('score',0), reverse=True)[:10]
print(f"[bold]Saved {len(scored)} opportunities.[/bold] Top by score:")
for o in top: print(f" • ({o.get('score')}) {o.get('title')} — {o.get('id')}")
if name == 'main': cli()
"@

Write-Info "Scaffold ready at $Root"
Write-Info "Use -Overwrite to replace existing files (backs up to .bak by default). Append -NoBackup to skip backups."