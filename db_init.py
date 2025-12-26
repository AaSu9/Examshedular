import sqlite3
import json

# The existing database structure
SYLLABUS_DATA = {
    "Purbanchal University (PoU)": {
        "Engineering": {
            "Bachelor in Computer Engineering": {
                "Semester 1": {
                    "Mathematics I": ["Matrix", "Calculus", "Vectors", "Co-ordinate Geometry"],
                    "Physics": ["Mechanics", "Waves & Oscillations", "Optics", "Electromagnetism"],
                    "English for Technical Communication": ["Grammar", "Technical Writing", "Presentation Skills"],
                    "Computer Programming": ["Tokens & Syntax", "Control Statements", "Functions", "Arrays", "Pointers", "File Handling"],
                    "Fundamental of Computing Technology": ["Architecture", "Operating Systems", "Networking", "Internet Intro"],
                    "Engineering Drawing": ["Scale", "Projection", "Sectioning", "Isometric"],
                    "Workshop Technology": ["Carpentry", "Foundry", "Welding", "Machine Shop"]
                },
                "Semester 2": {
                    "Mathematics II": ["Calculus II", "Differential Equations", "Laplace Transform"],
                    "Chemistry": ["Organic Chemistry", "Metals & Alloys", "Environmental Chemistry"],
                    "Object Oriented Programming with C++": ["Classes & Objects", "Inheritance", "Polymorphism", "Templates"],
                    "Digital Logic": ["Gates", "K-Maps", "Sequential Circuits", "Counters"],
                    "Basic Electrical Engineering": ["AC/DC Circuits", "Electromagnetism", "Transformers"],
                    "Applied Mechanics": ["Statics", "Centroid", "Friction", "Dynamics"]
                },
                "Semester 3": {
                    "Mathematics III": ["Probability", "Statistics", "Fourier Series"],
                    "Data Structure and Algorithm": ["Linked Lists", "Stacks & Queues", "Trees", "Graphs", "Sorting"],
                    "Object Oriented Analysis and Design": ["UML Basics", "Use Case", "Class Diagrams"],
                    "Computer Graphics": ["Output Primitives", "2D/3D Transformations", "Shading"],
                    "Electronic Devices and Circuits": ["Semiconductors", "BJT", "FET", "Amplifiers"],
                    "Applied Sociology": ["Social Change", "Culture", "Structure"],
                    "Project I": ["Documentation", "Implementation", "Presentation"]
                },
                "Semester 4": {
                    "Database Management System": ["ER Model", "SQL", "Normalization", "Concurrency"],
                    "Python Programming": ["Data Structures", "Modules", "Web Scraping", "API"],
                    "Discrete Structure": ["Logic", "Set Theory", "Graph Theory", "Trees"],
                    "Microprocessor": ["Intel 8085", "Assembly Language", "Interrupts", "I/O Interfacing"],
                    "Communication System": ["Signals", "Modulation", "Transmission Media"],
                    "Probability and Statistics": ["Distributions", "Sampling", "Hypothesis Testing"]
                },
                "Semester 5": {
                    "Algorithm Analysis and Design": ["Complexity", "Dynamic Programming", "Greedy Algorithms"],
                    "Computer Architecture and Design": ["Control Unit", "Pipelining", "Memory Hierarchy"],
                    "Numerical Methods": ["Interpolation", "Linear Equations", "Integration"],
                    "Operating System": ["Processes", "Memory Management", "File Systems"],
                    "Engineering Economics": ["Time Value of Money", "Investment Analysis", "Risk Analysis"],
                    "Research Methodology": ["Methods", "Ethics", "Proposal Writing"],
                    "Project II": ["Design Phase", "Alpha Testing", "Reporting"]
                },
                "Semester 6": {
                    "Artificial Intelligence": ["Search Techniques", "Expert Systems", "Neural Networks"],
                    "Computer Network": ["OSI Layers", "TCP/IP", "Routing", "Security"],
                    "Internet of Things": ["Sensors", "Arduino/RPi", "Cloud Protocol"],
                    "Software Engineering": ["Models", "Requirements", "Testing", "Maintenance"],
                    "Theory of Computation": ["Automata", "CFG", "Turing Machines"],
                    "Elective I": ["Data Mining", "Multimedia", "Distributed Systems"]
                },
                "Semester 7": {
                    "Distributed and Cloud Computing": ["Virtualization", "AWS/Azure", "Parallelism"],
                    "Information Technology Project Management": ["Planning", "Agile", "Cost Management"],
                    "Simulation and Modeling": ["System Analysis", "Queuing Models", "Validation"],
                    "Elective II": ["Big Data", "Compiler Design", "Deep Learning"],
                    "Elective III": ["Fault Tolerant", "Software Security", "GIS"],
                    "Project III Part A": ["Architecture", "Database Design", "Initial Code"]
                },
                "Semester 8": {
                    "Cyber Security": ["Network Security", "Malware Analysis", "Forensics"],
                    "Engineering Professional Practice": ["Ethics", "Law", "Entrepreneurship"],
                    "Elective IV": ["Data Science", "Blockchain", "Robotics"],
                    "Project III Part B": ["Optimization", "Final testing", "Thesis"],
                    "Internship": ["Industry Experience", "Reflective Report"]
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
    
    # Auth & Multi-Timelin    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        xp INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        avatar TEXT DEFAULT 'default',
        is_pro BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

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
