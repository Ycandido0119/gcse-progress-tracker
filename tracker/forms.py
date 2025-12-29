from django import forms
from .models import Subject, Feedback


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