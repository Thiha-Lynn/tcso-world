"""SSH-only operator tool; never exposed through HTTP."""
import argparse
import json
from datetime import datetime, timezone
from intake import database
parser = argparse.ArgumentParser(description='Review private TCSO applications')
parser.add_argument('--limit', type=int, default=20)
args = parser.parse_args()
with database() as db:
    for ref, created, payload in db.execute('SELECT reference, created, payload FROM applications ORDER BY created DESC LIMIT ?', (max(1,min(args.limit,100)),)):
        print(json.dumps({'reference':ref,'received':datetime.fromtimestamp(created,timezone.utc).isoformat(), **json.loads(payload)},ensure_ascii=False))
