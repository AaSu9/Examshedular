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

    # First, collect unique semester names
    semesters_data = [
        "Semester 1", "Semester 2", "Semester 3", "Semester 4",
        "Semester 5", "Semester 6", "Semester 7", "Semester 8",
        "Elective I", "Elective II", "Elective III", "Elective IV"
    ]
    
    # Create semesters ONCE
    semester_ids = {}
    for sem_name in semesters_data:
        cursor.execute("INSERT OR IGNORE INTO semesters (course_id, name) VALUES (?, ?)", (course_id, sem_name))
        cursor.execute("SELECT id FROM semesters WHERE course_id = ? AND name = ? LIMIT 1", (course_id, sem_name))
        semester_ids[sem_name] = cursor.fetchone()[0]
    
    # Now add subjects to the semesters
    subjects_data = {
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
    
    for sem_name, subjects in subjects_data.items():
        sem_id = semester_ids[sem_name]
        for sub_name in subjects:
            cursor.execute("INSERT OR IGNORE INTO subjects (semester_id, name) VALUES (?, ?)", (sem_id, sub_name))

    # FINAL CLEANUP: Remove all universities except PU and TU as requested
    cursor.execute("DELETE FROM universities WHERE name NOT LIKE 'Purbanchal%' AND name NOT LIKE 'Tribhuvan%'")
    
    conn.commit()
    conn.close()
    print("Cleanup complete. Purbanchal University data seeded successfully.")

if __name__ == '__main__':
    seed_purbanchal()
