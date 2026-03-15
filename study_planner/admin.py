from django.contrib import admin
from .models import University, Faculty, Course, Semester, Subject, Chapter, CustomUser, SavedSchedule, TopicMastery, SessionStats

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'xp', 'streak', 'is_pro')

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'university')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty')

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'course')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'semester', 'base_difficulty', 'is_elective')
    list_filter = ('semester', 'is_elective')
    search_fields = ('name',)

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')
    search_fields = ('name', 'subject__name')

@admin.register(SavedSchedule)
class SavedScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')

admin.site.register(TopicMastery)
admin.site.register(SessionStats)
