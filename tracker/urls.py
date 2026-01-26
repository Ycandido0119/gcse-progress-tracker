from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Registration URLs
    path('accounts/register/', views.register, name='register'),

    # Subject URLs
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('subjects/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('subjects/<int:pk>/edit', views.edit_subject, name='edit_subject'),
    path('subjects/<int:pk>/delete', views.delete_subject, name='delete_subject'),

    # Feedback URLs
    path('subjects/<int:subject_pk>/feedback/add/', views.add_feedback, name='add_feedback'),
    path('feedback/<int:pk>/edit/', views.edit_feedback, name='edit_feedback'),
    path('feedback/<int:pk>/delete/', views.delete_feedback, name='delete_feedback'),

    # Term Goal URLS
    path('subjects/<int:subject_pk>/goals/add', views.add_term_goal, name='add_term_goal'),
    path('goals/<int:pk>/edit/', views.edit_term_goal, name='edit_term_goal'),
    path('goals/<int:pk>/delete/', views.delete_term_goal, name='delete_term_goal'),

    # Study Sessions URLs
    path('subjects/<int:subject_pk>/sessions/add/', views.add_study_session, name='add_study_session'),
    path('sessions/<int:pk>/edit/', views.edit_study_session, name='edit_study_session'),
    path('sessions/<int:pk>/delete/', views.delete_study_session, name='delete_study_session'),

    # Roadmap URLS
    path('subjects/<int:subject_pk>/roadmap/generate/', views.generate_roadmap, name='generate_roadmap'),
    path('roadmaps/<int:pk>/', views.roadmap_detail, name='roadmap_detail'),
    path('roadmaps/<int:pk>/delete/', views.delete_roadmap, name='delete_roadmap'),
    path('roadmap-steps/<int:pk>/', views.roadmap_step_detail, name='roadmap_step_detail'),

    # Roadmap Progress URLs
    path('roadmap-items/<int:pk>/toggle/', views.toggle_checklist_item, name='toggle_checklist_item'),

    # Parent Dashboard URLs
    path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('parent/student/<int:student_id>/', views.parent_student_detail, name='parent_student_detail'),

    # Alerts URLs
    path('parent/alerts/', views.parent_alert_history, name='parent_alert_history'),
    path('parent/alerts/<int:alert_id>/read/', views.mark_alert_read, name='mark_alert_read'),
    path('parent/alerts/read-all/', views.mark_all_alerts_read, name='mark_all_alerts_read'),
]