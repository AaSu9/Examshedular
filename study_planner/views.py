from django.shortcuts import render
from django.db.models import Avg, Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import University, Faculty, Course, Semester, Subject, Chapter, SavedSchedule, CustomUser, TopicMastery, SessionStats
from planner import generate_study_plan, get_micro_plan
import json
from datetime import datetime, timedelta
import nepali_datetime
from django.contrib.auth import authenticate, login, logout

def index(request):
    return render(request, 'index.html')

def get_metadata(request):
    """Reconstructs the nested dictionary structure from the database for the frontend wizard."""
    data = {}
    unis = University.objects.prefetch_related('faculties__courses__semesters__subjects').all()
    
    for uni in unis:
        uni_data = {}
        for fac in uni.faculties.all():
            fac_data = {}
            for course in fac.courses.all():
                course_data = {}
                for sem in course.semesters.all():
                    sem_data = {}
                    for sub in sem.subjects.all():
                        sem_data[sub.name] = {
                            "id": sub.id,
                            "difficulty": sub.base_difficulty,
                            "is_elective": sub.is_elective
                        }
                    course_data[sem.name] = sem_data
                fac_data[course.name] = course_data
            uni_data[fac.name] = fac_data
        data[uni.name] = uni_data

    # Add Current BS Date
    now = datetime.now()
    try:
        np_now = nepali_datetime.date.from_datetime_date(now.date())
        data['today_bs'] = np_now.strftime('%Y-%m-%d')
    except:
        data['today_bs'] = "2082-09-05"
    
    return JsonResponse(data)

@csrf_exempt
def generate_schedule(request):
    if request.method != 'POST': return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
        exams = data.get('exams', [])
        
        # Inject chapters if missing (from DB)
        for ex in exams:
            if not ex.get('chapters') or len(ex['chapters']) == 0:
                sub = Subject.objects.filter(name=ex['name']).first()
                if sub:
                    ex['chapters'] = list(sub.chapters.values_list('name', flat=True))
                if not ex['chapters']:
                    ex['chapters'] = ["Introduction", "Core Concepts", "Practical Application", "Final Review"]
        
        total_hours = int(data.get('daily_hours', 8))
        session_mins = int(data.get('session_mins', 90))
        break_mins = int(data.get('break_mins', 15))
        start_time = data.get('start_time', "06:00")

        # Mastery mapping
        topic_mastery_map = {}
        if request.user.is_authenticated:
            mastery_data = TopicMastery.objects.filter(user=request.user)
            for m in mastery_data:
                if m.subject not in topic_mastery_map: topic_mastery_map[m.subject] = {}
                topic_mastery_map[m.subject][m.topic] = m.mastery_score

        schedule = generate_study_plan(
            exams, 
            daily_study_hours=total_hours,
            session_mins=session_mins,
            break_mins=break_mins,
            start_time=start_time,
            topic_mastery_map=topic_mastery_map
        )
        return JsonResponse(schedule, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def replan_day(request):
    if request.method != 'POST': return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
        tasks = get_micro_plan(
            data.get('subject'),
            data.get('focus', 'Revision'),
            int(data.get('hours', 8)),
            int(data.get('session_mins', 90)),
            int(data.get('break_mins', 15)),
            data.get('start_time', "06:00")
        )
        return JsonResponse({"tasks": tasks})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def get_schedules(request):
    if not request.user.is_authenticated: return JsonResponse({"error": "Unauthorized"}, status=401)
    schedules = SavedSchedule.objects.filter(user=request.user).order_by('-created_at')
    
    nepal_now = datetime.utcnow() + timedelta(hours=5, minutes=45)
    today_ad_str = nepal_now.date().strftime("%Y-%m-%d")

    results = []
    for s in schedules:
        results.append({
            "name": s.name,
            "data": s.data,
            "inputs": s.inputs
        })
    return JsonResponse(results, safe=False)

@csrf_exempt
def save_schedule(request):
    if not request.user.is_authenticated: return JsonResponse({"error": "Unauthorized"}, status=401)
    if request.method != 'POST': return JsonResponse({"error": "Method not allowed"}, status=405)
    data = json.loads(request.body)
    SavedSchedule.objects.update_or_create(
        user=request.user, 
        name=data.get('name'),
        defaults={'data': data.get('data'), 'inputs': data.get('inputs')}
    )
    return JsonResponse({"success": True})

@csrf_exempt
def delete_schedule(request):
    if not request.user.is_authenticated: return JsonResponse({"error": "Unauthorized"}, status=401)
    data = json.loads(request.body)
    SavedSchedule.objects.filter(user=request.user, name=data.get('name')).delete()
    return JsonResponse({"success": True})

@csrf_exempt
def log_session_v17(request):
    if not request.user.is_authenticated: return JsonResponse({"error": "Unauthorized"}, status=401)
    data = json.loads(request.body)
    score = data.get('focus_score', 100)
    
    SessionStats.objects.create(
        user=request.user,
        subject=data.get('subject'),
        topic=data.get('topic'),
        duration_mins=data.get('duration_mins'),
        focus_score=score,
        distraction_count=data.get('distractions', 0),
        idle_seconds=data.get('idle_seconds', 0)
    )
    
    mastery_gain = 5 if score > 80 else (2 if score > 50 else 0)
    tm, created = TopicMastery.objects.get_or_create(
        user=request.user,
        subject=data.get('subject'),
        topic=data.get('topic')
    )
    tm.mastery_score = min(100, tm.mastery_score + mastery_gain)
    tm.save()
    
    return JsonResponse({"success": True, "mastery_gain": mastery_gain})

def get_analytics_v17(request):
    if not request.user.is_authenticated: return JsonResponse({"error": "Unauthorized"}, status=401)
    stats = SessionStats.objects.filter(user=request.user)
    avg_focus = stats.aggregate(Avg('focus_score'))['focus_score__avg'] or 0
    burnout = "LOW"
    # Placeholder for counts...
    return JsonResponse({"avg_focus": avg_focus, "burnout_risk": burnout, "mastery": {}})

@csrf_exempt
def sync_xp(request):
    if not request.user.is_authenticated: return JsonResponse({"error": "Unauthorized"}, status=401)
    data = json.loads(request.body)
    request.user.xp = data.get('xp', 0)
    request.user.streak = data.get('streak', 0)
    request.user.save()
    return JsonResponse({"success": True})

def get_leaderboard(request):
    top = CustomUser.objects.order_by('-xp')[:10]
    leaderboard = [{"username": u.username, "xp": u.xp, "streak": u.streak} for u in top]
    return JsonResponse({"leaderboard": leaderboard, "user_rank": 0})

@csrf_exempt
def login_user(request):
    if request.method != 'POST': return JsonResponse({"error": "Method not allowed"}, status=405)
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')
    
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        # Check if administrative access is needed
        redirect_url = None
        if user.is_staff or user.is_superuser:
            redirect_url = '/admin/'
            
        return JsonResponse({
            "success": True, 
            "user": {"username": user.username, "email": user.email},
            "redirect": redirect_url
        })
    return JsonResponse({"success": False, "error": "Invalid credentials"}, status=401)

@csrf_exempt
def register_user(request):
    if request.method != 'POST': return JsonResponse({"error": "Method not allowed"}, status=405)
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')
    
    if CustomUser.objects.filter(username=username).exists():
        return JsonResponse({"success": False, "error": "Identity already taken"}, status=400)
    
    user = CustomUser.objects.create_user(username=username, password=password)
    return JsonResponse({"success": True})

def logout_user(request):
    logout(request)
    return JsonResponse({"success": True})

def auth_status(request):
    if request.user.is_authenticated:
        return JsonResponse({"logged_in": True, "username": request.user.username})
    return JsonResponse({"logged_in": False})
