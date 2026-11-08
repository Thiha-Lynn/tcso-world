"""Daily retention cleanup and a private, consistent current SQLite backup."""
import os
import sqlite3
import time
from intake import STATE, database
from email_verification import schema
os.umask(0o077)
with database() as db:
    schema(db)
    db.execute('DELETE FROM email_codes WHERE created < ?', (int(time.time()) - 86400,))
    db.execute('DELETE FROM applications WHERE created < ?', (int(time.time()) - 89 * 86400,))
    db.execute('DELETE FROM rate_limits WHERE created < ?', (int(time.time()) - 3600,))
with database() as source, sqlite3.connect(STATE / 'intake-backup.sqlite3') as target:
    source.backup(target)
