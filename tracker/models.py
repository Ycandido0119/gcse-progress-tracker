from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile to students and parents."""
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('parent', 'Parent'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    full_name = models.CharField(max_length=200)
    year_group = models.IntegerField(null=True, blank=True) # Only for students
    linked_student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='parent_profile',
        null=True,
        blank=True,
        help_text="For parents, link to the student they monitor."

    )
    email_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"
    
    class Meta:
        ordering = ['full_name']


class Subject(models.Model):
    """Academic subjects the student is studying."""
    SUBJECT_CHOICES = [
        ('maths', 'Mathematics'),
        ('english', 'English'),
        ('science', 'Science'),
        ('mandarin', 'Mandarin'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_name_display()} - {self.user.username}"
    
    def get_latest_term_goal(self):
        """Get the most recent term goal for this subject."""
        return self.term_goals.order_by('-created_at').first()
    
    def get_total_study_hours(self):
        """Calculate total hours spent studying this subject."""
        result = self.study_sessions.aggregate(total=Sum('hours_spent'))
        return result['total'] or 0
    
    def get_completion_percentage(self):
        """Calculate overall completion percentage for active roadmap."""
        active_roadmap = self.roadmaps.filter(is_active=True).first()
        if not active_roadmap:
            return 0
        
        total_steps = active_roadmap.steps.count()
        if total_steps == 0:
            return 0
        
        completed_steps = active_roadmap.steps.filter(
            checklist_items__is_completed=True
        ).distinct().count()

        return round((completed_steps / total_steps) * 100, 1)
    
    class Meta:
        ordering = ['name']
        unique_together = ('user', 'name')


class TermGoal(models.Model):
    """Academic goals for a specific term."""
    TERM_CHOICES = [
        ('autumn_2025', 'Autumn 2025'),
        ('spring_2026', 'Spring 2026'),
        ('summer_2026', 'Summer 2026'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='term_goals')
    current_level = models.CharField(max_length=50, help_text="e.g., Grade 5, Level 3")
    target_level = models.CharField(max_length=50, help_text="e.g., Grade 7, Level 5")
    term = models.CharField(max_length=20, choices=TERM_CHOICES)
    deadline = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject.get_name_display()} - {self.current_level} → {self.target_level}"
    
    def days_remaining(self):
        """Calculate days until deadline"""
        delta = self.deadline - timezone.now().date()
        return delta.days
    
    def is_overdue(self):
        """check if deadline has passed"""
        return timezone.now().date() > self.deadline
    
    class Meta:
        ordering = ['-created_at']


class Feedback(models.Model):
    """Teacher feedback from parents evenings or assessments."""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='feedbacks')
    strengths = models.TextField(help_text="Areas where the student excels.")
    weaknesses = models.TextField(help_text="Areas where the student is struggling.")
    areas_to_improve = models.TextField(help_text="Specific action items from teacher.")
    feedback_date = models.DateField()
    created_at = models.DateTimeField

    def __str__(self):
        return f"{self.subject.get_name_display()} feedback - {self.feedback_date}"
    
    class Meta:
        ordering = ['-feedback_date']
        verbose_name_plural = "Feedbacks"


class Roadmap(models.Model):
    """AI-generated improvement plan for a subject."""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='roadmaps')
    term_goal = models.ForeignKey(TermGoal, on_delete=models.CASCADE, related_name='roadmaps')
    title = models.CharField(max_length=200)
    overview = models.TextField(help_text="AI-generated summary of the plan.")
    total_steps = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.subject.get_name_display()}"
    
    def update_total_steps(self):
        """Update the count of total steps."""
        self.total_steps = self.steps.count()
        self.save()

    class Meta:
        ordering = ['-generated_at']


class RoadmapStep(models.Model):
    """Individual actionable step in a roadmap."""
    CATEGORY_CHOICES = [
        ('weakness', 'Address Weakness'),
        ('strength', 'Build on Strength'),
        ('level_up', 'Level Up Skill'),
    ]

    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='steps')
    order_number = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    estimated_hours = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)], 
        help_text="Estimated hours to complete this step."
    )
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Step {self.order_number}: {self.title}"
    
    def is_completed(self):
        """Check if all checklist items are completed."""
        total_items = self.checklist_items.count()
        if total_items == 0:
            return False
        completed_items = self.checklist_items.filter(is_completed=True).count()
        return completed_items == total_items
    
    class Meta:
        ordering = ['order_number']


class ChecklistItem(models.Model):
    """Individual checklist task within a roadmap step."""
    roadmap_step = models.ForeignKey(
        RoadmapStep,
        on_delete=models.CASCADE,
        related_name='checklist_items'
    )
    task_description = models.TextField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.task_description[:50]}"
    
    def mark_completed(self):
        """Mark this item as completed."""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
    
    def mark_incomplete(self):
        """Mark this item as incomplete."""
        self.is_completed = False
        self.completed_at = None
        self.save()

    class Meta:
        ordering = ['id']


class Resource(models.Model):
    """Study resources linked to roadmap steps."""
    RESOURCE_TYPE_CHOICES = [
        ('video', 'Video'),
        ('article', 'Article'),
        ('exercise', 'Practice Exercise'),
        ('ai_generated', 'AI-Generated Content'),
    ]

    roadmap_step = models.ForeignKey(
        RoadmapStep,
        on_delete=models.CASCADE,
        related_name='resources'
    )
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="External link (Youtube, Khan Academy, etc.)"
    )
    ai_content = models.TextField(
        null=True,
        blank=True,
        help_text="AI-generated study material."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_resource_type_display()}: {self.title}"
    
    class Meta:
        ordering = ['-created_at']


class StudySession(models.Model):
    """Time tracking for study sessions."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='study_sessions')
    hours_spent = models.FloatField(
        validators=[MinValueValidator(0.1), MaxValueValidator(24.0)],
        help_text="Hours spent studying"
    )
    session_date = models.DateField()
    notes = models.TextField(blank=True, help_text="Optional notes about the session.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject.get_name_display()} - {self.hours_spent} hrs on {self.session_date}"
    
    class Meta:
        ordering = ['-session_date']


class ProgressAlert(models.Model):
    """Automated alerts for parents when student falls behind."""
    ALERT_TYPE_CHOICES = [
        ('behind_schedule', 'Behind Schedule'),
        ('no_activity', 'No Recent Activity'),
        ('low_completion', 'Low Completion Rate'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='alerts')
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='progress_alerts'
    )
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.subject.get_name_display()}"
    
    def mark_as_sent(self):
        """Mark this alert as sent."""
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save()
    
    class Meta:
        ordering = ['-created_at']