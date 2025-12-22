import sqlite3

def seed_purbanchal():
    conn = sqlite3.connect('padsala.db')
    cursor = conn.cursor()

    # Get or Create University
    cursor.execute("INSERT OR IGNORE INTO universities (name) VALUES (?)", ("Purbanchal University",))
    cursor.execute("SELECT id FROM universities WHERE name = ?", ("Purbanchal University",))
    uni_id = cursor.fetchone()[0]

    # Get or Create Faculty
    cursor.execute("INSERT OR IGNORE INTO faculties (university_id, name) VALUES (?, ?)", (uni_id, "Engineering"))
    cursor.execute("SELECT id FROM faculties WHERE university_id = ? AND name = ?", (uni_id, "Engineering"))
    fac_id = cursor.fetchone()[0]

    # Get or Create Course
    cursor.execute("INSERT OR IGNORE INTO courses (faculty_id, name) VALUES (?, ?)", (fac_id, "Bachelor in Computer Engineering"))
    cursor.execute("SELECT id FROM courses WHERE faculty_id = ? AND name = ?", (fac_id, "Bachelor in Computer Engineering"))
    course_id = cursor.fetchone()[0]

    data = [
        ("Semester 1", "Mathematics I"), ("Semester 1", "Physics"), ("Semester 1", "English for Technical Communication"),
        ("Semester 1", "Computer Programming"), ("Semester 1", "Fundamental of Computing Technology"),
        ("Semester 1", "Engineering Drawing"), ("Semester 1", "Workshop Technology"),
        
        ("Semester 2", "Mathematics II"), ("Semester 2", "Chemistry"), ("Semester 2", "Object Oriented Programming with C++"),
        ("Semester 2", "Digital Logic"), ("Semester 2", "Basic Electrical Engineering"), ("Semester 2", "Applied Mechanics"),
        
        ("Semester 3", "Mathematics III"), ("Semester 3", "Data Structure and Algorithm"), ("Semester 3", "Object Oriented Analysis and Design"),
        ("Semester 3", "Computer Graphics"), ("Semester 3", "Electronic Devices and Circuits"), ("Semester 3", "Applied Sociology"), ("Semester 3", "Project I"),
        
        ("Semester 4", "Database Management System"), ("Semester 4", "Python Programming"), ("Semester 4", "Discrete Structure"),
        ("Semester 4", "Microprocessor"), ("Semester 4", "Communication System"), ("Semester 4", "Probability and Statistics"),
        
        ("Semester 5", "Algorithm Analysis and Design"), ("Semester 5", "Computer Architecture and Design"), ("Semester 5", "Numerical Methods"),
        ("Semester 5", "Operating System"), ("Semester 5", "Engineering Economics"), ("Semester 5", "Research Methodology"), ("Semester 5", "Project II"),
        
        ("Semester 6", "Artificial Intelligence"), ("Semester 6", "Computer Network"), ("Semester 6", "Internet of Things"),
        ("Semester 6", "Software Engineering"), ("Semester 6", "Theory of Computation"), ("Semester 6", "Elective I"),
        
        ("Semester 7", "Distributed and Cloud Computing"), ("Semester 7", "Information Technology Project Management"),
        ("Semester 7", "Simulation and Modeling"), ("Semester 7", "Elective II"), ("Semester 7", "Elective III"), ("Semester 7", "Project III Part A"),
        
        ("Semester 8", "Cyber Security"), ("Semester 8", "Engineering Professional Practice"), ("Semester 8", "Elective IV"),
        ("Semester 8", "Project III Part B"), ("Semester 8", "Internship"),

        # Elective Lists (Stored as their own "semesters" for the UI picker)
        ("Elective I", "Data Mining and Data Warehousing"), ("Elective I", "Multimedia Technology"), ("Elective I", "Distributed System"),
        ("Elective I", "High Performance Computing"), ("Elective I", "Machine Learning"), ("Elective I", "Cryptography and Network Security"),
        ("Elective I", "Mobile and Sensor Computing"), ("Elective I", "Unix Programming"),

        ("Elective II", "Big Data Technologies"), ("Elective II", "Information and Cyber Security"), ("Elective II", "Compiler Design"),
        ("Elective II", "Java Programming"), ("Elective II", "Deep Learning"), ("Elective II", "Business Intelligence"),
        ("Elective II", "Human Computer Interaction"), ("Elective II", "Real Time Operating System"),

        ("Elective III", "Fault Tolerant System"), ("Elective III", "Software Security"), ("Elective III", "Web Security"),
        ("Elective III", "Quantum Computing"), ("Elective III", "Augmented and Virtual Reality"), ("Elective III", "GIS"),
        ("Elective III", "Advanced Database Programming"),

        ("Elective IV", "Data Science"), ("Elective IV", "Next Generation Network"), ("Elective IV", "Computational Cognitive Science"),
        ("Elective IV", "Agile Software Development"), ("Elective IV", "Blockchain"), ("Elective IV", "Digital Solutions for Climate Change"),
        ("Elective IV", "Automation and Robotics")
    ]

    for sem_name, sub_name in data:
        cursor.execute("INSERT OR IGNORE INTO semesters (course_id, name) VALUES (?, ?)", (course_id, sem_name))
        cursor.execute("SELECT id FROM semesters WHERE course_id = ? AND name = ?", (course_id, sem_name))
        sem_id = cursor.fetchone()[0]
        
        cursor.execute("INSERT OR IGNORE INTO subjects (semester_id, name) VALUES (?, ?)", (sem_id, sub_name))
        sub_id = cursor.lastrowid
        
        # Add a default chapter for newly added subjects if needed (get_chapters takes care of fallbacks)
        cursor.execute("INSERT INTO chapters (subject_id, name) VALUES (?, ?)", (sub_id, "Complete Purbanchal Syllabus Preparation"))

    conn.commit()
    conn.close()
    print("Purbanchal University data seeded successfully.")

if __name__ == '__main__':
    seed_purbanchal()
