import sqlite3

def rebuild_db():
    conn = sqlite3.connect('padsala.db')
    cursor = conn.cursor()

    # Clean start
    cursor.execute('DROP TABLE IF EXISTS chapters')
    cursor.execute('DROP TABLE IF EXISTS subjects')
    cursor.execute('DROP TABLE IF EXISTS semesters')
    cursor.execute('DROP TABLE IF EXISTS courses')
    cursor.execute('DROP TABLE IF EXISTS faculties')
    cursor.execute('DROP TABLE IF EXISTS universities')

    # Re-create tables
    cursor.execute('CREATE TABLE universities (id INTEGER PRIMARY KEY, name TEXT UNIQUE)')
    cursor.execute('CREATE TABLE faculties (id INTEGER PRIMARY KEY, university_id INTEGER, name TEXT, FOREIGN KEY(university_id) REFERENCES universities(id))')
    cursor.execute('CREATE TABLE courses (id INTEGER PRIMARY KEY, faculty_id INTEGER, name TEXT, FOREIGN KEY(faculty_id) REFERENCES faculties(id))')
    cursor.execute('CREATE TABLE semesters (id INTEGER PRIMARY KEY, course_id INTEGER, name TEXT, FOREIGN KEY(course_id) REFERENCES courses(id))')
    cursor.execute('CREATE TABLE subjects (id INTEGER PRIMARY KEY, semester_id INTEGER, name TEXT, FOREIGN KEY(semester_id) REFERENCES semesters(id))')
    cursor.execute('CREATE TABLE chapters (id INTEGER PRIMARY KEY, subject_id INTEGER, name TEXT, FOREIGN KEY(subject_id) REFERENCES subjects(id))')

    # Seed Unified Purbanchal University Data
    cursor.execute("INSERT INTO universities (name) VALUES (?)", ("Purbanchal University (PU)",))
    uni_id = cursor.lastrowid

    cursor.execute("INSERT INTO faculties (university_id, name) VALUES (?, ?)", (uni_id, "Engineering"))
    fac_id = cursor.lastrowid

    cursor.execute("INSERT INTO courses (faculty_id, name) VALUES (?, ?)", (fac_id, "Bachelor in Computer Engineering"))
    course_id = cursor.lastrowid

    purbanchal_data = {
        "Semester 1": ["Mathematics I", "Physics", "English for Technical Communication", "Computer Programming", "Fundamental of Computing Technology", "Engineering Drawing", "Workshop Technology"],
        "Semester 2": ["Mathematics II", "Chemistry", "Object Oriented Programming with C++", "Digital Logic", "Basic Electrical Engineering", "Applied Mechanics"],
        "Semester 3": ["Mathematics III", "Data Structure and Algorithm", "Object Oriented Analysis and Design", "Computer Graphics", "Electronic Devices and Circuits", "Applied Sociology", "Project I"],
        "Semester 4": ["Database Management System", "Python Programming", "Discrete Structure", "Microprocessor", "Communication System", "Probability and Statistics"],
        "Semester 5": ["Algorithm Analysis and Design", "Computer Architecture and Design", "Numerical Methods", "Operating System", "Engineering Economics", "Research Methodology", "Project II"],
        "Semester 6": ["Artificial Intelligence", "Computer Network", "Internet of Things", "Software Engineering", "Theory of Computation", "Elective I"],
        "Semester 7": ["Distributed and Cloud Computing", "Information Technology Project Management", "Simulation and Modeling", "Elective II", "Elective III", "Project III Part A"],
        "Semester 8": ["Cyber Security", "Engineering Professional Practice", "Elective IV", "Project III Part B", "Internship"],
        "Elective I": ["Data Mining and Data Warehousing", "Multimedia Technology", "Distributed System", "High Performance Computing", "Machine Learning", "Cryptography and Network Security", "Mobile and Sensor Computing", "Unix Programming"],
        "Elective II": ["Big Data Technologies", "Information and Cyber Security", "Compiler Design", "Java Programming", "Deep Learning", "Business Intelligence", "Human Computer Interaction", "Real Time Operating System"],
        "Elective III": ["Fault Tolerant System", "Software Security", "Web Security", "Quantum Computing", "Augmented and Virtual Reality", "GIS", "Advanced Database Programming"],
        "Elective IV": ["Data Science", "Next Generation Network", "Computational Cognitive Science", "Agile Software Development", "Blockchain", "Digital Solutions for Climate Change", "Automation and Robotics"]
    }

    for sem_name, subs in purbanchal_data.items():
        cursor.execute("INSERT INTO semesters (course_id, name) VALUES (?, ?)", (course_id, sem_name))
        sem_id = cursor.lastrowid
        for sub_name in subs:
            cursor.execute("INSERT INTO subjects (semester_id, name) VALUES (?, ?)", (sem_id, sub_name))
            sub_id = cursor.lastrowid
            # Add at least one chapter for the automatic system
            cursor.execute("INSERT INTO chapters (subject_id, name) VALUES (?, ?)", (sub_id, "Focus Study Block"))

    # Add other placeholder unis so the app isn't empty
    cursor.execute("INSERT INTO universities (name) VALUES (?)", ("Tribhuvan University (TU)",))
    tu_id = cursor.lastrowid
    cursor.execute("INSERT INTO faculties (university_id, name) VALUES (?, ?)", (tu_id, "Science & Technology"))
    tu_fac_id = cursor.lastrowid
    cursor.execute("INSERT INTO courses (faculty_id, name) VALUES (?, ?)", (tu_fac_id, "B.Sc. CSIT"))
    tu_course_id = cursor.lastrowid
    cursor.execute("INSERT INTO semesters (course_id, name) VALUES (?, ?)", (tu_course_id, "1st Sem"))
    tu_sem_id = cursor.lastrowid
    cursor.execute("INSERT INTO subjects (semester_id, name) VALUES (?, ?)", (tu_sem_id, "Introduction to IT"))

    conn.commit()
    conn.close()
    print("Database rebuilt with unified Purbanchal University data.")

if __name__ == '__main__':
    rebuild_db()
