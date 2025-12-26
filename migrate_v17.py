import sqlite3

def migrate():
    print("--- Padsala v17 Database Migration ---")
    try:
        conn = sqlite3.connect('syllabus.db')
        cursor = conn.cursor()
        
        # New columns for Gamification (v17)
        columns = {
            'xp': 'INTEGER DEFAULT 0',
            'streak': 'INTEGER DEFAULT 0',
            'avatar': "TEXT DEFAULT 'default'",
            'is_pro': 'BOOLEAN DEFAULT 0'
        }
        
        for col, dtype in columns.items():
            try:
                # SQLite doesn't support IF NOT EXISTS in ADD COLUMN, so we catch the error
                cursor.execute(f'ALTER TABLE users ADD COLUMN {col} {dtype}')
                print(f"[SUCCESS] Added column: {col}")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print(f"[SKIP] Column already exists: {col}")
                else:
                    print(f"[ERROR] Could not add {col}: {e}")
                
        conn.commit()
        conn.close()
        print("\nMigration complete. Database is ready for The Arena.")
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Migration failed: {e}")

if __name__ == "__main__":
    migrate()
