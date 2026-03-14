import sqlite3

DATABASE = 'padsala.db'

def migrate():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("Starting V18 Migration...")
    
    # 1. Add base_difficulty and is_elective to subjects
    try:
        cursor.execute("ALTER TABLE subjects ADD COLUMN base_difficulty INTEGER DEFAULT 2")
        print("Added base_difficulty column.")
    except sqlite3.OperationalError:
        print("base_difficulty column already exists.")

    try:
        cursor.execute("ALTER TABLE subjects ADD COLUMN is_elective INTEGER DEFAULT 0")
        print("Added is_elective column.")
    except sqlite3.OperationalError:
        print("is_elective column already exists.")
        
    # 2. Add last_login to users if missing
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
        print("Added last_login column.")
    except sqlite3.OperationalError:
        print("last_login column already exists.")

    # 3. Add XP system columns if missing
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE users ADD COLUMN streak INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE users ADD COLUMN is_pro INTEGER DEFAULT 0")
        print("Added Gamification columns.")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    print("Migration V18 Complete.")

if __name__ == '__main__':
    migrate()
