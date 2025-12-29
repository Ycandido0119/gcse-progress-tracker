from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Subject URLs
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('subjects/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('subjects/<int:pk>/edit', views.edit_subject, name='edit_subject'),
    path('subjects/<int:pk>/delete', views.delete_subject, name='delete_subject'),

    # Feedback URLs
    path('subjects/<int:subject_pk>/feedback/add/', views.add_feedback, name='add_feedback'),
    path('feedback/<int:pk>/edit/', views.edit_feedback, name='edit_feedback'),
    path('feedback/<int:pk>/delete/', views.delete_feedback, name='delete_feedback'),
]