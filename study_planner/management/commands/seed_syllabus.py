from django.core.management.base import BaseCommand
from study_planner.models import University, Faculty, Course, Semester, Subject, Chapter

class Command(BaseCommand):
    help = 'Seeds the syllabus data for PU'

    def handle(self, *args, **kwargs):
        # 1. Purbanchal University
        uni, _ = University.objects.get_or_create(name="Purbanchal University (PU)")
        fac, _ = Faculty.objects.get_or_create(university=uni, name="Engineering")
        course, _ = Course.objects.get_or_create(faculty=fac, name="Bachelor in Computer Engineering")

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
            sem, _ = Semester.objects.get_or_create(course=course, name=sem_name)
            for sub_name in subs:
                sub, _ = Subject.objects.get_or_create(semester=sem, name=sub_name)
                # Add a default focus chapter
                Chapter.objects.get_or_create(subject=sub, name="Focus Study Block")

        # 2. Tribhuvan University (TU) Placeholder
        uni_tu, _ = University.objects.get_or_create(name="Tribhuvan University (TU)")
        fac_tu, _ = Faculty.objects.get_or_create(university=uni_tu, name="Science & Technology")
        course_tu, _ = Course.objects.get_or_create(faculty=fac_tu, name="B.Sc. CSIT")
        sem_tu, _ = Semester.objects.get_or_create(course=course_tu, name="1st Sem")
        Subject.objects.get_or_create(semester=sem_tu, name="Introduction to IT")

        self.stdout.write(self.style.SUCCESS('Successfully seeded syllabus data'))
