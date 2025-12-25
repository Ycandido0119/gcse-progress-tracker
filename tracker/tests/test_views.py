from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from tracker.models import Subject, UserProfile, StudySession
from datetime import date
from django.contrib.messages import get_messages


class DashboardViewTest(TestCase):
    """Test cases for the dashboard view"""
    
    def setUp(self):
        """Set up test data before each test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        UserProfile.objects.create(
            user=self.user,
            role='student',
            full_name='Test Student',
            year_group=9
        )
        
        self.dashboard_url = reverse('tracker:dashboard')
    
    def test_dashboard_requires_login(self):
        """Test that dashboard redirects to login if not authenticated"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_dashboard_shows_subjects(self):
        """Test that dashboard displays user's subjects"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create subjects
        Subject.objects.create(user=self.user, name='maths')
        Subject.objects.create(user=self.user, name='english')
        
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MATHEMATICS')
        self.assertContains(response, 'ENGLISH')
    
    def test_dashboard_shows_correct_stats(self):
        """Test that dashboard calculates statistics correctly"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create a subject with study sessions
        subject = Subject.objects.create(user=self.user, name='science')
        StudySession.objects.create(
            user=self.user,
            subject=subject,
            hours_spent=2.5,
            session_date=date.today()
        )
        
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_subjects'], 1)
        self.assertEqual(response.context['total_hours'], 2.5)
    
    def test_dashboard_empty_state(self):
        """Test dashboard with no subjects shows empty state"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No subjects yet!')


class AddSubjectViewTest(TestCase):
    """Test cases for the add subject view"""
    
    def setUp(self):
        """Set up test data before each test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        UserProfile.objects.create(
            user=self.user,
            role='student',
            full_name='Test Student',
            year_group=9
        )
        
        self.add_subject_url = reverse('tracker:add_subject')
    
    def test_add_subject_requires_login(self):
        """Test that add subject requires authentication"""
        response = self.client.get(self.add_subject_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_add_subject_get_request(self):
        """Test that GET request shows the form"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.add_subject_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add New Subject')
        self.assertIn('form', response.context)
    
    def test_add_subject_post_valid_data(self):
        """Test creating a subject with valid data"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'name': 'maths',
            'description': 'Mathematics subject'
        }
        
        response = self.client.post(self.add_subject_url, data)
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tracker:dashboard'))
        
        # Subject should be created
        self.assertEqual(Subject.objects.count(), 1)
        subject = Subject.objects.first()
        self.assertEqual(subject.name, 'maths')
        self.assertEqual(subject.user, self.user)
    
    def test_add_subject_post_invalid_data(self):
        """Test form shows errors with invalid data"""
        self.client.login(username='testuser', password='testpass123')
        
        # Missing required name field
        data = {
            'name': '',
            'description': 'Test'
        }
        
        response = self.client.post(self.add_subject_url, data)
        
        # Should show form again with errors
        self.assertEqual(response.status_code, 200)
        self.assertIn('name', response.context['form'].errors)
        
        # No subject should be created
        self.assertEqual(Subject.objects.count(), 0)
    
    def test_add_duplicate_subject(self):
        """Test that adding duplicate subject shows error"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create existing subject
        Subject.objects.create(user=self.user, name='english')
        
        # Try to create duplicate
        data = {
            'name': 'english',
            'description': 'Another english'
        }
        
        response = self.client.post(self.add_subject_url, data)
        
        # Should show form with error
        self.assertEqual(response.status_code, 200)
        self.assertIn('name', response.context['form'].errors)
        
        # Should still only have 1 subject
        self.assertEqual(Subject.objects.count(), 1)
    
    def test_add_subject_success_message(self):
        """Test that success message is shown after adding subject"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'name': 'mandarin',
            'description': 'Mandarin subject'
        }
        
        response = self.client.post(self.add_subject_url, data, follow=True)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Mandarin has been added successfully', str(messages[0]))


class SubjectDetailViewTest(TestCase):
    """Test cases for the subject detail view"""
    
    def setUp(self):
        """Set up test data before each test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        UserProfile.objects.create(
            user=self.user,
            role='student',
            full_name='Test Student',
            year_group=9
        )
        
        self.subject = Subject.objects.create(
            user=self.user,
            name='science',
            description='Science subject'
        )
        
        self.detail_url = reverse('tracker:subject_detail', args=[self.subject.pk])
    
    def test_subject_detail_requires_login(self):
        """Test that subject detail requires authentication"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_subject_detail_shows_correct_subject(self):
        """Test that detail page shows the correct subject"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['subject'], self.subject)
        self.assertContains(response, 'Science')
    
    def test_user_cannot_view_other_users_subject(self):
        """Test that users cannot access other users' subjects"""
        # Create another user and their subject
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_subject = Subject.objects.create(
            user=other_user,
            name='maths'
        )
        
        # Login as first user and try to access other user's subject
        self.client.login(username='testuser', password='testpass123')
        other_detail_url = reverse('tracker:subject_detail', args=[other_subject.pk])
        
        response = self.client.get(other_detail_url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)


class EditSubjectViewTest(TestCase):
    """Test cases for the edit subject view"""
    
    def setUp(self):
        """Set up test data before each test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        UserProfile.objects.create(
            user=self.user,
            role='student',
            full_name='Test Student',
            year_group=9
        )
        
        self.subject = Subject.objects.create(
            user=self.user,
            name='maths',
            description='Original description'
        )
        
        self.edit_url = reverse('tracker:edit_subject', args=[self.subject.pk])
    
    def test_edit_subject_requires_login(self):
        """Test that edit subject requires authentication"""
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_edit_subject_get_request(self):
        """Test that GET request shows the form with existing data"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.edit_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Mathematics')
        self.assertContains(response, 'Original description')
    
    def test_edit_subject_post_valid_data(self):
        """Test updating subject with valid data"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'name': 'maths',
            'description': 'Updated description'
        }
        
        response = self.client.post(self.edit_url, data)
        
        # Should redirect to subject detail
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tracker:subject_detail', args=[self.subject.pk]))
        
        # Subject should be updated
        self.subject.refresh_from_db()
        self.assertEqual(self.subject.description, 'Updated description')
    
    def test_edit_subject_success_message(self):
        """Test that success message is shown after editing"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'name': 'maths',
            'description': 'Updated description'
        }
        
        response = self.client.post(self.edit_url, data, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('has been updated successfully', str(messages[0]))


class DeleteSubjectViewTest(TestCase):
    """Test cases for the delete subject view"""
    
    def setUp(self):
        """Set up test data before each test"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        UserProfile.objects.create(
            user=self.user,
            role='student',
            full_name='Test Student',
            year_group=9
        )
        
        self.subject = Subject.objects.create(
            user=self.user,
            name='english',
            description='English subject'
        )
        
        self.delete_url = reverse('tracker:delete_subject', args=[self.subject.pk])
    
    def test_delete_subject_requires_login(self):
        """Test that delete subject requires authentication"""
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_delete_subject_get_shows_confirmation(self):
        """Test that GET request shows confirmation page"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.delete_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete English?')
        self.assertContains(response, 'This action cannot be undone')
    
    def test_delete_subject_post_deletes_subject(self):
        """Test that POST request deletes the subject"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.delete_url)
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tracker:dashboard'))
        
        # Subject should be deleted
        self.assertFalse(Subject.objects.filter(pk=self.subject.pk).exists())
    
    def test_delete_subject_success_message(self):
        """Test that success message is shown after deletion"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.delete_url, follow=True)
        
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('has been deleted', str(messages[0]))