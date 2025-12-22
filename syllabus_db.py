import sqlite3

DATABASE = 'padsala.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_metadata():
    """Reconstructs the nested dictionary structure from the database for the frontend wizard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # We could do a complex join, but for a metadata tree, a few simple queries are fine
    data = {}
    
    unis = cursor.execute('SELECT id, name FROM universities').fetchall()
    for uni in unis:
        uni_name = uni['name']
        data[uni_name] = {}
        
        facs = cursor.execute('SELECT id, name FROM faculties WHERE university_id = ?', (uni['id'],)).fetchall()
        for fac in facs:
            fac_name = fac['name']
            if fac_name not in data[uni_name]:
                data[uni_name][fac_name] = {}
            
            courses = cursor.execute('SELECT id, name FROM courses WHERE faculty_id = ?', (fac['id'],)).fetchall()
            for course in courses:
                course_name = course['name']
                if course_name not in data[uni_name][fac_name]:
                    data[uni_name][fac_name][course_name] = {}
                
                sems = cursor.execute('SELECT id, name FROM semesters WHERE course_id = ?', (course['id'],)).fetchall()
                for sem in sems:
                    sem_name = sem['name']
                    if sem_name not in data[uni_name][fac_name][course_name]:
                        data[uni_name][fac_name][course_name][sem_name] = {}
                    
                    subs = cursor.execute('SELECT id, name FROM subjects WHERE semester_id = ?', (sem['id'],)).fetchall()
                    for sub in subs:
                        sub_name = sub['name']
                        # Chapters are fetched only when specific subject details are needed
                        data[uni_name][fac_name][course_name][sem_name][sub_name] = [] 
                        
    conn.close()
    return data

def get_chapters(university, faculty, course, semester, subject):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT c.name FROM chapters c
    JOIN subjects s ON c.subject_id = s.id
    JOIN semesters sem ON s.semester_id = sem.id
    JOIN courses crs ON sem.course_id = crs.id
    JOIN faculties f ON crs.faculty_id = f.id
    JOIN universities u ON f.university_id = u.id
    WHERE u.name = ? AND f.name = ? AND crs.name = ? AND sem.name = ? AND s.name = ?
    """
    
    rows = cursor.execute(query, (university, faculty, course, semester, subject)).fetchall()
    chapters = [row['name'] for row in rows]
    conn.close()

    if chapters:
        return chapters
    
    # Smart Generic Generator (Fallback)
    if "math" in subject.lower():
        return ["Limit & Continuity", "Derivatives", "Integration", "Matrices", "Exam Practice"]
    if "program" in subject.lower() or "code" in subject.lower() or "java" in subject.lower() or "python" in subject.lower() or " c " in f" {subject.lower()} ":
        return ["Syntax & Variables", "Control Logic", "Loops", "Functions/Methods", "Debugging"]
    if "account" in subject.lower():
        return ["Ledger Posting", "Financial Statements", "Cash Flow", "Auditing", "Revision"]
    if "physics" in subject.lower():
        return ["Mechanics", "Thermodynamics", "Optics", "Electrostatics", "Mock Exam"]
    
    return ["Introduction", "Core Concepts", "Practical Application", "Case Studies", "Final Review"]
