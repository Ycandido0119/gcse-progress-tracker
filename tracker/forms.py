from django import forms
from .models import Subject


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
                raise forms.ValidationError(
                    f'You already have {self.fields["name"].choices[int(name)][1]} in your subjects.'
                )
            
            return name