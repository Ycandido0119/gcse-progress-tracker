from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Subject
from .forms import SubjectForm


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
    """Detailed view of a single subject."""
    subject = get_object_or_404(Subject, pk=pk, user=request.user)

    # Get related data
    latest_goal = subject.get_latest_term_goal()
    latest_feedback = subject.feedbacks.order_by('-feedback_date').first()
    active_roadmap = subject.roadmaps.filter(is_active=True).first()
    recent_sessions = subject.study_sessions.order_by('-session_date')[:5]

    context = {
        'subject': subject,
        'latest_goal': latest_goal,
        'latest_feedback': latest_feedback,
        'active_roadmap': active_roadmap,
        'recent_sessions': recent_sessions,
        'total_hours': subject.get_total_study_hours(),
        'completion_percentage': subject.get_completion_percentage(),
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