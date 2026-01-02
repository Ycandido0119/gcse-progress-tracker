from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
from tracker.models import Subject, StudySession
from tracker.forms import StudySessionForm
from django.contrib.messages import get_messages


class StudySessionModelTest(TestCase):
    """Test the StudySession model"""

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

    def test_create_study_session(self):
        """Test creating a study session"""
        session = StudySession.objects.create(
            user=self.user,
            subject=self.subject,
            hours_spent=2.5,
            session_date=date.today(),
            notes='Studied algebra'
        )
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.subject, self.subject)
        self.assertEqual(session.hours_spent, 2.5)
        self.assertEqual(session.notes, 'Studied algebra')

    def test_str_representation(self):
        """Test string representation"""
        session = StudySession.objects.create(
            user=self.user,
            subject=self.subject,
            hours_spent=1.5,
            session_date=date(2024, 12, 25)
        )
        expected = f"Mathematics - 1.5 hrs on 2024-12-25"
        self.assertEqual(str(session), expected)
    
    def test_session_ordering(self):
        """Test that sessions are ordered by date (newest first)"""
        StudySession.objects.create(
            user=self.user,
            subject=self.subject,
            hours_spent=1.0,
            session_date=date(2024, 12, 1)
        )
        StudySession.objects.create(
            user=self.user,
            subject=self.subject,
            hours_spent=2.0,
            session_date=date(2024, 12, 15)
        )

        sessions = StudySession.objects.filter(user=self.user)
        self.assertEqual(sessions[0].hours_spent, 2.0)
        self.assertEqual(sessions[1].hours_spent, 1.0)


class StudySessionFormTest(TestCase):
    """Test the StudySessionForm"""

    def test_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'session_date': date.today().isoformat(),
            'hours_spent': 2.5,
            'notes': 'Studied calculus'
        }
        form = StudySessionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_future_date_invalid(self):
        """Test form rejects future dates"""
        form_data = {
            'session_date': (date.today() + timedelta(days=1)).isoformat(),
            'hours_spent': 2.0,
            'notes': 'Test'
        }
        form = StudySessionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cannot be in the future', str(form.errors))

    def test_form_hours_too_low(self):
        """Test form rejects hours below minimum"""
        form_data = {
            'session_date': date.today().isoformat(),
            'hours_spent': 0.05, # Below the minimum
            'notes': 'Test'
        }
        form = StudySessionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('at least 0.1', str(form.errors))

    def test_form_hours_too_high(self):
        """Test form rejects hours above maximum"""
        form_data = {
            'session_date': date.today().isoformat(),
            'hours_spent': 25.0, # Above the maximum
            'notes': 'Test'
        }
        form = StudySessionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cannot exceed 24', str(form.errors))

    def test_form_notes_optional(self):
        """Test that notes field is optional"""
        form_data = {
            'session_date': date.today().isoformat(),
            'hours_spent': 1.5,
            'notes': '' # Notes section are left empty
        }
        form = StudySessionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_missing_required_fields(self):
        """Test form with missing required fields"""
        form = StudySessionForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('session_date', form.errors)
        self.assertIn('hours_spent', form.errors)


class StudySessionViewTest(TestCase):
    """Test study session views"""
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

    def test_add_study_session_requires_login(self):
        """Test that adding study session requires authentication"""
        url = reverse('tracker:add_study_session', args=[self.subject.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_add_study_session_get(self):
        """Test GET request to add study session page"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tracker:add_study_session', args=[self.subject.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Log Study Time')
        self.assertIsInstance(response.context['form'], StudySessionForm)

    def test_add_study_session_post_valid(self):
        """Test POST request with valid data"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tracker:add_study_session', args=[self.subject.pk])
        data = {
            'session_date': date.today().isoformat(),
            'hours_spent': 2.5,
            'notes': 'Worked on algebra problems'
        }
        response = self.client.post(url, data)

        # Should redirect to subject detail
        self.assertEqual(response.status_code, 302)

        # Check study session was created
        self.assertEqual(StudySession.objects.count(), 1)
        session = StudySession.objects.first()
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.subject, self.subject)
        self.assertEqual(session.hours_spent, 2.5)
        self.assertEqual(session.notes, 'Worked on algebra problems')

    def test_add_study_session_success_message(self):
        """Test success message after adding session"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tracker:add_study_session', args=[self.subject.pk])
        data = {
            'session_date': date.today().isoformat(),
            'hours_spent': 1.5,
            'notes': 'Test'
        }
        response = self.client.post(url, data, follow=True)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Logged 1.5 hours', str(messages[0]))

    def test_edit_study_session_get(self):
        """Test GET request to edit study session"""
        self.client.login(username='testuser', password='testpass123')
        session = StudySession.objects.create(
            user=self.user,
            subject=self.subject,
            hours_spent=2.0,
            session_date=date.today()
        )
        url = reverse('tracker:edit_study_session', args=[session.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Study Session')
        self.assertEqual(response.context['session'], session)

    def test_edit_study_session_post_valid(self):
        """Test POST request to edit study session"""
        self.client.login(username='testuser', password='testpass123')
        session = StudySession.objects.create(
            user=self.user,
            subject=self.subject,
            hours_spent=2.0,
            session_date=date.today()
        )
        url = reverse('tracker:edit_study_session', args=[session.pk])
        data = {
            'session_date': date.today().isoformat(),
            'hours_spent': 3.0, # Changed
            'notes': 'Updated notes' # Changed
        }
        response = self.client.post(url, data)

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Check updates
        session.refresh_from_db()
        self.assertEqual(session.hours_spent, 3.0)
        self.assertEqual(session.notes, 'Updated notes')

    def test_delete_study_session_get(self):
        """Test GET request to delete confirmation page"""
        self.client.login(username='testuser', password='testpass123')
        session = StudySession.objects.create(
            user=self.user,
            subject=self.subject,
            hours_spent=1.5,
            session_date=date.today()
        )
        url = reverse('tracker:delete_study_session', args=[session.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete Study Session')
        self.assertContains(response, '1.5')

    def test_delete_study_session_post(self):
        """Test POST request to delete study session"""
        self.client.login(username='testuser', password='testpass123')
        session = StudySession.objects.create(
            user=self.user,
            subject=self.subject,
            hours_spent=2.0,
            session_date=date.today()
        )
        url = reverse('tracker:delete_study_session', args=[session.pk])
        response = self.client.post(url)

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Check deletion
        self.assertEqual(StudySession.objects.count(), 0)

    def test_cannot_access_other_users_session(self):
        """Test user cannot access another user's session"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        other_subject = Subject.objects.create(
            user=other_user,
            name='english',
            description='English'
        )
        session = StudySession.objects.create(
            user=other_user,
            subject=other_subject,
            hours_spent=1.0,
            session_date=date.today()
        )

        # Try to access as different user
        self.client.login(username='testuer', password='testpass123')
        url = reverse('tracker:edit_study_session', args=[session.pk])
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 404])