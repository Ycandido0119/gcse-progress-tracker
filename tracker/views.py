from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from .models import (
    Subject, Feedback, TermGoal, StudySession, 
    Roadmap, RoadmapStep, ChecklistItem, UserProfile, ProgressAlert
)
from .ai_service import get_ai_service, RoadmapGenerationError
from .forms import SubjectForm, FeedbackForm, TermGoalForm, StudySessionForm
from django.db.models import Sum, Count, Q
import json
from datetime import date, timedelta
from django.views.decorators.csrf import csrf_exempt


@login_required
def dashboard(request):
    """Dashboard with analytics and visualisations"""
    # Redirects parents to parent dashboard
    try:
        if request.user.profile.role == 'parent':
            return redirect('tracker:parent_dashboard')
    except UserProfile.DoesNotExist:
        pass

    user = request.user
    subjects = Subject.objects.filter(user=user).prefetch_related(
        'feedbacks', 'term_goals', 'study_sessions', 'roadmaps'
    )

    # Total study hours
    total_hours = StudySession.objects.filter(
        subject__user=user
    ).aggregate(
        total=Sum('hours_spent')
    )['total'] or 0

    # Study streak (consecutive days with study sessions)
    study_streak = calculate_study_streak(user)

    # Total completed tasks across all roadmaps
    total_tasks = ChecklistItem.objects.filter(
        roadmap_step__roadmap__subject__user=user
    ).count()

    completed_tasks = ChecklistItem.objects.filter(
        roadmap_step__roadmap__subject__user=user,
        is_completed=True
    ).count()

    completion_percentage = (
        round((completed_tasks / total_tasks) * 100, 1)
        if total_tasks > 0 else 0
    )

    # Average daily hours (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    hours_last_30 = StudySession.objects.filter(
        subject__user=user,
        session_date__gte=thirty_days_ago
    ).aggregate(
        total=Sum('hours_spent')
    )['total'] or 0

    avg_daily_hours = round(hours_last_30 / 30, 1)

    weekly_data = get_weekly_study_data(user)

    subject_data = []
    subject_labels = []

    for subject in subjects:
        hours = subject.study_sessions.aggregate(
            total=Sum('hours_spent')
        )['total'] or 0

        if hours > 0:
            subject_labels.append(subject.get_name_display())
            subject_data.append(float(hours))

  

    progress_data = {
        'labels': ['Completed', 'Remaining'],
        'data': [completed_tasks, total_tasks - completed_tasks]
    }

    recent_activity = get_recent_activity(user, limit=5)

    most_studied = None
    if subject_data:
        max_hours_index = subject_data.index(max(subject_data))
        most_studied = subject_labels[max_hours_index]

    context = {
        'subjects': subjects,

        # Key metrics
        'total_hours': round(total_hours, 1),
        'study_streak': study_streak,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'completion_percentage': completion_percentage,
        'avg_daily_hours': avg_daily_hours,
        'most_studied': most_studied,

        # Chart data (as JSON for Javascript)
        'weekly_chart_data': json.dumps({
            'labels': weekly_data['labels'],
            'data': weekly_data['data'],
        }),
        'subject_chart_data': json.dumps({
            'labels': subject_labels,
            'data': subject_data,
        }),
        'progress_chart_data': json.dumps(progress_data),

        # Recent activity
        'recent_activity': recent_activity,
    }

    return render(request, 'tracker/dashboard.html', context)


def calculate_study_streak(user):
    """Calculate consecutive days with study sessions"""
    today = date.today()
    streak = 0
    current_date = today

    while True:
        # Check if there are study sessions on current_date
        has_session = StudySession.objects.filter(
            subject__user=user,
            session_date=current_date
        ).exists()

        if has_session:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            # Streak broken
            break

        # Safety limit
        if streak > 365:
            break

    return streak

def get_weekly_study_data(user):
    """Get study hours for the last 7 days"""
    today = date.today()
    labels = []
    data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%a'))

        hours = StudySession.objects.filter(
            subject__user=user,
            session_date=day
        ).aggregate(
            total=Sum('hours_spent')
        )['total'] or 0

        data.append(float(hours))

    return {'labels': labels, 'data': data}


def get_recent_activity(user, limit=5):
    """Get recent study sessions, feedback, and completed tasks"""
    activities = []

    # Recent study sessions
    recent_sessions = StudySession.objects.filter(
        subject__user=user
    ).select_related('subject').order_by('-session_date')[:limit]

    for session in recent_sessions:
        activities.append({
            'type': 'study',
            'icon': '📚',
            'text': f"Studied {session.subject.get_name_display()} for {session.hours_spent} hours",
            'date': session.session_date,
            'timestamp': timezone.make_aware(
                timezone.datetime.combine(session.session_date, timezone.datetime.min.time())
            )
        })

    # Recent feedback (MOVED OUTSIDE THE LOOP!)
    recent_feedbacks = Feedback.objects.filter(
        subject__user=user
    ).select_related('subject').order_by('-created_at')[:limit]

    for feedback in recent_feedbacks:
        activities.append({
            'type': 'feedback',
            'icon': '💭',
            'text': f"Added feedback for {feedback.subject.get_name_display()}",
            'date': feedback.feedback_date,
            'timestamp': feedback.created_at
        })
    
    # Recently completed tasks (MOVED OUTSIDE THE LOOP!)
    recent_completions = ChecklistItem.objects.filter(
        roadmap_step__roadmap__subject__user=user,
        is_completed=True,
        completed_at__isnull=False
    ).select_related(
        'roadmap_step__roadmap__subject'
    ).order_by('-completed_at')[:limit]

    for item in recent_completions:
        activities.append({
            'type': 'completion',
            'icon': '✅',
            'text': f"Completed: {item.task_description[:50]}...",
            'date': item.completed_at.date(),
            'timestamp': item.completed_at
        })

    # Sort by timestamp and return most recent (MOVED OUTSIDE!)
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:limit]

@login_required
def add_subject(request):
    """Create a new subject."""
    if request.method == 'POST':
        form = SubjectForm(request.POST, user=request.user)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.user = request.user
            subject.save()
            messages.success(request, f'{subject.get_name_display()} has been added successfully.')
            return redirect('tracker:dashboard')
    else:
        form = SubjectForm(user=request.user)

    context = {
        'form': form,
        'title': 'Add New Subject',
    }

    return render(request, 'tracker/subject_form.html', context)

@login_required
def subject_detail(request, pk):
    """View details of a specific subject"""

    # Check if user is a parent
    try:
        if request.user.profile.role == 'parent':
            # Parents should view subjects through parent dashboard
            messages.info(request, "Please use the Parent Dashboard to view student subjects.")
            return redirect('tracker:parent_dashboard')
    except UserProfile.DoesNotExist:
        pass

    # Get subject fpr cirremt user only(students)
    subject = get_object_or_404(Subject, pk=pk, user=request.user)
    
    # Get all related data
    feedbacks = subject.feedbacks.all().order_by('-feedback_date')
    term_goals = subject.term_goals.all().order_by('-deadline')
    study_sessions = subject.study_sessions.all().order_by('-session_date')[:10]
    
    context = {
        'subject': subject,
        'feedbacks': feedbacks,           # ✅ Added
        'term_goals': term_goals,         # ✅ Added
        'study_sessions': study_sessions, # ✅ Added
        'total_hours': subject.get_total_study_hours(),
        'completion': subject.get_completion_percentage(),
    }
    
    return render(request, 'tracker/subject_detail.html', context)

@login_required
def edit_subject(request, pk):
    """Edit an existing subject."""
    subject = get_object_or_404(Subject, pk=pk, user=request.user)

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'{subject.get_name_display()} has been updated successfully!')
            return redirect('tracker:subject_detail', pk=subject.pk)
    else:
        form = SubjectForm(instance=subject, user=request.user)
    
    context = {
        'form': form,
        'subject': subject,
        'title': f'Edit {subject.get_name_display()}',
    }

    return render(request, 'tracker/subject_form.html', context)

@login_required
def delete_subject(request, pk):
    """Delete a subject."""
    subject = get_object_or_404(Subject, pk=pk, user=request.user)

    if request.method == 'POST':
        subject_name = subject.get_name_display()
        subject.delete()
        messages.success(request, f'{subject_name} has been deleted successfully.')
        return redirect('tracker:dashboard')
    
    context = {
        'subject': subject,
    }

    return render(request, 'tracker/confirm_delete.html', context)

# ==================== FEEDBACK VIEWS ====================

@login_required
def add_feedback(request, subject_pk):
    """Add teacher feedback for a subject"""
    subject = get_object_or_404(Subject, pk=subject_pk, user=request.user)

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.subject = subject
            feedback.save()
            messages.success(request, f'Feedback for {subject.get_name_display()} has been added successfully!')
            return redirect('tracker:subject_detail', pk=subject.pk)
    else:
        form=FeedbackForm()

    context = {
        'form': form,
        'subject': subject,
        'title': f'Add Feedback for {subject.get_name_display()}',
    }

    return render(request, 'tracker/feedback_form.html', context)

@login_required
def edit_feedback(request, pk):
    """Edit existing feedback"""
    feedback = get_object_or_404(Feedback, pk=pk, subject__user=request.user)
    subject = feedback.subject

    if request.method == 'POST':
        form = FeedbackForm(request.POST, instance=feedback)
        if form.is_valid():
            form.save()
            messages.success(request, f'Feedback for {subject.get_name_display()} has been updated successfully!')
            return redirect('tracker:subject_detail', pk=subject.pk)
        
    else:
        form = FeedbackForm(instance=feedback)

    context = {
        'form': form,
        'subject': subject,
        'feedback': feedback,
        'title': f'Edit Feedback for {subject.get_name_display()}',
    }

    return render(request, 'tracker/feedback_form.html', context)

@login_required
def delete_feedback(request, pk):
    """Delete feedback"""
    feedback = get_object_or_404(Feedback, pk=pk, subject__user=request.user)
    subject = feedback.subject

    if request.method == 'POST':
        feedback.delete()
        messages.success(request, f'Feedback for {subject.get_name_display()} has been deleted.')
        return redirect('tracker:subject_detail', pk=subject.pk)
    
    context = {
        'feedback': feedback,
        'subject': subject,
    }

    return render(request, 'tracker/feedback_confirm_delete.html', context)

@login_required
def add_term_goal(request, subject_pk):
    """Add a term goal for a subject"""
    subject = get_object_or_404(Subject, pk=subject_pk, user=request.user)

    if request.method == 'POST':
        form = TermGoalForm(request.POST)
        if form.is_valid():
            term_goal = form.save(commit=False)
            term_goal.subject = subject
            term_goal.save()
            messages.success(
                request,
                f'Term goal set: Level {term_goal.current_level} → {term_goal.target_level} '
                f'by {term_goal.deadline.strftime("%B %d %Y")}'
            )
            return redirect('tracker:subject_detail', pk=subject.pk)
    else:
        form = TermGoalForm()

    return render(request, 'tracker/termgoal_form.html', {
        'form': form,
        'subject': subject,
        'title': f'Set Term Goal for {subject.get_name_display()}'
    })

@login_required
def edit_term_goal(request, pk):
    """Edit an existing term goal"""
    term_goal = get_object_or_404(TermGoal, pk=pk, subject__user=request.user)

    if request.method == 'POST':
        form = TermGoalForm(request.POST, instance=term_goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Term goal has been updated!')
            return redirect('tracker:subject_detail', pk=term_goal.subject.pk)
    else:
        form = TermGoalForm(instance=term_goal)

    return render(request, 'tracker/termgoal_form.html', {
        'form': form,
        'subject': term_goal.subject,
        'title': f'Edit Term Goal for {term_goal.subject.get_name_display()}',
        'term_goal': term_goal
    })

@login_required
def delete_term_goal(request, pk):
    """Delete a term goal"""
    term_goal = get_object_or_404(TermGoal, pk=pk, subject__user=request.user)
    subject = term_goal.subject

    if request.method == 'POST':
        term_goal.delete()
        messages.success(request, 'Term goal has been deleted.')
        return redirect('tracker:subject_detail', pk=subject.pk)
    
    return render(request, 'tracker/termgoal_confirm_delete.html', {
        'term_goal': term_goal,
        'subject': subject
    })

@login_required
def add_study_session(request, subject_pk):
    """Add a study session for a subject"""
    subject = get_object_or_404(Subject, pk=subject_pk, user=request.user)

    if request.method == 'POST':
        form = StudySessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.subject = subject
            session.save()
            messages.success(
                request,
                f'Logged {session.hours_spent} hours for {subject.get_name_display()}!'
            )
            return redirect('tracker:subject_detail', pk=subject.pk)
    else:
        form = StudySessionForm()

    return render(request, 'tracker/studysession_form.html', {
        'form': form,
        'subject': subject,
        'title': f'Log Study Time for {subject.get_name_display()}'
    })

@login_required
def edit_study_session(request, pk):
    """Edit an existing study session"""
    session = get_object_or_404(StudySession, pk=pk, user=request.user)

    if request.method == 'POST':
        form = StudySessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Study session has been updated!')
            return redirect('tracker:subject_detail', pk=session.subject.pk)
    else:
        form = StudySessionForm(instance=session)

    return render(request, 'tracker/studysession_form.html', {
        'form': form,
        'subject': session.subject,
        'title': f'Edit Study Session for {session.subject.get_name_display()}',
        'session': session
    })

@login_required
def delete_study_session(request, pk):
    """Delete a study session"""
    session = get_object_or_404(StudySession, pk=pk, user=request.user)
    subject = session.subject

    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Study session has been deleted.')
        return redirect('tracker:subject_detail', pk=subject.pk)
    
    return render(request, 'tracker/studysession_confirm_delete.html', {
        'session': session,
        'subject': subject
    })

@login_required
def generate_roadmap(request, subject_pk):
    """Genereate AI roadmap for a subject"""
    subject = get_object_or_404(Subject, pk=subject_pk, user=request.user)

    # Get the latest term goal
    term_goal = subject.term_goals.order_by('-created_at').first()

    if not term_goal:
        messages.error(
            request,
            'Please set a term goal before generating a roadmap.'
        )
        return redirect('tracker:subject_detail', pk=subject.pk)
    
    # Get all feedback for this subject
    feedbacks = subject.feedbacks.all()

    if not feedbacks.exists():
        messages.warning(
            request,
            'No teacher feedback found. This roadmap will be less personalised. '
            'Consider adding feedback first for better results.'
        )

    if request.method == 'POST':
        try:
            # Collect data for AI
            strengths = []
            weaknesses = []
            areas_to_improve = []

            for feedback in feedbacks:
                if feedback.strengths:
                    strengths.append(feedback.strengths)
                if feedback.weaknesses:
                    weaknesses.append(feedback.weaknesses)
                if feedback.areas_to_improve:
                    areas_to_improve.append(feedback.areas_to_improve)

            # Get AI service
            ai_service = get_ai_service()

            # Generate roadmap
            roadmap_data = ai_service.generate_roadmap(
                subject_name=subject.get_name_display(),
                current_level=term_goal.current_level,
                target_level=term_goal.target_level,
                strengths=strengths,
                weaknesses=weaknesses,
                areas_to_improve=areas_to_improve,
                deadline=term_goal.deadline,
                study_hours_logged=subject.get_total_study_hours()
            )

            # Save to database (in a transaction for data integrity)
            with transaction.atomic():
                # Deactivate old roadmaps
                Roadmap.objects.filter(
                    subject=subject,
                    is_active=True,
                ).update(is_active=False)

                # Create a new roadmap
                roadmap = Roadmap.objects.create(
                    subject=subject,
                    term_goal=term_goal,
                    title=roadmap_data['title'],
                    overview=roadmap_data['overview'],
                    is_active=True
                )

                # Create steps and checklist items
                for step_data in roadmap_data['steps']:
                    step = RoadmapStep.objects.create(
                        roadmap=roadmap,
                        order_number=step_data['order'],
                        title=step_data['title'],
                        description=step_data['description'],
                        category=step_data['category'],
                        difficulty=step_data['difficulty'],
                        estimated_hours=step_data['estimated_hours']
                    )

                    # Create checklist items
                    for task in step_data['checklist']:
                        ChecklistItem.objects.create(
                            roadmap_step=step,
                            task_description=task
                        )

                # Update total steps count
                roadmap.update_total_steps()

            messages.success(
                request,
                f'🎉 AI roadmap generated successfully! '
                f'{roadmap.total_steps} steps created to help you reach {term_goal.target_level}'
            )
            return redirect('tracker:roadmap_detail', pk=roadmap.pk)
        
        except RoadmapGenerationError as e:
            messages.error(
                request,
                f'Failed to generate roadmap: {str(e)}. Please try again.'
            )
        except Exception as e:
            messages.error(
                request,
                f'An unexpected error occurred: {str(e)}. Please try again.'
            )

    # GET request - show confirmation page
    context = {
        'subject': subject,
        'term_goal': term_goal,
        'feedback_count': feedbacks.count(),
        'has_feedback': feedbacks.exists(),
    }

    return render(request, 'tracker/roadmap_generate.html', context)


@login_required
def roadmap_detail(request, pk):
    """View a specific roadmap with all its steps"""
    roadmap = get_object_or_404(
        Roadmap.objects.select_related('subject', 'term_goal')
        .prefetch_related('steps__checklist_items'),
        pk=pk,
        subject__user=request.user
    )

    # Calculate progress statistics
    total_checklist_items = 0
    completed_checklist_items = 0

    for step in roadmap.steps.all():
        items = step.checklist_items.all()
        total_checklist_items += items.count()
        completed_checklist_items += items.filter(is_completed=True).count()

    completion_percentage = 0
    if total_checklist_items > 0:
        completion_percentage = round(
            (completed_checklist_items / total_checklist_items) * 100,
            1
        )

    context = {
        'roadmap': roadmap,
        'subject': roadmap.subject,
        'total_checklist_items': total_checklist_items,
        'completed_checklist_items': completed_checklist_items,
        'completion_percentage': completion_percentage,
    }

    return render(request, 'tracker/roadmap_detail.html', context)

@login_required
def roadmap_step_detail(request, pk):
    """View a specific roadmap step in detail"""
    step = get_object_or_404(
        RoadmapStep.objects.select_related('roadmap__subject', 'roadmap__term_goal')
        .prefetch_related('checklist_items', 'resources'),
        pk=pk,
        roadmap__subject__user=request.user
    )

    # Calculate step completion
    total_items = step.checklist_items.count()
    completed_items = step.checklist_items.filter(is_completed=True).count()
    step_completion = 0
    if total_items > 0:
        step_completion = round((completed_items / total_items) * 100, 1)

    context = {
        'step': step,
        'roadmap': step.roadmap,
        'subject': step.roadmap.subject,
        'total_items': total_items,
        'completed_items': completed_items,
        'step_completion': step_completion,
    }

    return render(request, 'tracker/roadmap_step_detail.html', context)


@login_required
def delete_roadmap(request, pk):
    """Delete a roadmap"""
    roadmap = get_object_or_404(
        Roadmap,
        pk=pk,
        subject__user=request.user
    )
    subject = roadmap.subject

    if request.method == 'POST':
        roadmap_title = roadmap.title
        roadmap.delete()
        messages.success(
            request,
            f'Roadmap "{roadmap_title}" has been deleted.'
        )
        return redirect('tracker:subject_detail', pk=subject.pk)
    
    context = {
        'roadmap': roadmap,
        'subject': subject,
    }

    return render(request, 'tracker/roadmap_confirm_delete.html', context)
        

@login_required
@require_POST
def toggle_checklist_item(request, pk):
    """Toggle completion status of a checklist item via AJAX"""

    # Get checklist item, ensuring user owns the roadmap
    checklist_item = get_object_or_404(
        ChecklistItem.objects.select_related(
            'roadmap_step__roadmap__subject'
        ),
        pk=pk,
        roadmap_step__roadmap__subject__user=request.user
    )

    # Toggle completion status
    checklist_item.is_completed = not checklist_item.is_completed

    # Update completed_at timestamp
    if checklist_item.is_completed:
        checklist_item.completed_at = timezone.now()
    else:
        checklist_item.completed_at = None

    checklist_item.save()

    # Calculate step progress
    step = checklist_item.roadmap_step
    step_items = step.checklist_items.all()
    step_completed = step_items.filter(is_completed=True).count()
    step_total = step_items.count()
    step_progress = (step_completed / step_total * 100) if step_total > 0 else 0

    # Calculate roadmap progress
    roadmap = step.roadmap
    all_items = ChecklistItem.objects.filter(
        roadmap_step__roadmap=roadmap
    )
    roadmap_completed = all_items.filter(is_completed=True).count()
    roadmap_total = all_items.count()
    roadmap_progress = (roadmap_completed / roadmap_total * 100) if roadmap_total > 0 else 0

    # Return JSON response
    return JsonResponse({
        'success': True,
        'is_completed': checklist_item.is_completed,
        'completed_at': checklist_item.completed_at.isoformat() if checklist_item.completed_at else None,
        'step_progress': round(step_progress, 1),
        'step_completed': step_completed,
        'step_total': step_total,
        'roadmap_progress': round(roadmap_progress, 1),
        'roadmap_completed': roadmap_completed,
        'roadmap_total': roadmap_total, 
    })

@login_required
def parent_dashboard(request):
    """
    Parent dashboard showing aggregated data for all their children.
    """
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, "You don't have a user profile. Please contact support.")
        return redirect('tracker:dashboard')
    
    # Check if user is a parent
    if user_profile.role != 'parent':
        messages.error(request, "Access denied. This page is for parents only.")
        return redirect('tracker:dashboard')
    
    # Get all linked students
    children = user_profile.linked_students.all()
    
    if not children.exists():
        messages.info(request, "No students linked to your account yet. Please contact support to link your child's account.")
        return redirect('tracker:dashboard')
    
    # Get data for each child
    children_data = []
    for child in children:
        # Get subjects
        subjects = Subject.objects.filter(user=child).prefetch_related(
            'term_goals', 'study_sessions', 'roadmaps'
        )
        
        # Calculate metrics
        total_hours = StudySession.objects.filter(
            subject__user=child
        ).aggregate(total=Sum('hours_spent'))['total'] or 0
        
        total_tasks = ChecklistItem.objects.filter(
            roadmap_step__roadmap__subject__user=child
        ).count()
        
        completed_tasks = ChecklistItem.objects.filter(
            roadmap_step__roadmap__subject__user=child,
            is_completed=True
        ).count()
        
        completion_percentage = (
            round((completed_tasks / total_tasks) * 100, 1)
            if total_tasks > 0 else 0
        )
        
        # Study streak
        study_streak = calculate_study_streak(child)
        
        # Get active roadmaps
        active_roadmaps = Roadmap.objects.filter(
            subject__user=child,
            is_active=True
        ).select_related('subject')
        
        # Recent activity
        recent_activity = get_recent_activity(child, limit=5)
        
        # Average daily hours (last 30 days)
        from django.utils import timezone
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        hours_last_30 = StudySession.objects.filter(
            subject__user=child,
            session_date__gte=thirty_days_ago
        ).aggregate(total=Sum('hours_spent'))['total'] or 0
        avg_daily_hours = round(hours_last_30 / 30, 1)
        
        children_data.append({
            'student': child,
            'subjects': subjects,
            'total_hours': round(total_hours, 1),
            'completion_percentage': completion_percentage,
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks,
            'study_streak': study_streak,
            'active_roadmaps': active_roadmaps,
            'recent_activity': recent_activity,
            'avg_daily_hours': avg_daily_hours,
        })
    
    context = {
        'user_profile': user_profile,
        'children_data': children_data,
        'total_children': children.count(),
    }
    
    return render(request, 'tracker/parent_dashboard.html', context)


@login_required
def parent_student_detail(request, student_id):
    """
    Detailed view of a specific student's progress for parents.
    """
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, "Access denied.")
        return redirect('tracker:dashboard')
    
    # Check if user is a parent
    if user_profile.role != 'parent':
        messages.error(request, "Access denied. This page is for parents only.")
        return redirect('tracker:dashboard')
    
    # Verify this student is linked to this parent
    student = get_object_or_404(User, id=student_id)
    if student not in user_profile.linked_students.all():
        messages.error(request, "Access denied. This student is not linked to your account.")
        return redirect('tracker:parent_dashboard')
    
    # Get all student data
    subjects = Subject.objects.filter(user=student).prefetch_related(
        'term_goals', 'study_sessions', 'roadmaps', 'feedbacks'
    )
    
    # Calculate metrics
    total_hours = StudySession.objects.filter(
        subject__user=student
    ).aggregate(total=Sum('hours_spent'))['total'] or 0
    
    study_streak = calculate_study_streak(student)
    
    total_tasks = ChecklistItem.objects.filter(
        roadmap_step__roadmap__subject__user=student
    ).count()
    
    completed_tasks = ChecklistItem.objects.filter(
        roadmap_step__roadmap__subject__user=student,
        is_completed=True
    ).count()
    
    completion_percentage = (
        round((completed_tasks / total_tasks) * 100, 1)
        if total_tasks > 0 else 0
    )
    
    # Get recent activity
    recent_activity = get_recent_activity(student, limit=10)
    
    # Get active roadmaps with progress
    active_roadmaps = Roadmap.objects.filter(
        subject__user=student,
        is_active=True
    ).select_related('subject')
    
    context = {
        'student': student,
        'subjects': subjects,
        'total_hours': round(total_hours, 1),
        'study_streak': study_streak,
        'completion_percentage': completion_percentage,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'recent_activity': recent_activity,
        'active_roadmaps': active_roadmaps,
    }
    
    return render(request, 'tracker/parent_student_detail.html', context)

@login_required
def parent_alert_history(request):
    """View alert histroy for parents."""
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, "Access denied.")
        return redirect('tracker:dashboard')
    
    # Check if user is a parent
    if user_profile.role != 'parent':
        messages.error(request, "Access denied. This page is for parents only.")
        return redirect('tracker:dashboard')
    
    # Get all alerts for this parent
    alerts = ProgressAlert.objects.filter(
        parent=request.user
    ).select_related('student', 'related_subject', 'related_roadmap')

    # Filter by type if specified
    alert_type = request.GET.get('type')
    if alert_type:
        alerts = alerts.filter(alert_type=alert_type)

    # Filter by student if specified
    student_id = request.GET.get('student')
    if student_id:
        alerts = alerts.filter(student_id=student_id)

    # Filter by read status
    show_unread_only = request.GET.get('unread') == 'true'
    if show_unread_only:
        alerts = alerts.filter(is_read=False)

    # Get counts
    total_alerts = ProgressAlert.objects.filter(parent=request.user).count()
    unread_count = ProgressAlert.objects.filter(parent=request.user, is_read=False).count()

    # Get children for filter
    children = user_profile.get_children()

    context = {
        'alerts': alerts[:50], # Limit to 50 most recent
        'total_alerts': total_alerts,
        'unread_count': unread_count,
        'children': children,
        'selected_type': alert_type,
        'selected_student': student_id,
        'show_unread_only': show_unread_only,
    }

    return render(request, 'tracker/parent_alert_history.html', context)


@login_required
@require_POST
def mark_alert_read(request, alert_id):
    """Mark an alert as read (AJAX endpoint)."""
    try:
        user_profile = request.user.profile
        if user_profile.role != 'parent':
            return JsonResponse({'error': 'Access denied'}, status=403)
    except UserProfile.DoesNotExist:
        return JsonResponse({'error', 'Access denied'}, status=403)
    
    alert = get_object_or_404(ProgressAlert, id=alert_id, parent=request.user)
    alert.mark_as_read()

    return JsonResponse({
        'success': True,
        'alert_id': alert_id,
        'read_at': alert.read_at.isoformat() if alert.read_at else None
    })


@login_required
@csrf_exempt
def mark_all_alerts_read(request):
    """Mark all alerts as read (AJAX endpoint)."""
    # Allow GET for testing, but prefer POST in production
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'No profile'}, status=403)
    
    if user_profile.role != 'parent':
        return JsonResponse({'error': 'Not a parent'}, status=403)
    
    unread_alerts = ProgressAlert.objects.filter(
        parent=request.user,
        is_read=False
    )
    
    count = unread_alerts.count()
    
    for alert in unread_alerts:
        alert.mark_as_read()
    
    return JsonResponse({
        'success': True,
        'count': count
    })