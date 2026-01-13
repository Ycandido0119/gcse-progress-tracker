from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from tracker.models import (
    UserProfile, Subject, StudySession, TermGoal,
    Feedback, Roadmap, RoadmapStep, ChecklistItem
)


class UserProfileParentTest(TestCase):
    """Test the UserProfile model with parent role."""

    def setUp(self):
        self.parent_user = User.objects.create_user(
            username='parent1',
            password='testpass123'
        )
        self.student_user = User.objects.create_user(
            username='student1',
            password='testpass123'
        )

    def test_create_parent_profile(self):
        """Test creating a parent user profile."""
        profile = UserProfile.objects.create(
            user=self.parent_user,
            role='parent',
            full_name='Parent One'
        )
        self.assertEqual(profile.role, 'parent')
        self.assertEqual(profile.email_notifications, True) # Default

    def test_link_child_to_parent(self):
        """Test linking a child to a parent profile."""
        profile = UserProfile.objects.create(
            user=self.parent_user,
            role='parent',
            full_name='Parent One'
        )
        profile.linked_students.add(self.student_user)

        self.assertIn(self.student_user, profile.linked_students.all())
        self.assertEqual(profile.linked_students.count(), 1)

    def test_get_children_method(self):
        """Test get_children method returns linked students."""
        profile = UserProfile.objects.create(
            user=self.parent_user,
            role='parent',
            full_name='Parent One'
        )
        profile.linked_students.add(self.student_user)

        children = profile.get_children()
        self.assertEqual(children.count(), 1)
        self.assertIn(self.student_user, children)

    def test_student_profile_get_children_returns_empty(self):
        """Test that student profiles return no children."""
        profile = UserProfile.objects.create(
            user=self.student_user,
            role='student',
            full_name='Student One',
            year_group=10
        )

        children = profile.get_children()
        self.assertEqual(children.count(), 0)


class ParentDashboardAccessTest(TestCase):
    """Test access control for parent dashboard."""

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
        self.other_user = User.objects.create_user(
            username='other_user',
            password='testpass123'
        )

        # Create parent profile
        self.parent_profile = UserProfile.objects.create(
            user=self.parent_user,
            role='parent',
            full_name='Parent One'
        )
        self.parent_profile.linked_students.add(self.student_user)

        # Create student profile
        UserProfile.objects.create(
            user=self.student_user,
            role='student',
            full_name='Student One',
            year_group=10
        )

        self.url = reverse('tracker:parent_dashboard')

    def test_parent_dashboard_requires_login(self):
        """Test that parent dashboard requires authentication."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302) # Redirect to login
        self.assertIn('/accounts/login/', response.url)

    def test_parent_with_profile_can_access(self):
        """Test that parent with profile can access dashboard"""
        self.client.login(username='parent1', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/parent_dashboard.html')

    def test_student_user_cannot_access_parent_dashboard(self):
        """Test that student users cannot access parent dashboard."""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302) # Redirect

    def test_parent_with_no_children_sees_message(self):
        """Test parent with no linked children sees appropriate message."""
        # Create parent with no children
        lonely_parent = User.objects.create_user(
            username='lonely_parent',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=lonely_parent,
            role='parent',
            full_name='Lonely Parent'
        )

        self.client.login(username='lonely_parent', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302) # Redirected


class ParentDashboardDataTest(TestCase):
    """Test data display on parent dashboard."""

    def setUp(self):
        self.client = Client()

        # Create users
        self.parent_user = User.objects.create_user(
            username='parent1',
            password='testpass123'
        )
        self.student_user = User.objects.create_user(
            username='student1',
            password='testpass123'
        )

        # Create profiles
        self.parent_profile = UserProfile.objects.create(
            user=self.parent_user,
            role='parent',
            full_name='Parent One'
        )
        self.parent_profile.linked_students.add(self.student_user)

        UserProfile.objects.create(
            user=self.student_user,
            role='student',
            full_name='Student One',
            year_group=10
        )

        # Create subject
        self.subject = Subject.objects.create(
            user=self.student_user,
            name='maths'
        )

        # Create study sessions
        for i in range(3):
            StudySession.objects.create(
                user=self.student_user,
                subject=self.subject,
                hours_spent=2.0,
                session_date=date.today() - timedelta(days=i)
            )

        self.url = reverse('tracker:parent_dashboard')

    def test_dashboard_shows_student_name(self):
        """Test that dashboard displays student name."""
        self.client.login(username='parent1', password='testpass123')
        response = self.client.get(self.url)

        self.assertContains(response, 'Student1')


class ParentStudentDetailTest(TestCase):
    """Test parent student detail view."""

    def setUp(self):
        self.client = Client()

        # Create users
        self.parent_user = User.objects.create_user(
            username='parent1',
            password='testpass123'
        )
        self.student_user = User.objects.create_user(
            username='student1',
            password='testpass123'
        )
        self.other_student = User.objects.create_user(
            username='other_student',
            password='testpass123'
        )

        # Create profiles
        self.parent_profile = UserProfile.objects.create(
            user=self.parent_user,
            role='parent',
            full_name='Parent One'
        )
        self.parent_profile.linked_students.add(self.student_user)

        UserProfile.objects.create(
            user=self.student_user,
            role='student',
            full_name='Student One',
            year_group=10
        )

        UserProfile.objects.create(
            user=self.other_student,
            role='student',
            full_name='Other Student',
            year_group=11
        )

        # Create subject and data
        self.subject = Subject.objects.create(
            user=self.student_user,
            name='maths',
            description='Test description'
        )

        StudySession.objects.create(
            user=self.student_user,
            subject=self.subject,
            hours_spent=3.5,
            session_date=date.today()
        )

        self.url = reverse('tracker:parent_student_detail', args=[self.student_user.id])

    def test_detail_requires_login(self):
        """Test that detail view requires authentication."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302) # Redirect to login

    def test_parent_can_view_own_child_detail(self):
        """Test that parent can view their own child's detail."""
        self.client.login(username='parent1', password='testpass123')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/parent_student_detail.html')

    def test_parent_cannot_view_other_student_detail(self):
        """Test that parent cannot view unlinked student's detail."""
        other_url = reverse('tracker:parent_student_detail', args=[self.other_student.id])

        self.client.login(username='parent1', password='testpass123')
        response = self.client.get(other_url)

        self.assertEqual(response.status_code, 302) # Redirected

    def test_student_cannot_access_detail_view(self):
        """Test that students cannot access parent detail view."""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302) # Redirected