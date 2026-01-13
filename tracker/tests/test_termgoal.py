from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
from tracker.models import Subject, TermGoal
from tracker.forms import TermGoalForm


class TermGoalModelTest(TestCase):
    """Test the TermGoal model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.subject = Subject.objects.create(
            user=self.user,
            name='maths',
            description='Mathematics'
        )

    def test_create_term_goal(self):
        """Test creating a term goal"""
        term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='spring_2026',  # Using valid choice
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
        self.assertEqual(term_goal.subject, self.subject)
        self.assertEqual(term_goal.term, 'spring_2026')
        self.assertEqual(term_goal.current_level, 'Grade 5')
        self.assertEqual(term_goal.target_level, 'Grade 7')

    def test_is_overdue_false(self):
        """Test that goal with future deadline is not overdue"""
        term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='summer_2026',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
        self.assertFalse(term_goal.is_overdue())

    def test_is_overdue_true(self):
        """Test that goal with past deadline is overdue"""
        term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='autumn_2025',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() - timedelta(days=1)
        )
        self.assertTrue(term_goal.is_overdue())

    def test_str_representation(self):
        """Test string representation"""
        term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='spring_2026',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
        expected = f"Mathematics - Grade 5 → Grade 7"
        self.assertEqual(str(term_goal), expected)


class TermGoalFormTest(TestCase):
    """Test the TermGoalForm"""

    def test_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'term': 'spring_2026',  # Using valid choice
            'current_level': 'Grade 5',
            'target_level': 'Grade 7',
            'deadline': (date.today() + timedelta(days=90)).isoformat()
        }
        form = TermGoalForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_deadline_in_past(self):
        """Test form rejects past deadline for new goals"""
        form_data = {
            'term': 'autumn_2025',
            'current_level': 'Grade 5',
            'target_level': 'Grade 7',
            'deadline': (date.today() - timedelta(days=1)).isoformat()
        }
        form = TermGoalForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Deadline must be in the future', str(form.errors))

    def test_form_missing_required_fields(self):
        """Test form with missing required fields"""
        form = TermGoalForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 4)  # All 4 fields required


class TermGoalViewTest(TestCase):
    """Test term goal views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.subject = Subject.objects.create(
            user=self.user,
            name='maths',
            description='Mathematics'
        )

    def test_add_term_goal_requires_login(self):
        """Test that adding term goal requires authentication"""
        url = reverse('tracker:add_term_goal', args=[self.subject.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_add_term_goal_get(self):
        """Test GET request to add term goal page"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tracker:add_term_goal', args=[self.subject.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Set Term Goal')
        self.assertIsInstance(response.context['form'], TermGoalForm)

    def test_add_term_goal_post_valid(self):
        """Test POST request with valid data"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tracker:add_term_goal', args=[self.subject.pk])
        data = {
            'term': 'spring_2026',  # Using valid choice
            'current_level': 'Grade 5',
            'target_level': 'Grade 7',
            'deadline': (date.today() + timedelta(days=90)).isoformat()
        }
        response = self.client.post(url, data)
        
        # Should redirect to subject detail
        self.assertEqual(response.status_code, 302)
        
        # Check term goal was created
        self.assertEqual(TermGoal.objects.count(), 1)
        term_goal = TermGoal.objects.first()
        self.assertEqual(term_goal.subject, self.subject)
        self.assertEqual(term_goal.term, 'spring_2026')
        self.assertEqual(term_goal.current_level, 'Grade 5')
        self.assertEqual(term_goal.target_level, 'Grade 7')

    def test_edit_term_goal_get(self):
        """Test GET request to edit term goal"""
        self.client.login(username='testuser', password='testpass123')
        term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='spring_2026',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
        url = reverse('tracker:edit_term_goal', args=[term_goal.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Term Goal')
        self.assertEqual(response.context['term_goal'], term_goal)

    def test_edit_term_goal_post_valid(self):
        """Test POST request to edit term goal"""
        self.client.login(username='testuser', password='testpass123')
        term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='spring_2026',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
        url = reverse('tracker:edit_term_goal', args=[term_goal.pk])
        data = {
            'term': 'summer_2026',  # Changed to different valid choice
            'current_level': 'Grade 5',
            'target_level': 'Grade 8',  # Changed
            'deadline': (date.today() + timedelta(days=120)).isoformat()
        }
        response = self.client.post(url, data)
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Check updates
        term_goal.refresh_from_db()
        self.assertEqual(term_goal.term, 'summer_2026')
        self.assertEqual(term_goal.target_level, 'Grade 8')

    def test_delete_term_goal_get(self):
        """Test GET request to delete confirmation page"""
        self.client.login(username='testuser', password='testpass123')
        term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='spring_2026',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
        url = reverse('tracker:delete_term_goal', args=[term_goal.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete Term Goal')

    def test_delete_term_goal_post(self):
        """Test POST request to delete term goal"""
        self.client.login(username='testuser', password='testpass123')
        term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='spring_2026',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
        url = reverse('tracker:delete_term_goal', args=[term_goal.pk])
        response = self.client.post(url)
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Check deletion
        self.assertEqual(TermGoal.objects.count(), 0)

    def test_cannot_access_other_users_term_goal(self):
        """Test user cannot access another user's term goal"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        other_subject = Subject.objects.create(
            user=other_user,
            name='english',
            description='English'
        )
        term_goal = TermGoal.objects.create(
            subject=other_subject,
            term='spring_2026',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
        
        # Try to access as different user
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tracker:edit_term_goal', args=[term_goal.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)