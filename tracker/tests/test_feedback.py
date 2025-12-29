from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from tracker.models import Subject, UserProfile, Feedback
from tracker.forms import FeedbackForm
from datetime import date
from django.contrib.messages import get_messages


class FeedbackModelTest(TestCase):
    """Test cases for the Feedback model"""
    
    def setUp(self):
        """Set up test data"""
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
            name='maths'
        )
    
    def test_create_feedback(self):
        """Test creating feedback successfully"""
        feedback = Feedback.objects.create(
            subject=self.subject,
            strengths='Good at algebra',
            weaknesses='Needs work on geometry',
            areas_to_improve='Practice more problems',
            feedback_date=date.today()
        )
        
        self.assertEqual(feedback.subject, self.subject)
        self.assertEqual(feedback.strengths, 'Good at algebra')
        self.assertIsNotNone(feedback.created_at)  # Fixed: Should be NotNone
    
    def test_feedback_str_method(self):
        """Test string representation of feedback"""
        feedback = Feedback.objects.create(
            subject=self.subject,
            strengths='Test',
            weaknesses='Test',
            areas_to_improve='Test',
            feedback_date=date(2024, 12, 1)
        )
        
        expected_str = f"Mathematics feedback - 2024-12-01"
        self.assertEqual(str(feedback), expected_str)
    
    def test_feedback_ordering(self):
        """Test that feedback is ordered by date (newest first)"""
        Feedback.objects.create(
            subject=self.subject,
            strengths='Old',
            weaknesses='Old',
            areas_to_improve='Old',
            feedback_date=date(2024, 11, 1)
        )
        
        Feedback.objects.create(
            subject=self.subject,
            strengths='New',
            weaknesses='New',
            areas_to_improve='New',
            feedback_date=date(2024, 12, 1)
        )
        
        feedbacks = Feedback.objects.filter(subject=self.subject)
        self.assertEqual(feedbacks[0].strengths, 'New')
        self.assertEqual(feedbacks[1].strengths, 'Old')


class FeedbackFormTest(TestCase):
    """Test cases for the FeedbackForm"""
    
    def test_form_with_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'strengths': 'Good understanding of algebra',
            'weaknesses': 'Struggles with geometry',
            'areas_to_improve': 'Practice more geometry problems',
            'feedback_date': date.today()
        }
        
        form = FeedbackForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_missing_required_field(self):
        """Test form with missing required field"""
        form_data = {
            'strengths': 'Good',
            'weaknesses': '',  # Missing required field
            'areas_to_improve': 'Improve',
            'feedback_date': date.today()
        }
        
        form = FeedbackForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('weaknesses', form.errors)
    
    def test_form_widgets(self):
        """Test that form has correct widgets"""
        form = FeedbackForm()
        
        self.assertEqual(form.fields['strengths'].widget.__class__.__name__, 'Textarea')
        self.assertEqual(form.fields['weaknesses'].widget.__class__.__name__, 'Textarea')
        self.assertEqual(form.fields['areas_to_improve'].widget.__class__.__name__, 'Textarea')


class AddFeedbackViewTest(TestCase):
    """Test cases for add feedback view"""
    
    def setUp(self):
        """Set up test data"""
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
            name='english'
        )
        
        self.add_feedback_url = reverse('tracker:add_feedback', args=[self.subject.pk])
    
    def test_add_feedback_requires_login(self):
        """Test that add feedback requires authentication"""
        response = self.client.get(self.add_feedback_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_add_feedback_get_request(self):
        """Test GET request shows form"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.add_feedback_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Feedback')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['subject'], self.subject)
    
    def test_add_feedback_post_valid_data(self):
        """Test adding feedback with valid data"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'strengths': 'Excellent writing skills',
            'weaknesses': 'Grammar needs improvement',
            'areas_to_improve': 'Practice punctuation',
            'feedback_date': date.today().isoformat()  # Fixed: Use isoformat for date
        }
        
        response = self.client.post(self.add_feedback_url, data)
        
        # Should redirect to subject detail
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tracker:subject_detail', args=[self.subject.pk]))
        
        # Feedback should be created
        self.assertEqual(Feedback.objects.count(), 1)
        feedback = Feedback.objects.first()
        self.assertEqual(feedback.subject, self.subject)
        self.assertEqual(feedback.strengths, 'Excellent writing skills')
    
    def test_add_feedback_post_invalid_data(self):
        """Test adding feedback with invalid data"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'strengths': '',  # Missing required field
            'weaknesses': 'Test',
            'areas_to_improve': 'Test',
            'feedback_date': date.today().isoformat()  # Fixed: Use isoformat
        }
        
        response = self.client.post(self.add_feedback_url, data)
        
        # Should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertIn('strengths', response.context['form'].errors)
        
        # No feedback should be created
        self.assertEqual(Feedback.objects.count(), 0)
    
    def test_add_feedback_success_message(self):
        """Test success message after adding feedback"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'strengths': 'Good',
            'weaknesses': 'Needs work',
            'areas_to_improve': 'Practice',
            'feedback_date': date.today().isoformat()  # Fixed: Use isoformat
        }
        
        response = self.client.post(self.add_feedback_url, data, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('has been added successfully', str(messages[0]))


class EditFeedbackViewTest(TestCase):
    """Test cases for edit feedback view"""
    
    def setUp(self):
        """Set up test data"""
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
            name='science'
        )
        
        self.feedback = Feedback.objects.create(
            subject=self.subject,
            strengths='Good practical skills',
            weaknesses='Theory needs work',
            areas_to_improve='Read textbook',
            feedback_date=date.today()
        )
        
        self.edit_url = reverse('tracker:edit_feedback', args=[self.feedback.pk])
    
    def test_edit_feedback_requires_login(self):
        """Test that edit feedback requires authentication"""
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_edit_feedback_get_request(self):
        """Test GET request shows form with existing data"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.edit_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Feedback')
        self.assertContains(response, 'Good practical skills')
    
    def test_edit_feedback_post_valid_data(self):
        """Test updating feedback with valid data"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'strengths': 'Updated strengths',
            'weaknesses': 'Updated weaknesses',
            'areas_to_improve': 'Updated areas',
            'feedback_date': date.today().isoformat()  # Fixed: Use isoformat
        }
        
        response = self.client.post(self.edit_url, data)
        
        # Should redirect to subject detail
        self.assertEqual(response.status_code, 302)
        
        # Feedback should be updated
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.strengths, 'Updated strengths')
    
    def test_user_cannot_edit_other_users_feedback(self):
        """Test that users cannot edit other users' feedback"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_subject = Subject.objects.create(
            user=other_user,
            name='maths'
        )
        other_feedback = Feedback.objects.create(
            subject=other_subject,
            strengths='Test',
            weaknesses='Test',
            areas_to_improve='Test',
            feedback_date=date.today()
        )
        
        self.client.login(username='testuser', password='testpass123')
        other_edit_url = reverse('tracker:edit_feedback', args=[other_feedback.pk])
        
        response = self.client.get(other_edit_url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)


class DeleteFeedbackViewTest(TestCase):
    """Test cases for delete feedback view"""
    
    def setUp(self):
        """Set up test data"""
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
            name='mandarin'
        )
        
        self.feedback = Feedback.objects.create(
            subject=self.subject,
            strengths='Good pronunciation',
            weaknesses='Character writing',
            areas_to_improve='Practice writing',
            feedback_date=date.today()
        )
        
        self.delete_url = reverse('tracker:delete_feedback', args=[self.feedback.pk])
    
    def test_delete_feedback_requires_login(self):
        """Test that delete feedback requires authentication"""
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_delete_feedback_get_shows_confirmation(self):
        """Test GET request shows confirmation page"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(self.delete_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete Feedback?')
        self.assertContains(response, 'Good pronunciation')
    
    def test_delete_feedback_post_deletes_feedback(self):
        """Test POST request deletes feedback"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.delete_url)
        
        # Should redirect to subject detail
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tracker:subject_detail', args=[self.subject.pk]))
        
        # Feedback should be deleted
        self.assertFalse(Feedback.objects.filter(pk=self.feedback.pk).exists())
    
    def test_delete_feedback_success_message(self):
        """Test success message after deletion"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(self.delete_url, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('has been deleted', str(messages[0]))