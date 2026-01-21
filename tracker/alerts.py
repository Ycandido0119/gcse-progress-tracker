from django.utils import timezone
from django.db.models import Sum, Max
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives
from datetime import timedelta, date
from tracker.models import (
    ProgressAlert, UserProfile, User, StudySession,
    TermGoal, Roadmap, ChecklistItem, Subject, Feedback
)


def generate_low_activity_alerts():
    """Generate alerts for students with low study activity"""
    alerts_created = 0

    # Get all parent profiles
    parent_profiles = UserProfile.objects.filter(
        role='parent',
        alert_low_activity=True
    )

    for parent_profile in parent_profiles:
        for student in parent_profile.get_children():
            # Get last study session date
            last_session = StudySession.objects.filter(
                subject__user=student,
            ).order_by('-session_date').first()

            if last_session:
                days_since_study = (date.today() - last_session.session_date).days
            else:
                days_since_study = 999 # Never studied

            # Check if threshold exceeded
            threshold = parent_profile.alert_low_activity_days
            if days_since_study >= threshold:
                # Check if alert already sent recently (last 24 hours)
                recent_alert = ProgressAlert.objects.filter(
                    parent=parent_profile.user,
                    student=student,
                    alert_type='low_activity',
                    created_at__gte=timezone.now() - timedelta(days=1)
                ).exists()

                if not recent_alert:
                    # Create alert
                    ProgressAlert.objects.create(
                        parent=parent_profile.user,
                        student=student,
                        alert_type='low_activity',
                        severity='warning',
                        title=f"{student.username} hasn't studied recently",
                        message=f"{student.username} hasn't logged any study sessions in the last {days_since_study} days. Consider checking in to see if they are need support."
                    )
                    alerts_created += 1

    return alerts_created

def generate_goal_at_risk_alerts():
    """Generate alerts for goals at risk of not being met."""
    alerts_created = 0

    parents_profiles = UserProfile.objects.filter(
        role='parent',
        alert_goal_at_risk=True
    )

    for parent_profile in parents_profiles:
        for student in parent_profile.get_children():
            # Get active term goals
            goals = TermGoal.objects.filter(
                subject__user=student,
                deadline__gte=date.today()
            )

            for goal in goals:
                days_until_deadline = (goal.deadline - date.today()).days
                threshold = parent_profile.alert_goal_at_risk_days

                # Check if deadline is approaching
                if days_until_deadline <= threshold and days_until_deadline > 0:
                    progress = goal.calculate_progress()
                    # expected_progress = ((goal.target_level - goal.current_level) /
                      #                  (goal.target_level - goal.current_level)) * 100
                    
                    # Alert if progress is less than 50% with deadline approaching
                    if progress < 50:
                        # Check for similar alert
                        recent_alert = ProgressAlert.objects.filter(
                            parent=parent_profile.user,
                            student=student,
                            alert_type='goal_at_risk',
                            related_subject=goal.subject,
                            created_at__gte=timezone.now() - timedelta(days=2)
                        ).exists()

                        if not recent_alert:
                            ProgressAlert.objects.create(
                                parent=parent_profile.user,
                                student=student,
                                alert_type='goal_at_risk',
                                severity='warning',
                                title=f"Goal at risk: {goal.subject.get_name_display()}",
                                message=f"{student.username}'s {goal.get_term_display()} goal for {goal.subject.get_name_display()} (Level {goal.current_level} → {goal.target_level}) is at risk. Only {days_until_deadline} days left and currently at {progress:.0f}% progress.",
                            )
                            alerts_created += 1

        return alerts_created
    
def generate_milestone_alerts():
    """Generate alerts when students reach progress milestones."""
    alerts_created = 0
    
    parent_profiles = UserProfile.objects.filter(
        role='parent',
        alert_milestones=True
    )
    
    milestones = [25, 50, 75, 100]
    
    for parent_profile in parent_profiles:
        for student in parent_profile.get_children():
            # Get active roadmaps
            roadmaps = Roadmap.objects.filter(
                subject__user=student,
                is_active=True
            )
            
            for roadmap in roadmaps:
                progress = roadmap.calculate_overall_progress()
                
                # Check which milestone(s) have been reached
                for milestone in milestones:
                    if progress >= milestone:
                        # IMPROVED: Check if already alerted for this specific milestone
                        existing_alert = ProgressAlert.objects.filter(
                            parent=parent_profile.user,
                            student=student,
                            alert_type='milestone_achieved',
                            related_roadmap=roadmap,
                            title__contains=f"{milestone}%"  # ← Make sure title contains the milestone
                        ).exists()
                        
                        if not existing_alert:
                            # Only create if no existing alert for THIS milestone
                            ProgressAlert.objects.create(
                                parent=parent_profile.user,
                                student=student,
                                alert_type='milestone_achieved',
                                severity='success',
                                title=f"🎉 {milestone}% milestone reached!",  # ← Title includes milestone
                                message=f"Great progress! {student.username} has completed {milestone}% of their {roadmap.subject.get_name_display()} roadmap: '{roadmap.title}'.",
                                related_roadmap=roadmap,
                                related_subject=roadmap.subject
                            )
                            alerts_created += 1
                            # IMPORTANT: Only alert for the HIGHEST milestone reached
                            break  # Exit milestone loop after first creation
    
    return alerts_created

def generate_roadmap_completed_alerts():
    """Generate alerts when students complete roadmaps."""
    alerts_created = 0

    parent_profiles = UserProfile.objects.filter(
        role='parent',
        alert_roadmap_completed=True
    )

    for parent_profile in parent_profiles:
        for student in parent_profile.get_children():
            # Get recently completed roadmaps (100% progress)
            roadmaps = Roadmap.objects.filter(
                subject__user=student
            )

            for roadmap in roadmaps:
                if roadmap.calculate_overall_progress() == 100:
                    # Check if already alerted
                    existing_alert = ProgressAlert.objects.filter(
                        parent=parent_profile.user,
                        student=student,
                        alert_type='roadmap_completed',
                        related_roadmap=roadmap
                    ).exists()

                    if not existing_alert:
                        ProgressAlert.objects.create(
                            parent=parent_profile.user,
                            student=student,
                            alert_type='roadmap_completed',
                            severity='success',
                            title=f"🎉 Roadmap completed",
                            message=f"Congratulations! {student.username} has completed their {roadmap.subject.get_name_display()} roadmap: '{roadmap.title}'. All {roadmap.get_total_items()} tasks are done!",
                            related_roadmap=roadmap,
                            related_subject=roadmap.subject
                        )
                        alerts_created += 1

    return alerts_created

def generate_streak_broken_alerts():
    """Generate alerts when study streaks are broken."""
    alerts_created = 0

    parents_profiles = UserProfile.objects.filter(
        role='parent',
        alert_streak_broken=True,
    )

    for parent_profile in parents_profiles:
        for student in parent_profile.get_children():
            # Check if studied yesterday but not today
            yesterday = date.today() - timedelta(days=1)
            studied_yesterday = StudySession.objects.filter(
                subject__user=student,
                session_date=yesterday
            ).exists()

            studied_today = StudySession.objects.filter(
                subject__user=student,
                session_date=date.today()
            ).exists()

            if studied_yesterday and not studied_today:
                # Check if already alerted today
                recent_alert = ProgressAlert.objects.filter(
                    parent=parent_profile.user,
                    student=student,
                    alert_type='streak_broken',
                    created_at__date=date.today()
                ).exists()

                if not recent_alert:
                    ProgressAlert.objects.create(
                        parent=parent_profile.user,
                        studnet=student,
                        alert_type='streak_broken',
                        severity='warning',
                        title=f"Study streak at risk",
                        message=f"{student.username}'s study streak is at risk! They studied yesterday but haven't logged any study time today yet."
                    )
                    alerts_created += 1

    return alerts_created

def generate_new_feedback_alerts():
    """Generate alerts when new teacher feedback is added."""
    alerts_created = 0

    parent_profiles = UserProfile.objects.filter(
        role='parent',
        alert_new_feedback=True
    )

    # Only check for feedback from last 24 hours
    yesterday = timezone.now() - timedelta(days=1)

    for parent_profile in parent_profiles:
        for student in parent_profile.get_children():
            # Get new feedback
            new_feedbacks = Feedback.objects.filter(
                subject__user=student,
                created_at__gte=yesterday
            )

            for feedback in new_feedbacks:
                # Check if already alerted
                existing_alert = ProgressAlert.objects.filter(
                    parent=parent_profile.user,
                    student=student,
                    alert_type='new_feedback',
                    related_subject=feedback.subject,
                    created_at__gte=yesterday
                ).exists()

                if not existing_alert:
                    ProgressAlert.objects.create(
                        parent=parent_profile.user,
                        student=student,
                        alert_type='new_feedback',
                        severity='info',
                        title=f"New teacher feedback: {feedback.subject.get_name_display()}",
                        message=f"New feedback has been added for {student.username} in {feedback.subject.get_name_display()}. Check the parent dashboard to review strengths, weaknesses, and areas to improve.",
                        related_subject=feedback.subject
                    )
                    alerts_created += 1

    return alerts_created

def send_alert_emails():
    """Send email notifications for unsent alerts based on parent preferences."""
    emails_sent = 0

    # Get all parent profiles
    parent_profiles = UserProfile.objects.filter(
        role='parent',
        email_notifications=True
    )

    for parent_profile in parent_profiles:
        # Get unsent alerts for this parent
        unsent_alerts = ProgressAlert.objects.filter(
            parent=parent_profile.user,
            is_sent=False
        ).order_by('-created_at')

        if not unsent_alerts.exists():
            continue

        # Check alert frequency preference
        frequency = parent_profile.alert_frequency
        last_sent = parent_profile.last_alert_sent

        should_send = False

        if frequency == 'immediate':
            should_send = True,
        elif frequency == 'daily':
            if not last_sent or (timezone.now() - last_sent).days >= 1:
                should_send = True
        elif frequency == 'weekly':
            if not last_sent or (timezone.now() - last_sent).days >= 7:
                should_send = True

        if should_send:
            # Prepate email
            parent_email = parent_profile.user.email

            if not parent_email:
                continue # Skip if no email

            # Generate dashboard URL
            dashboard_url = f"{settings.SITE_URL}/parent/dashboard/"
            preferences_url = f"{settings.SITE_URL}/parent/preferences/"

            # Render email template
            context = {
                'parent_name': parent_profile.full_name,
                'alerts': unsent_alerts[:10], # Limit to 10 most recent
                'alerts_count': unsent_alerts.count(),
                'dashboard_url': dashboard_url,
                'preferences_url': preferences_url,
            }

            html_content = render_to_string('tracker/emails/progress_alert_email.html', context)
            text_content = render_to_string('tracker/emails/progress_alert_email.txt', context)

            # Create subject line
            if unsent_alerts.count() == 1:
                subject = f"Study Alert: {unsent_alerts.first().title}"
            else:
                subject = f"Study Progress: {unsent_alerts.count()} New Alerts"

            # Send email
            try:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[parent_email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()

                # Mark alerts as sent
                for alert in unsent_alerts:
                    alert.mark_as_sent()

                # Update last sent timestamp
                parent_profile.last_alert_sent = timezone.now()
                parent_profile.save()

                emails_sent += 1

            except Exception as e:
                print(f"Error sending email to {parent_email}: {e}")
                continue

    return emails_sent

def generate_all_alerts():
    """Generate all types of alerts. Returns count of alerts created."""
    total = 0

    total += generate_low_activity_alerts()
    total += generate_goal_at_risk_alerts()
    total += generate_milestone_alerts()
    total += generate_roadmap_completed_alerts()
    total += generate_streak_broken_alerts()
    total += generate_new_feedback_alerts()

    return total
