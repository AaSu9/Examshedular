from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/metadata', views.get_metadata, name='get_metadata'),
    path('api/generate-schedule', views.generate_schedule, name='generate_schedule'),
    path('api/replan-day', views.replan_day, name='replan_day'),
    path('api/sync/schedules', views.get_schedules, name='get_schedules'),
    path('api/sync/save', views.save_schedule, name='save_schedule'),
    path('api/sync/delete', views.delete_schedule, name='delete_schedule'),
    path('api/v17/log-session', views.log_session_v17, name='log_session_v17'),
    path('api/v17/analytics', views.get_analytics_v17, name='get_analytics_v17'),
    path('api/v17/sync-xp', views.sync_xp, name='sync_xp'),
    path('api/v17/leaderboard', views.get_leaderboard, name='get_leaderboard'),
    path('api/auth/status', views.auth_status, name='auth_status'),
    path('api/auth/login', views.login_user, name='login_user'),
    path('api/auth/register', views.register_user, name='register_user'),
    path('api/auth/logout', views.logout_user, name='logout_user'),
    path('api/exam-plan/', views.api_exam_plan, name='api_exam_plan'),
    path('api/today-plan/', views.api_today_plan, name='api_today_plan'),
    path('api/update-mastery/', views.api_update_mastery, name='api_update_mastery'),
]
