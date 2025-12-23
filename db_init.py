import sqlite3
import json

# The existing database structure
SYLLABUS_DATA = {
    "Purbanchal University (PoU)": {
        "Engineering": {
            "B.E. Computer": {
                "1st Sem": {
                    "Engineering Mathematics I": ["Calculus", "Linear Algebra", "Complex Numbers"],
                    "Engineering Physics": ["Optics", "Electrostatics", "Magnetism"],
                    "Computer Programming (C)": ["Data Types", "Control Structures", "Arrays", "Functions"],
                    "Basic Electrical Engineering": ["DC Circuits", "AC Circuits", "Transformers"],
                    "Engineering Drawing I": ["Projections", "Orthographic", "Isometrics"]
                },
                "2nd Sem": {
                    "Engineering Mathematics II": ["Integration", "Differential Equations"],
                    "Engineering Chemistry": ["Atomic Structure", "Polymers", "Thermodynamics"],
                    "Object Oriented Programming (C++)": ["Classes", "Inheritance", "Polymorphism"],
                    "Basic Electronics": ["Semiconductors", "Diodes", "Transistors"],
                    "Workshop Technology": ["Carpentry", "Foundry", "Welding"]
                },
                "3rd Sem": {
                    "Discrete Structure": ["Logic", "Graph Theory", "Sets"],
                    "Microprocessor": ["8085", "Architecture", "Assembly"],
                    "Data Structure & Algorithms": ["Lists", "Stacks", "Trees", "Sorting"],
                    "Digital Logic": ["Gates", "Combinational", "Sequential"]
                }
            },
            "B.E. Civil": {
                "1st Sem": {
                    "Engineering Drawing I": ["Scale", "Projection", "Sectioning"],
                    "Applied Mechanics": ["Statics", "Dynamics"],
                    "Mathematics I": ["Calculus", "Algebra"]
                }
            }
        },
        "Science & Technology": {
            "BIT": {
                "1st Sem": {
                    "Introduction to IT": ["IT Basics", "Digital Ethics"],
                    "Programming Concept": ["Logic Building", "Loops"],
                    "Mathematics": ["Algebra", "Probability"]
                }
            }
        }
    }
}

def init_db():
    conn = sqlite3.connect('padsala.db')
    cursor = conn.cursor()

    # Drop tables if they exist to start fresh
    cursor.execute('DROP TABLE IF EXISTS chapters')
    cursor.execute('DROP TABLE IF EXISTS subjects')
    cursor.execute('DROP TABLE IF EXISTS semesters')
    cursor.execute('DROP TABLE IF EXISTS courses')
    cursor.execute('DROP TABLE IF EXISTS faculties')
    cursor.execute('DROP TABLE IF EXISTS universities')

    # Create tables
    cursor.execute('CREATE TABLE universities (id INTEGER PRIMARY KEY, name TEXT UNIQUE)')
    cursor.execute('CREATE TABLE faculties (id INTEGER PRIMARY KEY, university_id INTEGER, name TEXT, FOREIGN KEY(university_id) REFERENCES universities(id))')
    cursor.execute('CREATE TABLE courses (id INTEGER PRIMARY KEY, faculty_id INTEGER, name TEXT, FOREIGN KEY(faculty_id) REFERENCES faculties(id))')
    cursor.execute('CREATE TABLE semesters (id INTEGER PRIMARY KEY, course_id INTEGER, name TEXT, FOREIGN KEY(course_id) REFERENCES courses(id))')
    cursor.execute('CREATE TABLE subjects (id INTEGER PRIMARY KEY, semester_id INTEGER, name TEXT, FOREIGN KEY(semester_id) REFERENCES semesters(id))')
    cursor.execute('CREATE TABLE chapters (id INTEGER PRIMARY KEY, subject_id INTEGER, name TEXT, FOREIGN KEY(subject_id) REFERENCES subjects(id))')
    
    # Auth & Multi-Timeline Tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        password_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS saved_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        data TEXT NOT NULL,  -- JSON string of the schedule
        inputs TEXT,         -- JSON string of wizard inputs
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # v17: COGNITIVE DATA TABLES
    cursor.execute('''CREATE TABLE IF NOT EXISTS topic_mastery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        topic TEXT,
        mastery_score INTEGER DEFAULT 0,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS session_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        topic TEXT,
        duration_mins INTEGER,
        focus_score INTEGER,
        distraction_count INTEGER,
        idle_seconds INTEGER,
        abandoned BOOLEAN DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS user_metrics (
        user_id INTEGER PRIMARY KEY,
        total_xp INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        peak_study_hour INTEGER,
        burnout_risk TEXT DEFAULT 'LOW',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # Seed data
    for uni_name, faculties in SYLLABUS_DATA.items():
        cursor.execute('INSERT INTO universities (name) VALUES (?)', (uni_name,))
        uni_id = cursor.lastrowid
        
        for fac_name, courses in faculties.items():
            cursor.execute('INSERT INTO faculties (university_id, name) VALUES (?, ?)', (uni_id, fac_name))
            fac_id = cursor.lastrowid
            
            for course_name, semesters in courses.items():
                cursor.execute('INSERT INTO courses (faculty_id, name) VALUES (?, ?)', (fac_id, course_name))
                course_id = cursor.lastrowid
                
                for sem_name, subjects in semesters.items():
                    cursor.execute('INSERT INTO semesters (course_id, name) VALUES (?, ?)', (course_id, sem_name))
                    sem_id = cursor.lastrowid
                    
                    for sub_name, chapters in subjects.items():
                        cursor.execute('INSERT INTO subjects (semester_id, name) VALUES (?, ?)', (sem_id, sub_name))
                        sub_id = cursor.lastrowid
                        
                        for chap_name in chapters:
                            cursor.execute('INSERT INTO chapters (subject_id, name) VALUES (?, ?)', (sub_id, chap_name))

    conn.commit()
    conn.close()
    print("Database initialized and seeded successfully.")

if __name__ == '__main__':
    init_db()
