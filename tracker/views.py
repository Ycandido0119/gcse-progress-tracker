from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Subject, Feedback, TermGoal, StudySession
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