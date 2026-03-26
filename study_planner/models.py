from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    xp = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)
    avatar = models.CharField(max_length=50, default='default')
    is_pro = models.BooleanField(default=False)
    last_study_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username

class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    def __str__(self): return self.name

class Faculty(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='faculties')
    name = models.CharField(max_length=255)
    def __str__(self): return f"{self.university.name} - {self.name}"

class Course(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=255)
    def __str__(self): return f"{self.faculty.name} - {self.name}"

class Semester(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='semesters')
    name = models.CharField(max_length=255)
    def __str__(self): return f"{self.course.name} - {self.name}"

class Subject(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=255)
    base_difficulty = models.IntegerField(default=2)
    exam_date = models.DateField(null=True, blank=True)
    is_elective = models.BooleanField(default=False)
    def __str__(self): return self.name

class Chapter(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='chapters')
    name = models.CharField(max_length=255)
    def __str__(self): return f"{self.subject.name} - {self.name}"

class SavedSchedule(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='schedules')
    name = models.CharField(max_length=255)
    data = models.JSONField()
    inputs = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.user.username} - {self.name}"

class TopicMastery(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='mastery')
    subject = models.CharField(max_length=255)
    topic = models.CharField(max_length=255)
    mastery_score = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

class SessionStats(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='session_stats')
    subject = models.CharField(max_length=255)
    topic = models.CharField(max_length=255)
    duration_mins = models.IntegerField(null=True, blank=True)
    focus_score = models.IntegerField(default=100)
    distraction_count = models.IntegerField(default=0)
    idle_seconds = models.IntegerField(default=0)
    abandoned = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class StudyPlan(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='study_plans')
    date = models.DateField()
    subject = models.CharField(max_length=255)
    topic = models.CharField(max_length=255, null=True, blank=True)
    duration_mins = models.IntegerField(default=0)
    plan_type = models.CharField(max_length=50, default='study') # 'study' or 'revision' or 'exam'
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date']
        
    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.subject} ({self.plan_type})"
