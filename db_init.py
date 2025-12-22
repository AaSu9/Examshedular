import sqlite3
import json

# The existing database structure
SYLLABUS_DATA = {
    "Tribhuvan University (TU)": {
        "Science & Technology": {
            "B.Sc. CSIT": {
                "1st Sem": {
                    "Introduction to IT": ["IT Fundamentals", "Hardware & Software", "Input/Output", "Data Storage", "Networking"],
                    "C Programming": ["Tokens & Data Types", "Control Statements", "Functions", "Arrays", "Pointers", "File Handling"],
                    "Digital Logic": ["Number Systems", "Boolean Algebra", "Logic Gates", "Combinational Circuits", "Sequential Circuits"],
                    "Mathematics I": ["Set Theory", "Functions & Graphs", "Matrix & Determinants", "Limits", "Derivatives"],
                    "Physics": ["Mechanics", "Heat & Thermodynamics", "Optics", "Electrostatics"]
                },
                "2nd Sem": {
                    "Discrete Structure": ["Logic & Proofs", "Sets & Functions", "Graph Theory", "Trees", "Combinatorics"],
                    "Object Oriented Programming": ["Classes & Objects", "Inheritance", "Polymorphism", "Templates"],
                    "Microprocessor": ["Intel 8085 Architecture", "Instruction Set", "Assembly Language", "Interrupts"],
                    "Data Structures & Algorithms": ["Linked Lists", "Stacks & Queues", "Trees", "Sorting & Searching"],
                    "Mathematics II": ["Integration", "Differential Equations", "Vectors", "Complex Numbers"]
                }
            },
            "BIT": {
                "1st Sem": {
                    "Introduction to IT": ["IT Basics", "Digital Ethics", "E-governance"],
                    "Programming Concepts": ["Logic Building", "Syntax", "Variables"],
                    "Basic Mathematics": ["Calculus", "Linear Algebra"]
                }
            },
            "Engineering (B.E. Computer)": {
                "1st Year (I)": {
                    "Applied Mechanics": ["Forces", "Centroid", "Friction"],
                    "Basic Electrical Eng": ["DC Circuits", "AC Circuits", "Magnetic Circuits"],
                    "Engineering Physics": ["Wave Motion", "Optics", "Solid State"],
                    "Eng. Mathematics I": ["Differential Calculus", "Integral Calculus"]
                }
            }
        },
        "Management": {
            "BBA": {
                "1st Sem": {
                    "Macroeconomics": ["GDP", "Inflation", "Fiscal Policy"],
                    "English": ["Communication Skills", "Business Letter", "Presentation"],
                    "Financial Accounting": ["Trial Balance", "Adjustment Entries", "Financial Statements"]
                }
            },
            "BBS": {
                "1st Year": {
                    "Business English": ["Business Communication", "Report Writing"],
                    "Business Statistics": ["Data Representation", "Probability", "Testing"],
                    "Business Economics": ["Market Mechanism", "Production Theory"]
                }
            }
        }
    },
    "Pokhara University (PU)": {
        "Science & Technology": {
            "BCIS": {
                "1st Sem": {
                    "Introduction to Information System": ["IS Concepts", "E-commerce", "Database Management"],
                    "Digital Logic": ["Gates", "K-maps", "Registers"]
                }
            },
            "B.E. Software": {
                "1st Sem": {
                    "Fundamentals of Engineering": ["Problem Solving", "Ethics"],
                    "Computer Programming": ["Syntax", "Modular Programming"]
                }
            }
        },
        "Management": {
            "BBA": {
                "1st Sem": {
                    "Business Communication": ["Formal Letter", "Technical Writing"],
                    "Principles of Management": ["Planning", "Budgeting", "KPIs"]
                }
            }
        }
    },
    "Kathmandu University (KU)": {
        "Engineering": {
            "B.E. Computer Engineering": {
                "1st Year (I)": {
                    "Physics": ["Quantum Mechanics", "Electromagnetism"],
                    "Calculus": ["Single Variable Calculus", "Multi-variable Calculus"]
                }
            }
        },
        "Management": {
            "BBA": {
                "1st Sem": {
                    "Critical Thinking": ["Logic Analysis", "Argumentation"]
                }
            }
        }
    },
    "Purbanchal University (PoU)": {
        "Engineering": {
            "B.E. Civil": {
                "1st Sem": {
                    "Drawing": ["Scale", "Projection", "Sectioning"]
                }
            }
        }
    },
    "Agriculture & Forestry University (AFU)": {
        "Agriculture": {
            "B.Sc. Agriculture": {
                "1st Sem": {
                    "Agronomy": ["Crop Production", "Soil Science Basics"],
                    "Horticulture": ["Fruit Sciences", "Vegetable Sciences"]
                }
            }
        }
    },
    "Mid-Western University (MWU)": {
        "Humanities": {
            "BA Social Work": {
                "1st Sem": {
                    "Sociology": ["Social Change", "Culture", "Structure"]
                }
            }
        }
    },
    "Far-Western University (FWU)": {
        "Education": {
            "B.Ed. Computer": {
                "1st Sem": {
                    "Instructional Tech": ["E-learning", "Pedagogy"]
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
