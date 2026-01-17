from django.contrib import admin
from .models import (
    UserProfile, Subject, TermGoal, Feedback, 
    Roadmap, RoadmapStep, ChecklistItem, 
    Resource, StudySession, ProgressAlert
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'role', 'user', 'year_group', 'created_at']
    list_filter = ['role', 'year_group', 'email_notifications']
    search_fields = ['full_name', 'user__username']
    raw_id_fields = ['user']  # Only for ForeignKey/OneToOne fields
    filter_horizontal = ['linked_students']  # For ManyToManyField
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'full_name')
        }),
        ('Student Information', {
            'fields': ('year_group',),
            'classes': ('collapse',),
        }),
        ('Parent Information', {
            'fields': ('linked_students', 'phone_number'),
            'classes': ('collapse',),
        }),
        ('Settings', {
            'fields': ('email_notifications',),
        }),
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['get_name_display', 'user', 'created_at', 'updated_at']
    list_filter = ['name', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TermGoal)
class TermGoalAdmin(admin.ModelAdmin):
    list_display = ['subject', 'current_level', 'target_level', 'term', 'deadline', 'days_remaining']
    list_filter = ['term', 'deadline']
    search_fields = ['subject__name']
    date_hierarchy = 'deadline'

    def days_remaining(self, obj):
        days = obj.days_remaining()
        if days < 0:
            return f"Overdue by {abs(days)} days"
        return f"{days} days"
    days_remaining.short_description = 'Time Remaining'


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['subject', 'feedback_date', 'created_at']
    list_filter = ['feedback_date', 'subject__name']
    search_fields = ['subject__user__username', 'strengths', 'weaknesses']
    date_hierarchy = 'feedback_date'
    readonly_fields = ['created_at']


class RoadmapStepInline(admin.TabularInline):
    model = RoadmapStep
    extra = 1
    fields = ['order_number', 'title', 'category', 'difficulty', 'estimated_hours']


@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'total_steps', 'is_active', 'generated_at']
    list_filter = ['is_active', 'generated_at', 'subject__name']
    search_fields = ['title', 'overview']
    readonly_fields = ['generated_at', 'total_steps']
    inlines = [RoadmapStepInline]


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 1
    fields = ['task_description', 'is_completed', 'completed_at']
    readonly_fields = ['completed_at']


class ResourceInline(admin.TabularInline):
    model = Resource
    extra = 1
    fields = ['title', 'resource_type', 'url']


@admin.register(RoadmapStep)
class RoadmapStepAdmin(admin.ModelAdmin):
    list_display = []
    list_filter = []
    search_fields = []
    readonly_fields = []
    inlines = [ChecklistItemInline, ResourceInline]

    def is_completed(self, obj):
        return obj.is_completed()
    is_completed.boolean = True
    is_completed.short_description = 'Completed'


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ['task_description_short', 'roadmap_step', 'is_completed', 'completed_at']
    list_filter = ['is_completed', 'completed_at']
    search_fields = ['task_description']
    readonly_fields = ['completed_at']

    def task_description_short(self, obj):
        return obj.task_description[:50] + '...' if len(obj.task_description) > 50 else obj.task_description
    task_description_short.short_description = 'Task'


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'resource_type', 'roadmap_step', 'created_at']
    list_filter = ['resource_type', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject', 'hours_spent', 'session_date', 'created_at']
    list_filter = ['subject__name', 'session_date']
    search_fields = ['user__username', 'notes']
    date_hierarchy = 'session_date'
    readonly_fields = ['created_at']


@admin.register(ProgressAlert)
class ProgressAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'student', 'parent', 'alert_type', 'severity', 'is_read', 'created_at']
    list_filter = ['alert_type', 'severity', 'is_sent', 'is_read', 'created_at']
    search_fields = ['student__username', 'parent__username', 'title', 'message']
    readonly_fields = ['created_at', 'sent_at', 'read_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Alert Information', {
            'fields': ('alert_type', 'severity', 'title', 'message')
        }),
        ('Users', {
            'fields': ('parent', 'student')
        }),
        ('Related Objects', {
            'fields': ('related_subject', 'related_roadmap'),
            'classes': ('collapse'),
        }),
        ('Status', {
            'fields': ('is_sent', 'sent_at', 'is_read', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    actions = ['mark_as_sent', 'mark_as_read']

    def mark_as_sent(self, request, queryset):
        """Mark selected alerts as sent."""
        for alert in queryset:
            alert.mark_as_sent()
        self.message_user(request, f"{queryset.count()} alert(s) marked as sent.")
    mark_as_sent.short_description = "Mark selected alerts as sent"

    def mark_as_read(self, request, queryset):
        """Mark selected alerts as read."""
        for alert in queryset:
            alert.mark_as_read()
        self.message_user(request, f"{queryset.count()} alert(s) marked as read.")
    mark_as_read.short_description = "Mark selected alerts as read"