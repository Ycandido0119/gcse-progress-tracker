from django import forms
from datetime import date
from .models import Subject, Feedback, TermGoal, StudySession, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


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
    

class UserRegistrationForm(UserCreationForm):
    """Form for new user registration with role selection."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'your.email@example.com',
        }),
        label='Email address *',
        help_text='We\'ll never share your email with anyone else.'
    )

    full_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your full name',
        }),
        label='Full Name *',
        help_text='Your first and last name'
    )

    role = forms.ChoiceField(
        choices=[
            ('student', 'Student - I want to track my own progress'),
            ('parent', 'Parent - I want to monitor my child\'s progress'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio',
        }),
        label='I am a *',
        required=True,
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'role', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Choose a username',
            }),
        }
        labels = {
            'username': 'Username *',
        }
        helps_texts = {
            'username': '150 characters or fewer. Letters, digits and @/./+/_ only.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style password fields to match
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Create a password',
        })
        self.fields['password1'].label = 'Password *'
        self.fields['password1'].help_text = 'Your password must contain at least 8 characters.'

        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Confirm your password',
        })
        self.fields['password2'].label = 'Confirm Password *'
        self.fields['password2'].help_text = 'Enter the same password as before, for verification.'

    def clean_email(self):
        """Validate that email is unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'This email address is already registered. Please user a different email or try logging in.'
            )
        return email
    
    def clean_username(self):
        """Validate username with custom message."""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                'This username is already taken. Please choose a different username.'
            )
        return username
    

class LinkStudentForm(forms.Form):
    """Form for parents to link a student by username."""

    student_username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter student username',
        }),
        label='Student Username',
        help_text='Ask your child for their username, then enter it here to link their account.'
    )

    def __init__(self, *args, **kwargs):
        self.parent_user = kwargs.pop('parent_user', None)
        super().__init__(*args, **kwargs)

    def clean_student_username(self):
        """Validate that the student exists and isn't already linked."""
        username = self.cleaned_data.get('student_username')

        # Check if user exists
        try:
            student = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError(
                f'No user found with username "{username}". Please check the spelling and try again.'
            )
        
        # Check if user is a student
        try:
            profile = student.profile
            if profile.role != 'student':
                raise forms.ValidationError(
                    f'User "{username}" is not a student account. Only student accoutns can be linked.'
                )
        except UserProfile.DoesNotExist:
            raise forms.ValidationError(
                f'User "{username}" does not have a profile. Please contact support.'
            )
        
        # Check if already linked to this parent
        if self.parent_user and student in self.parent_user.profile.linked_students.all():
            raise forms.ValidationError(
                f'"{username}" is already linked to your account.'
            )
        
        return username