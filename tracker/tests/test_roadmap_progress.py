"""
Tests for Story 6.1: Track Roadmap Progress

Tests cover:
- Toggle checklist item completion
- Progress calculation
- Authentication and permissions
- JSON response format
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
import json

from tracker.models import (
    Subject, TermGoal, Roadmap, 
    RoadmapStep, ChecklistItem
)


class ToggleChecklistItemTests(TestCase):
    """Test toggling checklist item completion"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststudent',
            password='testpass123'
        )
        self.client.login(username='teststudent', password='testpass123')
        
        # Create subject and term goal
        self.subject = Subject.objects.create(
            user=self.user,
            name='maths'
        )
        
        self.term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='spring_2026',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
        
        # Create roadmap with steps
        self.roadmap = Roadmap.objects.create(
            subject=self.subject,
            term_goal=self.term_goal,
            title='Test Roadmap',
            overview='Test overview',
            total_steps=2
        )
        
        self.step1 = RoadmapStep.objects.create(
            roadmap=self.roadmap,
            order_number=1,
            title='Step 1',
            description='Description 1',
            category='weakness',
            difficulty='medium',
            estimated_hours=8
        )
        
        self.step2 = RoadmapStep.objects.create(
            roadmap=self.roadmap,
            order_number=2,
            title='Step 2',
            description='Description 2',
            category='strength',
            difficulty='easy',
            estimated_hours=5
        )
        
        # Create checklist items for step 1
        self.item1 = ChecklistItem.objects.create(
            roadmap_step=self.step1,
            task_description='Task 1'
        )
        self.item2 = ChecklistItem.objects.create(
            roadmap_step=self.step1,
            task_description='Task 2'
        )
        self.item3 = ChecklistItem.objects.create(
            roadmap_step=self.step1,
            task_description='Task 3'
        )
        
        # Create checklist items for step 2
        self.item4 = ChecklistItem.objects.create(
            roadmap_step=self.step2,
            task_description='Task 4'
        )
        self.item5 = ChecklistItem.objects.create(
            roadmap_step=self.step2,
            task_description='Task 5'
        )
    
    def test_toggle_item_to_completed(self):
        """Test marking an item as completed"""
        self.assertFalse(self.item1.is_completed)
        self.assertIsNone(self.item1.completed_at)
        
        response = self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item1.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Parse JSON response
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_completed'])  # Fixed: was 'item_completed'
        self.assertIsNotNone(data['completed_at'])
        
        # Verify database was updated
        self.item1.refresh_from_db()
        self.assertTrue(self.item1.is_completed)
        self.assertIsNotNone(self.item1.completed_at)
    
    def test_toggle_item_to_incomplete(self):
        """Test unmarking a completed item"""
        # Mark item as completed first
        self.item1.is_completed = True
        self.item1.save()
        
        response = self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item1.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Parse JSON response
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['is_completed'])
        self.assertIsNone(data['completed_at'])
        
        # Verify database was updated
        self.item1.refresh_from_db()
        self.assertFalse(self.item1.is_completed)
        self.assertIsNone(self.item1.completed_at)
    
    def test_calculates_step_progress(self):
        """Test step progress calculation"""
        # Mark 1 of 3 items complete in step 1
        response = self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item1.pk})
        )
        
        data = response.json()
        self.assertEqual(data['step_completed'], 1)
        self.assertEqual(data['step_total'], 3)
        self.assertAlmostEqual(data['step_progress'], 33.3, places=1)
    
    def test_calculates_roadmap_progress(self):
        """Test roadmap overall progress calculation"""
        # Total: 5 items (3 in step1, 2 in step2)
        # Mark 2 items complete
        self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item1.pk})
        )
        response = self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item4.pk})
        )
        
        data = response.json()
        self.assertEqual(data['roadmap_completed'], 2)
        self.assertEqual(data['roadmap_total'], 5)
        self.assertEqual(data['roadmap_progress'], 40.0)
    
    def test_requires_authentication(self):
        """Test toggle requires login"""
        self.client.logout()
        
        response = self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item1.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))
    
    def test_requires_post_method(self):
        """Test endpoint only accepts POST"""
        response = self.client.get(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item1.pk})
        )
        
        # Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)
    
    def test_cannot_toggle_other_users_items(self):
        """Test users cannot toggle other users' checklist items"""
        # Create another user's roadmap
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_subject = Subject.objects.create(
            user=other_user,
            name='science'
        )
        other_term_goal = TermGoal.objects.create(
            subject=other_subject,
            term='spring_2026',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
        other_roadmap = Roadmap.objects.create(
            subject=other_subject,
            term_goal=other_term_goal,
            title='Other Roadmap',
            overview='Other overview'
        )
        other_step = RoadmapStep.objects.create(
            roadmap=other_roadmap,
            order_number=1,
            title='Other Step',
            description='Desc',
            category='weakness',
            difficulty='medium',
            estimated_hours=8
        )
        other_item = ChecklistItem.objects.create(
            roadmap_step=other_step,
            task_description='Other Task'
        )
        
        # Try to toggle other user's item
        response = self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': other_item.pk})
        )
        
        self.assertEqual(response.status_code, 404)
        
        # Verify item was not changed
        other_item.refresh_from_db()
        self.assertFalse(other_item.is_completed)
    
    def test_progress_updates_correctly(self):
        """Test progress updates as multiple items are checked"""
        # Start with 0% progress
        # Step 1: 3 items
        # Step 2: 2 items
        # Total: 5 items
        
        # Check item 1 (step 1) - 1/5 = 20%
        response1 = self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item1.pk})
        )
        data1 = response1.json()
        self.assertEqual(data1['roadmap_progress'], 20.0)
        self.assertAlmostEqual(data1['step_progress'], 33.3, places=1)  # Fixed: was exact 33.33
        
        # Check item 2 (step 1) - 2/5 = 40%
        response2 = self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item2.pk})
        )
        data2 = response2.json()
        self.assertEqual(data2['roadmap_progress'], 40.0)
        self.assertAlmostEqual(data2['step_progress'], 66.7, places=1)  # Fixed: was exact 66.7
        
        # Check item 4 (step 2) - 3/5 = 60%
        response3 = self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item4.pk})
        )
        data3 = response3.json()
        self.assertEqual(data3['roadmap_progress'], 60.0)
        self.assertEqual(data3['step_progress'], 50.0)  # 1/2 in step 2


class ProgressCalculationTests(TestCase):
    """Test progress calculation edge cases"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststudent',
            password='testpass123'
        )
        self.client.login(username='teststudent', password='testpass123')
        
        self.subject = Subject.objects.create(
            user=self.user,
            name='maths'
        )
        
        self.term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='spring_2026',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
        
        self.roadmap = Roadmap.objects.create(
            subject=self.subject,
            term_goal=self.term_goal,
            title='Test Roadmap',
            overview='Test overview'
        )
        
        self.step = RoadmapStep.objects.create(
            roadmap=self.roadmap,
            order_number=1,
            title='Step 1',
            description='Description',
            category='weakness',
            difficulty='medium',
            estimated_hours=8
        )
        
        self.item1 = ChecklistItem.objects.create(
            roadmap_step=self.step,
            task_description='Task 1'
        )
        self.item2 = ChecklistItem.objects.create(
            roadmap_step=self.step,
            task_description='Task 2'
        )
    
    def test_all_items_completed(self):
        """Test progress when all items are completed"""
        # Complete both items
        self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item1.pk})
        )
        response = self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item2.pk})
        )
        
        data = response.json()
        self.assertEqual(data['roadmap_progress'], 100.0)
        self.assertEqual(data['step_progress'], 100.0)
    
    def test_unchecking_updates_progress(self):
        """Test progress decreases when items are unchecked"""
        # Check both items
        self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item1.pk})
        )
        self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item2.pk})
        )
        
        # Uncheck one item
        response = self.client.post(
            reverse('tracker:toggle_checklist_item', kwargs={'pk': self.item1.pk})
        )
        
        data = response.json()
        self.assertEqual(data['roadmap_progress'], 50.0)
        self.assertEqual(data['step_progress'], 50.0)