from django import forms
from datetime import date
from .models import Subject, Feedback, TermGoal, StudySession


class SubjectForm(forms.ModelForm):
    """Form for creating and editing subjects."""

    class Meta:
        model = Subject
        fields = ['name', 'description']
        widgets = {
            'name': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Optional: Add notes about this subject...',
            }),
        }
        labels = {
            'name': 'Subject *',
            'description': 'Description (Optional)',
        }
        help_texts = {
            'name': 'Select the subject you want to track.',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        """Validate that user doesn't already have this subject."""
        name = self.cleaned_data.get('name')

        # Check if this is an edit (instance exists) or a new subject
        if self.instance.pk:
            # Editing existing subject - allow same name
            existing = Subject.objects.filter(
                user=self.user,
                name=name
            ).exclude(pk=self.instance.pk)
        else:
            # Creating new subject - check for duplicates
            existing = Subject.objects.filter(
                user=self.user,
                name=name
            )

        if existing.exists():
            # Get the display name for the subject
            subject_choices = dict(Subject.SUBJECT_CHOICES)
            subject_display_name = subject_choices.get(name, name)
            raise forms.ValidationError(
                f'You already have {subject_display_name} in your subjects.'
            )
        
        return name
    

class FeedbackForm(forms.ModelForm):
    """Form for creating and editing teacher feedback"""
    
    class Meta:
        model = Feedback
        fields = ['strengths', 'weaknesses', 'areas_to_improve', 'feedback_date']
        widgets = {
            'strengths': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'What did the teacher praise? What is the student doing well?',
            }),
            'weaknesses': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'What areas need improvement? Where is the student struggling?',
            }),
            'areas_to_improve': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Specific action items from teacher. What should the student focus on?',
            }),
            'feedback_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
            })
        }
        labels = {
            'strengths': '💪 Strengths *',
            'weaknesses': '⚠️ Weaknesses *',
            'areas_to_improve': '🎯 Areas to Improve *',
            'feedback_date': 'Feedback Date *',
        }


class TermGoalForm(forms.ModelForm):
    """Form for creating and editing term goals"""
    
    class Meta:
        model = TermGoal
        fields = ['term', 'current_level', 'target_level', 'deadline']
        widgets = {
            'term': forms.Select(attrs={
                'class': 'form-input',
            }),
            'current_level': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Grade 5, Level 3',
                'maxlength': 50,
            }),
            'target_level': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Grade 7, Level 5',
                'maxlength': 50,
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
            }),
        }
        labels = {
            'term': '📅 Term *',
            'current_level': '📊 Current Level *',
            'target_level': '🎯 Target Level *',
            'deadline': '⏰ Deadline *',
        }
        help_texts = {
            'current_level': 'Your current grade/level (e.g., Grade 5, Level 3)',
            'target_level': 'The grade/level you want to achieve (e.g., Grade 7, Level 5)',
            'deadline': 'When do you need to reach this goal?',
        }

    def clean(self):
        """Validate deadline is in future for new goals"""
        cleaned_data = super().clean()
        deadline = cleaned_data.get('deadline')

        # Validate deadline is in future (unless editing existing goal)
        if deadline and not self.instance.pk:
            if deadline < date.today():
                raise forms.ValidationError(
                    'Deadline must be in the future. Choose a date that gives you time to achieve your goal.'
                )

        return cleaned_data
    
class StudySessionForm(forms.ModelForm):
    """Form for creating and editing study sessions"""

    class Meta:
        model = StudySession
        fields = ['session_date', 'hours_spent', 'notes']
        widgets = {
            'session_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
            }),
            'hours_spent': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0.1',
                'max': '24.0',
                'placeholder': 'e.g., 1.5',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Optional: What did you study? Any notes about this session...',
            }),
        }
        labels = {
            'session_date': '📅 Study Date *',
            'hours_spent': '⏱️ Hours Spent *',
            'notes': '📝 Notes (Optional)',
        }
        help_texts = {
            'session_date': 'When did you study',
            'hours_spent': 'How many hours did you study? (0.1 - 24.0)',
            'notes': 'What topics did you cover? Any observations?',
        }
    def clean_session_date(self):
        """Validate that session date is not in the future"""
        session_date = self.cleaned_data.get('session_date')

        if session_date and session_date > date.today():
            raise forms.ValidationError(
                'Study session date cannot be in the future. '
                'Please enter today\'s date or a past date.'
            )
        return session_date
    
    def clean_hours_spent(self):
        """Validate hours spent is within reasonable range"""
        hours = self.cleaned_data.get('hours_spent')

        if hours is not None:
            if hours < 0.1:
                raise forms.ValidationError(
                    'Hours must be at least 0.1 (6 minutes).'
                )
            if hours > 24.0:
                raise forms.ValidationError(
                    'Hours cannot exceed 24 in a single session.'
                )
            
        return hours