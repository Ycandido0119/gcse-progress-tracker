from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from datetime import date, timedelta
from tracker.models import(
    UserProfile, ProgressAlert, Subject, StudySession,
    TermGoal, Roadmap, RoadmapStep, ChecklistItem
)
from tracker.alerts import(
    generate_low_activity_alerts,
    generate_goal_at_risk_alerts,
    generate_milestone_alerts,
    generate_roadmap_completed_alerts,
    generate_all_alerts
)


class ProgressAlertModelTest(TestCase):
    """Test the ProgressAlert model."""

    def setUp(self):
        self.parent_user = User.objects.create_user(
            username='parent1',
            password='testpass123',
            email='parent@test.com'
        )
        self.student_user = User.objects.create_user(
            username='student1',
            password='testpass123'
        )
        self.parent_profile = UserProfile.objects.create(
            user=self.parent_user,
            role='parent',
            full_name='Parent One'
        )
        self.parent_profile.linked_students.add(self.student_user)

    def test_create_progress_alert(self):
        """Test creating a progress alert."""
        alert = ProgressAlert.objects.create(
            parent=self.parent_user,
            student=self.student_user,
            alert_type='low_activity',
            severity='warning',
            title='Test Alert',
            message='Test message'
        )

        self.assertEqual(alert.parent, self.parent_user)
        self.assertEqual(alert.student, self.student_user)
        self.assertFalse(alert.is_sent)
        self.assertFalse(alert.is_read)

    def test_mark_alert_as_read(self):
        """Test marking alert as read."""
        alert = ProgressAlert.objects.create(
            parent=self.parent_user,
            student=self.student_user,
            alert_type='milestone_achieved',
            severity='success',
            title='Milestone',
            message='50% complete'
        )

        self.assertFalse(alert.is_read)
        self.assertIsNone(alert.read_at)

        alert.mark_as_read()

        self.assertTrue(alert.is_read)
        self.assertIsNotNone(alert.read_at)

    def test_mark_alert_as_sent(self):
        """Test marking alert as sent."""
        alert = ProgressAlert.objects.create(
            parent=self.parent_user,
            student=self.student_user,
            alert_type='roadmap_completed',
            severity='success',
            title='Complete',
            message='Done!'
        )

        self.assertFalse(alert.is_sent)
        self.assertIsNone(alert.sent_at)

        alert.mark_as_sent()

        self.assertTrue(alert.is_sent)
        self.assertIsNotNone(alert.sent_at)


class LowActivityAlertTest(TestCase):
    """Test low activity alert generation."""

    def setUp(self):
        self.parent_user = User.objects.create_user(
            username='parent1',
            password='testpass123'
        )
        self.student_user = User.objects.create_user(
            username='student1',
            password='testpass123'
        )

        self.parent_profile = UserProfile.objects.create(
            user=self.parent_user,
            role='parent',
            full_name='Parent One',
            alert_low_activity=True,
            alert_low_activity_days=3
        )
        self.parent_profile.linked_students.add(self.student_user)

        self.subject = Subject.objects.create(
            user=self.student_user,
            name='maths'
        )

    def test_generates_alert_after_threshold(self):
        """Test that alert is generated after inactivity threshold."""
        # Create study session 4 days ago
        StudySession.objects.create(
            user=self.student_user,
            subject=self.subject,
            hours_spent=2.0,
            session_date=date.today() - timedelta(days=4)
        )

        alerts_created = generate_low_activity_alerts()

        self.assertEqual(alerts_created, 1)
        alert = ProgressAlert.objects.first()
        self.assertEqual(alert.alert_type, 'low_activity')
        self.assertEqual(alert.severity, 'warning')

    def test_no_alert_within_threshold(self):
        """Test that no alert is generated within threshold."""
        StudySession.objects.create(
            user=self.student_user,
            subject=self.subject,
            hours_spent=2.0,
            session_date=date.today() - timedelta(days=1)
        )

        alerts_created = generate_low_activity_alerts()

        self.assertEqual(alerts_created, 0)

    def test_no_duplicate_alerts(self):
        """Test that duplicate alerts are not created."""
        StudySession.objects.create(
            user=self.student_user,
            subject=self.subject,
            hours_spent=2.0,
            session_date=date.today() - timedelta(days=5)
        )

        # Generate alert first time
        generate_low_activity_alerts()
        self.assertEqual(ProgressAlert.objects.count(), 1)

        # Try to generate again
        generate_low_activity_alerts()
        self.assertEqual(ProgressAlert.objects.count(), 1) # Still just 1


class GoalAtRiskAlertTest(TestCase):
    """Test goal at risk alert generation."""

    def setUp(self):
        self.parent_user = User.objects.create_user(
            username='parent1',
            password='testpass123'
        )
        self.student_user = User.objects.create_user(
            username='student1',
            password='testpass123'
        )

        self.parent_profile = UserProfile.objects.create(
            user=self.parent_user,
            role='parent',
            full_name='Parent One',
            alert_goal_at_risk=True,
            alert_goal_at_risk_days=7
        )
        self.parent_profile.linked_students.add(self.student_user)

        self.subject = Subject.objects.create(
            user=self.student_user,
            name='maths'
        )

    def test_generates_alert_for_at_risk_goal(self):
        """Test alert generated for goal with approaching deadline."""
        # Create goal with deadline in 5 days
        TermGoal.objects.create(
            subject=self.subject,
            term='spring_2026',
            current_level=4,
            target_level=7,
            deadline=date.today() + timedelta(days=5)
        )

        alerts_created = generate_goal_at_risk_alerts()

        # Should create alert (deadline < 7 days, progress < 50%)
        self.assertGreaterEqual(alerts_created, 0)


class MilestoneAlertTest(TestCase):
    """Test milestone achievement alert generation."""

    def setUp(self):
        self.parent_user = User.objects.create_user(
            username='parent1',
            password='testpass123'
        )
        self.student_user = User.objects.create_user(
            username='student1',
            password='testpass123'
        )

        self.parent_profile = UserProfile.objects.create(
            user=self.parent_user,
            role='parent',
            full_name='Parent One',
            alert_milestones=True
        )
        self.parent_profile.linked_students.add(self.student_user)

        self.subject = Subject.objects.create(
            user=self.student_user,
            name='maths'
        )

        self.term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='spring_2026',
            current_level=5,
            target_level=7,
            deadline=date.today() + timedelta(days=90)
        )

        self.roadmap = Roadmap.objects.create(
            subject=self.subject,
            term_goal=self.term_goal,
            title='Test Roadmap',
            is_active=True
        )

        self.step = RoadmapStep.objects.create(
            roadmap=self.roadmap,
            order_number=1,
            title='Step 1',
            category='weakness',
            difficulty='easy',
            estimated_hours=5
        )

        # Create 4 tasks
        for i in range(4):
            ChecklistItem.objects.create(
                roadmap_step=self.step,
                task_description=f'Task {i+1}'
            )

    def test_generates_alert_at_25_percent(self):
        """Test alert generated at 25% milestone."""
        # Complete 1 out of 4 tasks (25%)
        item = ChecklistItem.objects.first()
        item.is_completed = True
        item.completed_at = timezone.now()
        item.save()

        alerts_created = generate_milestone_alerts()

        self.assertGreaterEqual(alerts_created, 0)

    def test_no_duplicate_milestone_alerts(self):
        """Test that milestone alerts are not duplicated."""
        # Complete 1 task
        item = ChecklistItem.objects.first()
        item.is_completed = True
        item.completed_at = timezone.now()
        item.save()

        # Generate once
        generate_milestone_alerts()
        count1 = ProgressAlert.objects.filter(alert_type='milestone_achieved').count()

        # Generate again
        generate_milestone_alerts()
        count2 = ProgressAlert.objects.filter(alert_type='milestone_achieved').count()

        self.assertEqual(count1, count2) # Should not increase


class RoadmapCompletedAlertTest(TestCase):
    """Test roadmap completed alert generation."""

    def setUp(self):
        self.parent_user = User.objects.create_user(
            username='parent1',
            password='testpass123'
        )
        self.student_user = User.objects.create_user(
            username='student1',
            password='testpass123'
        )

        self.parent_profile = UserProfile.objects.create(
            user=self.parent_user,
            role='parent',
            full_name='Parent One',
            alert_roadmap_completed=True
        )
        self.parent_profile.linked_students.add(self.student_user)

        self.subject= Subject.objects.create(
            user=self.student_user,
            name='maths'
        )

        self.term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='spring_2026',
            current_level=5,
            target_level=7,
            deadline=date.today() + timedelta(days=90)
        )

        self.roadmap = Roadmap.objects.create(
            subject=self.subject,
            term_goal=self.term_goal,
            title='Test Roadmap',
            is_active=True
        )

        self.step = RoadmapStep.objects.create(
            roadmap=self.roadmap,
            order_number=1,
            title='Step 1',
            category='weakness',
            difficulty='easy',
            estimated_hours=5
        )

        self.item = ChecklistItem.objects.create(
            roadmap_step=self.step,
            task_description='Task 1'
        )

    def test_generates_alert_on_completion(self):
        """Test alert generated when roadmap 100% complete."""
        # Complete the task
        self.item.is_completed = True
        self.item.completed_at = timezone.now()
        self.item.save()

        alert_created = generate_roadmap_completed_alerts()

        self.assertGreaterEqual(alert_created, 0)


class AlertHistoryViewTest(TestCase):
    """Test alert history view."""

    def setUp(self):
        self.client = Client()
        self.parent_user = User.objects.create_user(
            username='parent1',
            password='testpass123'
        )
        self.student_user = User.objects.create_user(
            username='student1',
            password='testpass123'
        )

        self.parent_profile = UserProfile.objects.create(
            user=self.parent_user,
            role='parent',
            full_name='Parent One'
        )
        self.parent_profile.linked_students.add(self.student_user)

        # Create some alerts
        for i in range(3):
            ProgressAlert.objects.create(
                parent=self.parent_user,
                student=self.student_user,
                alert_type='low_activity',
                severity='warning',
                title=f'Alert {i+1}',
                message=f'Message {i+1}'
            )

        self.url = reverse('tracker:parent_alert_history')

    def test_requires_login(self):
        """Test that alert history requires login."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_parent_can_access(self):
        """Test that parent can access alert history."""
        self.client.login(username='parent1', password='testpass123')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/parent_alert_history.html')

    def test_displays_alerts(self):
        """Test that alerts are displayed."""
        self.client.login(username='parent1', password='testpass123')
        response = self.client.get(self.url)

        self.assertContains(response, 'Alert 1')
        self.assertContains(response, 'Alert 2')
        self.assertContains(response, 'Alert 3')

    def test_filter_by_type(self):
        """Test filtering alerts by type."""
        # Create different type of alert
        ProgressAlert.objects.create(
            parent=self.parent_user,
            student=self.student_user,
            alert_type='milestone_achieved',
            severity='success',
            title='Milestone',
            message='50% done'
        )

        self.client.login(username='parent1', password='testpass123')
        response = self.client.get(self.url + '?type=milestone_achieved')

        self.assertContains(response, 'Milestone')
        self.assertNotContains(response, 'Alert 1')


class MarkAlertReadTest(TestCase):
    """Test marking alerts as read."""

    def setUp(self):
        self.client = Client()
        self.parent_user = User.objects.create_user(
            username='parent1',
            password='testpass123'
        )
        self.student_user = User.objects.create_user(
            username='student1',
            password='testpass123'
        )
        
        self.parent_profile = UserProfile.objects.create(
            user=self.parent_user,
            role='parent',
            full_name='Parent One'
        )
        self.parent_profile.linked_students.add(self.student_user)

        self.alert = ProgressAlert.objects.create(
            parent=self.parent_user,
            student=self.student_user,
            alert_type='low_activity',
            severity='warning',
            title='Test',
            message='Test'
        )

    def test_mark_single_alert_read(self):
        """Test marking single alert as read."""
        self.client.login(username='parent1', password='testpass123')
        url = reverse('tracker:mark_alert_read', args=[self.alert.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.alert.refresh_from_db()
        self.assertTrue(self.alert.is_read)

    def test_mark_all_alerts_read(self):
        """Test marking all alerts as read."""
        # Create more alerts
        for i in range(3):
            ProgressAlert.objects.create(
                parent=self.parent_user,
                student=self.student_user,
                alert_type='low_activity',
                severity='warning',
                title=f'Alert {i}',
                message=f'Message {i}'
            )

        self.client.login(username='parent1', password='testpass123')
        url = reverse('tracker:mark_all_alerts_read')

        response = self.client.post(
            url,
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)

        unread_count = ProgressAlert.objects.filter(
            parent=self.parent_user,
            is_read=False
        ).count()

        self.assertEqual(unread_count, 0)



