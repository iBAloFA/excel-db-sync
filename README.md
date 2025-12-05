# Excel ↔ Database Live Sync

Watches an Excel file and instantly syncs any change (add/edit/delete) to SQLite or PostgreSQL  
Also pushes database changes back to Excel. Perfect for non-technical teams!

```bash
pip install -r requirements.txt
python sync.py employees.xlsx --db sqlite:///company.db

Features

Real-time two-way sync (uses watchdog)
Auto-creates table from Excel headers
Handles Nigerian phone numbers, ₦ currency, dates
Conflict-free (database is source of truth)
Works offline-first
