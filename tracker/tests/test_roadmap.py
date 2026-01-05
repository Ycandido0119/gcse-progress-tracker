"""
Tests for Story 5.1: Generate AI Roadmap

Tests cover:
- AI service functionality
- Roadmap generation views
- Roadmap detail views
- Step detail views
- Delete functionality
- Error handling
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
import json

from tracker.models import (
    Subject, Feedback, TermGoal, Roadmap, 
    RoadmapStep, ChecklistItem
)
from tracker.ai_service import AIRoadmapService, RoadmapGenerationError


class AIServiceTests(TestCase):
    """Test the AI service functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='teststudent',
            password='testpass123'
        )
        
        self.subject = Subject.objects.create(
            user=self.user,
            name='maths',
            description='Test subject'
        )
        
        self.term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='spring_2026',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
        
        self.feedback = Feedback.objects.create(
            subject=self.subject,
            feedback_date=date.today(),
            strengths='Good at algebra',
            weaknesses='Struggles with geometry',
            areas_to_improve='Practice more proofs'
        )
    
    @patch('tracker.ai_service.anthropic.Anthropic')
    def test_ai_service_initialization(self, mock_anthropic):
        """Test AI service initializes correctly"""
        service = AIRoadmapService()
        self.assertIsNotNone(service.client)
        self.assertEqual(service.model, 'claude-sonnet-4-20250514')
    
    @patch('tracker.ai_service.anthropic.Anthropic')
    def test_generate_roadmap_success(self, mock_anthropic):
        """Test successful roadmap generation"""
        # Mock API response with 4 steps (minimum required)
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "title": "Mathematics Grade 5 → 7 Plan",
            "overview": "A comprehensive study plan",
            "steps": [
                {
                    "order": 1,
                    "title": "Master Algebra Basics",
                    "description": "Build strong foundation in algebra",
                    "category": "strength",
                    "difficulty": "medium",
                    "estimated_hours": 8,
                    "checklist": [
                        "Complete 20 practice problems",
                        "Review key concepts",
                        "Take practice quiz"
                    ]
                },
                {
                    "order": 2,
                    "title": "Improve Geometry Skills",
                    "description": "Focus on geometric proofs",
                    "category": "weakness",
                    "difficulty": "hard",
                    "estimated_hours": 12,
                    "checklist": [
                        "Study angle relationships",
                        "Practice 15 proofs",
                        "Complete geometry worksheet"
                    ]
                },
                {
                    "order": 3,
                    "title": "Number Theory Practice",
                    "description": "Master fractions and decimals",
                    "category": "weakness",
                    "difficulty": "medium",
                    "estimated_hours": 10,
                    "checklist": [
                        "Practice fraction operations",
                        "Complete decimal exercises",
                        "Take assessment"
                    ]
                },
                {
                    "order": 4,
                    "title": "Statistics Fundamentals",
                    "description": "Learn data analysis basics",
                    "category": "level_up",
                    "difficulty": "easy",
                    "estimated_hours": 6,
                    "checklist": [
                        "Study mean/median/mode",
                        "Create data visualizations",
                        "Complete statistics worksheet"
                    ]
                }
            ]
        }))]
        
        mock_client = mock_anthropic.return_value
        mock_client.messages.create.return_value = mock_response
        
        service = AIRoadmapService()
        roadmap_data = service.generate_roadmap(
            subject_name='Mathematics',
            current_level='Grade 5',
            target_level='Grade 7',
            strengths=['Good at algebra'],
            weaknesses=['Struggles with geometry'],
            areas_to_improve=['Practice more proofs'],
            deadline=date.today() + timedelta(days=90),
            study_hours_logged=10.0
        )
        
        self.assertEqual(roadmap_data['title'], 'Mathematics Grade 5 → 7 Plan')
        self.assertEqual(len(roadmap_data['steps']), 4)
        self.assertEqual(roadmap_data['steps'][0]['category'], 'strength')
    
    @patch('tracker.ai_service.anthropic.Anthropic')
    def test_generate_roadmap_validation(self, mock_anthropic):
        """Test roadmap validation catches invalid data"""
        # Mock invalid response (missing required fields)
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "title": "Test",
            "steps": []  # Missing overview, empty steps
        }))]
        
        mock_client = mock_anthropic.return_value
        mock_client.messages.create.return_value = mock_response
        
        service = AIRoadmapService()
        
        with self.assertRaises(RoadmapGenerationError):
            service.generate_roadmap(
                subject_name='Mathematics',
                current_level='Grade 5',
                target_level='Grade 7',
                strengths=[],
                weaknesses=[],
                areas_to_improve=[],
                deadline=date.today() + timedelta(days=90)
            )


class RoadmapGenerationViewTests(TestCase):
    """Test roadmap generation views"""
    
    def setUp(self):
        """Set up test data and client"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststudent',
            password='testpass123'
        )
        self.client.login(username='teststudent', password='testpass123')
        
        self.subject = Subject.objects.create(
            user=self.user,
            name='maths',
            description='Test subject'
        )
        
        self.term_goal = TermGoal.objects.create(
            subject=self.subject,
            term='spring_2026',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
    
    def test_generate_roadmap_get(self):
        """Test GET request shows confirmation page"""
        response = self.client.get(
            reverse('tracker:generate_roadmap', kwargs={'subject_pk': self.subject.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/roadmap_generate.html')
        self.assertContains(response, 'Generate AI Roadmap')
        self.assertContains(response, self.subject.get_name_display())
    
    def test_generate_roadmap_requires_login(self):
        """Test generation requires authentication"""
        self.client.logout()
        response = self.client.get(
            reverse('tracker:generate_roadmap', kwargs={'subject_pk': self.subject.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))
    
    def test_generate_roadmap_requires_term_goal(self):
        """Test generation requires term goal"""
        # Create subject without term goal
        subject_no_goal = Subject.objects.create(
            user=self.user,
            name='english',
            description='No goal'
        )
        
        response = self.client.get(
            reverse('tracker:generate_roadmap', kwargs={'subject_pk': subject_no_goal.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue('subject' in response.url)
    
    @patch('tracker.views.get_ai_service')
    def test_generate_roadmap_post_success(self, mock_get_service):
        """Test successful roadmap generation via POST"""
        # Mock AI service
        mock_service = MagicMock()
        mock_service.generate_roadmap.return_value = {
            'title': 'Test Roadmap',
            'overview': 'Test overview',
            'steps': [
                {
                    'order': 1,
                    'title': 'Step 1',
                    'description': 'Description',
                    'category': 'weakness',
                    'difficulty': 'medium',
                    'estimated_hours': 8,
                    'checklist': ['Task 1', 'Task 2', 'Task 3']
                }
            ]
        }
        mock_get_service.return_value = mock_service
        
        response = self.client.post(
            reverse('tracker:generate_roadmap', kwargs={'subject_pk': self.subject.pk})
        )
        
        # Should redirect to roadmap detail
        self.assertEqual(response.status_code, 302)
        
        # Verify roadmap was created
        roadmap = Roadmap.objects.filter(subject=self.subject).first()
        self.assertIsNotNone(roadmap)
        self.assertEqual(roadmap.title, 'Test Roadmap')
        self.assertEqual(roadmap.total_steps, 1)
        
        # Verify steps were created
        steps = RoadmapStep.objects.filter(roadmap=roadmap)
        self.assertEqual(steps.count(), 1)
        
        # Verify checklist items were created
        checklist = ChecklistItem.objects.filter(roadmap_step=steps.first())
        self.assertEqual(checklist.count(), 3)
    
    @patch('tracker.views.get_ai_service')
    def test_generate_roadmap_deactivates_old(self, mock_get_service):
        """Test new roadmap deactivates old one"""
        # Create existing roadmap
        old_roadmap = Roadmap.objects.create(
            subject=self.subject,
            term_goal=self.term_goal,
            title='Old Roadmap',
            overview='Old overview',
            is_active=True
        )
        
        # Mock AI service
        mock_service = MagicMock()
        mock_service.generate_roadmap.return_value = {
            'title': 'New Roadmap',
            'overview': 'New overview',
            'steps': [
                {
                    'order': 1,
                    'title': 'Step 1',
                    'description': 'Description',
                    'category': 'strength',
                    'difficulty': 'easy',
                    'estimated_hours': 5,
                    'checklist': ['Task 1', 'Task 2']
                }
            ]
        }
        mock_get_service.return_value = mock_service
        
        self.client.post(
            reverse('tracker:generate_roadmap', kwargs={'subject_pk': self.subject.pk})
        )
        
        # Verify old roadmap is deactivated
        old_roadmap.refresh_from_db()
        self.assertFalse(old_roadmap.is_active)
        
        # Verify new roadmap is active
        new_roadmap = Roadmap.objects.filter(subject=self.subject, is_active=True).first()
        self.assertIsNotNone(new_roadmap)
        self.assertEqual(new_roadmap.title, 'New Roadmap')
    
    def test_cannot_generate_for_other_users_subject(self):
        """Test users cannot generate roadmaps for others' subjects"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_subject = Subject.objects.create(
            user=other_user,
            name='science',
            description='Other user subject'
        )
        
        response = self.client.get(
            reverse('tracker:generate_roadmap', kwargs={'subject_pk': other_subject.pk})
        )
        
        self.assertEqual(response.status_code, 404)


class RoadmapDetailViewTests(TestCase):
    """Test roadmap detail view"""
    
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
            overview='Test overview',
            total_steps=2,
            is_active=True
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
        
        ChecklistItem.objects.create(
            roadmap_step=self.step1,
            task_description='Task 1'
        )
        ChecklistItem.objects.create(
            roadmap_step=self.step1,
            task_description='Task 2',
            is_completed=True
        )
    
    def test_roadmap_detail_get(self):
        """Test viewing roadmap detail"""
        response = self.client.get(
            reverse('tracker:roadmap_detail', kwargs={'pk': self.roadmap.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/roadmap_detail.html')
        self.assertContains(response, 'Test Roadmap')
        self.assertContains(response, 'Step 1')
    
    def test_roadmap_detail_calculates_progress(self):
        """Test progress calculation in roadmap detail"""
        response = self.client.get(
            reverse('tracker:roadmap_detail', kwargs={'pk': self.roadmap.pk})
        )
        
        # Should show 50% progress (1 of 2 items complete)
        self.assertContains(response, '50')
    
    def test_roadmap_detail_requires_login(self):
        """Test roadmap detail requires authentication"""
        self.client.logout()
        response = self.client.get(
            reverse('tracker:roadmap_detail', kwargs={'pk': self.roadmap.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))
    
    def test_cannot_view_other_users_roadmap(self):
        """Test users cannot view others' roadmaps"""
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
        
        response = self.client.get(
            reverse('tracker:roadmap_detail', kwargs={'pk': other_roadmap.pk})
        )
        
        self.assertEqual(response.status_code, 404)


class RoadmapStepDetailViewTests(TestCase):
    """Test roadmap step detail view"""
    
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
            title='Test Step',
            description='Step description',
            category='weakness',
            difficulty='medium',
            estimated_hours=8
        )
        
        ChecklistItem.objects.create(
            roadmap_step=self.step,
            task_description='Task 1'
        )
    
    def test_step_detail_get(self):
        """Test viewing step detail"""
        response = self.client.get(
            reverse('tracker:roadmap_step_detail', kwargs={'pk': self.step.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/roadmap_step_detail.html')
        self.assertContains(response, 'Test Step')
        self.assertContains(response, 'Step description')
        self.assertContains(response, 'Task 1')
    
    def test_step_detail_requires_login(self):
        """Test step detail requires authentication"""
        self.client.logout()
        response = self.client.get(
            reverse('tracker:roadmap_step_detail', kwargs={'pk': self.step.pk})
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))


class RoadmapDeleteViewTests(TestCase):
    """Test roadmap deletion"""
    
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
    
    def test_delete_roadmap_get(self):
        """Test GET shows confirmation page"""
        response = self.client.get(
            reverse('tracker:delete_roadmap', kwargs={'pk': self.roadmap.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/roadmap_confirm_delete.html')
        self.assertContains(response, 'Delete Roadmap')
        self.assertContains(response, 'Test Roadmap')
    
    def test_delete_roadmap_post(self):
        """Test POST deletes roadmap"""
        response = self.client.post(
            reverse('tracker:delete_roadmap', kwargs={'pk': self.roadmap.pk})
        )
        
        # Should redirect to subject detail
        self.assertEqual(response.status_code, 302)
        
        # Verify roadmap was deleted
        self.assertFalse(
            Roadmap.objects.filter(pk=self.roadmap.pk).exists()
        )
    
    def test_delete_roadmap_cascades_to_steps(self):
        """Test deleting roadmap also deletes steps and items"""
        step = RoadmapStep.objects.create(
            roadmap=self.roadmap,
            order_number=1,
            title='Step',
            description='Desc',
            category='weakness',
            difficulty='medium',
            estimated_hours=8
        )
        
        item = ChecklistItem.objects.create(
            roadmap_step=step,
            task_description='Task'
        )
        
        self.client.post(
            reverse('tracker:delete_roadmap', kwargs={'pk': self.roadmap.pk})
        )
        
        # Verify cascade deletion
        self.assertFalse(RoadmapStep.objects.filter(pk=step.pk).exists())
        self.assertFalse(ChecklistItem.objects.filter(pk=item.pk).exists())
    
    def test_cannot_delete_other_users_roadmap(self):
        """Test users cannot delete others' roadmaps"""
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
        
        response = self.client.post(
            reverse('tracker:delete_roadmap', kwargs={'pk': other_roadmap.pk})
        )
        
        self.assertEqual(response.status_code, 404)
        
        # Verify roadmap was not deleted
        self.assertTrue(
            Roadmap.objects.filter(pk=other_roadmap.pk).exists()
        )