import os
import sys
import json
import sqlite3
import shutil
from datetime import datetime

def check_integrity(db_path):
    if not os.path.exists(db_path):
        return False, "File does not exist"
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        res = cur.fetchall()
        conn.close()
        if res and res[0][0] == 'ok':
            return True, "ok"
        return False, str(res)
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("DIVYA TRADING CO. - DATABASE REPAIR & SYNC UTILITY")
    print("=" * 60)

    db_path = 'divya_trading.db'
    is_ok, reason = check_integrity(db_path)
    
    if is_ok:
        print(f"[OK] Existing database integrity verified: {reason}")
    else:
        print(f"[WARN] Database check failed ({reason}). Starting repair...")
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        corrupt_backup = f"divya_trading_corrupt_{timestamp}.db"
        if os.path.exists(db_path):
            shutil.copy2(db_path, corrupt_backup)
            print(f"[BACKUP] Preserved corrupted file as: {corrupt_backup}")
            os.remove(db_path)
            print("[CLEAN] Removed corrupted database file.")

    # Initialize fresh tables via SQLAlchemy
    print("[INIT] Creating database tables...")
    from app import app, db, restore_system_backup_from_dict
    from seed_data import seed_database

    with app.app_context():
        db.create_all()
        seed_database()
        
        # Check for production seed file
        seed_files = ['production_seed.json', 'live_backup.json']
        seeded = False
        for s_file in seed_files:
            if os.path.exists(s_file):
                print(f"[RESTORE] Importing data from {s_file}...")
                try:
                    with open(s_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    success, msg = restore_system_backup_from_dict(data)
                    if success:
                        print(f"[SUCCESS] Restored from {s_file}: {msg}")
                        seeded = True
                        break
                    else:
                        print(f"[NOTICE] Failed restore from {s_file}: {msg}")
                except Exception as ex:
                    print(f"[NOTICE] Could not parse {s_file}: {ex}")

    # Final verify
    is_healthy, final_reason = check_integrity(db_path)
    if is_healthy:
        print("=" * 60)
        print("[SUCCESS] Database is 100% HEALTHY and ACTIVE!")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"[ERROR] Integrity check still failing: {final_reason}")
        sys.exit(1)

if __name__ == '__main__':
    main()
