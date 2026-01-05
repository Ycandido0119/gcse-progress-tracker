from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Subject, Feedback, TermGoal, StudySession, Roadmap, RoadmapStep, ChecklistItem
from .ai_service import get_ai_service, RoadmapGenerationError
from .forms import SubjectForm, FeedbackForm, TermGoalForm, StudySessionForm


@login_required
def dashboard(request):
    """
    Main dashboard showing all subjects for the logged-in user
    """
    subjects = list(Subject.objects.filter(user=request.user).order_by('name'))
    
    # Calculate overall statistics
    total_subjects = len(subjects)
    
    # Calculate totals
    total_hours = 0
    total_completion = 0
    
    for subject in subjects:
        total_hours += subject.get_total_study_hours()
        total_completion += subject.get_completion_percentage()
    
    # Calculate average completion
    avg_completion = total_completion / total_subjects if total_subjects > 0 else 0
    
    context = {
        'subjects': subjects,
        'total_subjects': total_subjects,
        'total_hours': total_hours,
        'avg_completion': round(avg_completion, 1),
    }
    
    return render(request, 'tracker/dashboard.html', context)

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
        

        