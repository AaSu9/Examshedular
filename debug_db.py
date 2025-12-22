import sqlite3

conn = sqlite3.connect('padsala.db')
cursor = conn.cursor()

print("Universities:")
for row in cursor.execute("SELECT * FROM universities"):
    print(row)

print("\nFaculties for Purbanchal University (PU):")
# Assumes PU ID is 1 based on previous output
for row in cursor.execute("SELECT * FROM faculties WHERE university_id = 1"):
    print(row)

print("\nCourses for Faculty ID 1 (Engineering):")
for row in cursor.execute("SELECT * FROM courses WHERE faculty_id = 1"):
    print(row)

print("\nSemesters for Course ID 1 (Bachelor in Computer Engineering):")
for row in cursor.execute("SELECT * FROM semesters WHERE course_id = 1"):
    print(row)

conn.close()
