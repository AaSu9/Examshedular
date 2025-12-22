import sqlite3

def check_db():
    conn = sqlite3.connect('padsala.db')
    cursor = conn.cursor()
    
    print("Universities:")
    for row in cursor.execute("SELECT * FROM universities"):
        print(row)
        
    print("\nPurbanchal Faculties:")
    for row in cursor.execute("SELECT * FROM faculties WHERE university_id = (SELECT id FROM universities WHERE name LIKE '%Purbanchal%')"):
        print(row)
        
    print("\nEngineering Courses:")
    for row in cursor.execute("SELECT * FROM courses WHERE faculty_id IN (SELECT id FROM faculties WHERE name = 'Engineering')"):
        print(row)
        
    print("\nSemester Samples for Computer Engineering:")
    for row in cursor.execute("SELECT * FROM semesters WHERE course_id IN (SELECT id FROM courses WHERE name LIKE '%Computer%') LIMIT 5"):
        print(row)
        
    print("\nSubject Samples:")
    for row in cursor.execute("SELECT * FROM subjects LIMIT 10"):
        print(row)
        
    conn.close()

if __name__ == '__main__':
    check_db()
