"""
Tests for Story 8.1: Dashboard Analytics

Tests cover:
- Study streak calculation
- Weekly study data aggregation
- Subject comparison data
- Progress calculations
- Recent activity queries
- Metric calculations
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
from django.utils import timezone

from tracker.models import (
    Subject, StudySession, Feedback, TermGoal,
    Roadmap, RoadmapStep, ChecklistItem
)


class DashboardAnalyticsTests(TestCase):
    """Test dashboard analytics calculations"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststudent',
            password='testpass123'
        )
        self.client.login(username='teststudent', password='testpass123')
        
        # Create subjects
        self.maths = Subject.objects.create(
            user=self.user,
            name='maths'
        )
        
        self.english = Subject.objects.create(
            user=self.user,
            name='english'
        )
    
    def test_dashboard_loads_successfully(self):
        """Test dashboard page loads with analytics"""
        response = self.client.get(reverse('tracker:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/dashboard.html')
        self.assertIn('total_hours', response.context)
        self.assertIn('study_streak', response.context)
        self.assertIn('completion_percentage', response.context)
    
    def test_total_hours_calculation(self):
        """Test total study hours calculation"""
        # Add study sessions with user field
        StudySession.objects.create(
            user=self.user,
            subject=self.maths,
            session_date=date.today(),
            hours_spent=2.5
        )
        StudySession.objects.create(
            user=self.user,
            subject=self.english,
            session_date=date.today(),
            hours_spent=1.5
        )
        
        response = self.client.get(reverse('tracker:dashboard'))
        
        self.assertEqual(response.context['total_hours'], 4.0)
    
    def test_study_streak_single_day(self):
        """Test study streak with one day"""
        StudySession.objects.create(
            user=self.user,
            subject=self.maths,
            session_date=date.today(),
            hours_spent=2.0
        )
        
        response = self.client.get(reverse('tracker:dashboard'))
        
        self.assertEqual(response.context['study_streak'], 1)
    
    def test_study_streak_consecutive_days(self):
        """Test study streak with consecutive days"""
        today = date.today()
        
        # Create study sessions for 5 consecutive days
        for i in range(5):
            day = today - timedelta(days=i)
            StudySession.objects.create(
                user=self.user,
                subject=self.maths,
                session_date=day,
                hours_spent=1.0
            )
        
        response = self.client.get(reverse('tracker:dashboard'))
        
        self.assertEqual(response.context['study_streak'], 5)
    
    def test_study_streak_broken(self):
        """Test study streak breaks on missing day"""
        today = date.today()
        
        # Study today and yesterday
        StudySession.objects.create(
            user=self.user,
            subject=self.maths,
            session_date=today,
            hours_spent=1.0
        )
        StudySession.objects.create(
            user=self.user,
            subject=self.maths,
            session_date=today - timedelta(days=1),
            hours_spent=1.0
        )
        
        # Skip day before yesterday (gap)
        # Study 3 days ago
        StudySession.objects.create(
            user=self.user,
            subject=self.maths,
            session_date=today - timedelta(days=3),
            hours_spent=1.0
        )
        
        response = self.client.get(reverse('tracker:dashboard'))
        
        # Streak should be 2 (today + yesterday, broken by gap)
        self.assertEqual(response.context['study_streak'], 2)
    
    def test_study_streak_zero_when_no_sessions(self):
        """Test study streak is zero with no sessions"""
        response = self.client.get(reverse('tracker:dashboard'))
        
        self.assertEqual(response.context['study_streak'], 0)
    
    def test_completion_percentage_calculation(self):
        """Test task completion percentage"""
        # Create roadmap with tasks
        term_goal = TermGoal.objects.create(
            subject=self.maths,
            term='spring_2026',
            current_level='Grade 5',
            target_level='Grade 7',
            deadline=date.today() + timedelta(days=90)
        )
        
        roadmap = Roadmap.objects.create(
            subject=self.maths,
            term_goal=term_goal,
            title='Test Roadmap',
            overview='Overview'
        )
        
        step = RoadmapStep.objects.create(
            roadmap=roadmap,
            order_number=1,
            title='Step 1',
            description='Desc',
            category='weakness',
            difficulty='medium',
            estimated_hours=8
        )
        
        # Create 4 tasks, complete 2
        for i in range(4):
            ChecklistItem.objects.create(
                roadmap_step=step,
                task_description=f'Task {i+1}',
                is_completed=(i < 2)  # First 2 completed
            )
        
        response = self.client.get(reverse('tracker:dashboard'))
        
        self.assertEqual(response.context['completed_tasks'], 2)
        self.assertEqual(response.context['total_tasks'], 4)
        self.assertEqual(response.context['completion_percentage'], 50.0)
    
    def test_completion_percentage_zero_tasks(self):
        """Test completion percentage with no tasks"""
        response = self.client.get(reverse('tracker:dashboard'))
        
        self.assertEqual(response.context['completion_percentage'], 0)
    
    def test_avg_daily_hours_calculation(self):
        """Test average daily hours over last 30 days"""
        today = date.today()
        
        # Add 30 hours over 10 days (avg should be 1.0 per day)
        for i in range(10):
            day = today - timedelta(days=i)
            StudySession.objects.create(
                user=self.user,
                subject=self.maths,
                session_date=day,
                hours_spent=3.0
            )
        
        response = self.client.get(reverse('tracker:dashboard'))
        
        # 30 hours / 30 days = 1.0
        self.assertEqual(response.context['avg_daily_hours'], 1.0)
    
    def test_weekly_chart_data_structure(self):
        """Test weekly chart data has correct structure"""
        today = date.today()
        
        # Add study session for today
        StudySession.objects.create(
            user=self.user,
            subject=self.maths,
            session_date=today,
            hours_spent=2.5,
        )
        
        response = self.client.get(reverse('tracker:dashboard'))
        
        # Chart data should be JSON string
        self.assertIn('weekly_chart_data', response.context)
        
        import json
        chart_data = json.loads(response.context['weekly_chart_data'])
        
        # Should have labels and data
        self.assertIn('labels', chart_data)
        self.assertIn('data', chart_data)
        
        # Should have 7 days
        self.assertEqual(len(chart_data['labels']), 7)
        self.assertEqual(len(chart_data['data']), 7)
    
    def test_subject_comparison_data(self):
        """Test subject comparison chart data"""
        # Add different hours for each subject
        StudySession.objects.create(
            user=self.user,
            subject=self.maths,
            session_date=date.today(),
            hours_spent=5.0
        )
        StudySession.objects.create(
            user=self.user,
            subject=self.english,
            session_date=date.today(),
            hours_spent=3.0
        )
        
        response = self.client.get(reverse('tracker:dashboard'))
        
        import json
        chart_data = json.loads(response.context['subject_chart_data'])
        
        self.assertIn('labels', chart_data)
        self.assertIn('data', chart_data)
        
        # Should have 2 subjects
        self.assertEqual(len(chart_data['labels']), 2)
        self.assertEqual(len(chart_data['data']), 2)
        
        # Check values are correct
        self.assertIn(5.0, chart_data['data'])
        self.assertIn(3.0, chart_data['data'])
    
    def test_recent_activity_includes_study_sessions(self):
        """Test recent activity includes study sessions"""
        StudySession.objects.create(
            user=self.user,
            subject=self.maths,
            session_date=date.today(),
            hours_spent=2.0
        )
        
        response = self.client.get(reverse('tracker:dashboard'))
        
        self.assertIn('recent_activity', response.context)
        activities = response.context['recent_activity']
        
        self.assertGreater(len(activities), 0)
        
        # Check for study activity
        study_activities = [a for a in activities if a['type'] == 'study']
        self.assertEqual(len(study_activities), 1)
    
    def test_recent_activity_includes_feedback(self):
        """Test recent activity includes feedback"""
        from django.utils import timezone
        
        feedback = Feedback.objects.create(
            subject=self.maths,
            feedback_date=date.today(),
            strengths='Good',
            weaknesses='Needs work',
            areas_to_improve='Practice'
        )
        
        # Verify feedback was created
        self.assertIsNotNone(feedback.created_at)
        print(f"\nFeedback created_at: {feedback.created_at}")
        
        # Verify we can query it
        feedback_count = Feedback.objects.filter(subject__user=self.user).count()
        print(f"Feedback count for user: {feedback_count}")
        
        response = self.client.get(reverse('tracker:dashboard'))
        
        activities = response.context['recent_activity']
        print(f"Total activities: {len(activities)}")
        
        feedback_activities = [a for a in activities if a['type'] == 'feedback']
        print(f"Feedback activities: {len(feedback_activities)}")
        
        self.assertEqual(len(feedback_activities), 1)
    
    def test_recent_activity_limit(self):
        """Test recent activity respects limit"""
        # Create 10 study sessions
        for i in range(10):
            StudySession.objects.create(
                user=self.user,
                subject=self.maths,
                session_date=date.today() - timedelta(days=i),
                hours_spent=1.0
            )
        
        response = self.client.get(reverse('tracker:dashboard'))
        
        activities = response.context['recent_activity']
        
        # Should only return 5 (limit)
        self.assertLessEqual(len(activities), 5)
    
    def test_most_studied_subject(self):
        """Test most studied subject identification"""
        # Math: 10 hours
        StudySession.objects.create(
            user=self.user,
            subject=self.maths,
            session_date=date.today(),
            hours_spent=10.0
        )
        
        # English: 3 hours
        StudySession.objects.create(
            user=self.user,
            subject=self.english,
            session_date=date.today(),
            hours_spent=3.0
        )
        
        response = self.client.get(reverse('tracker:dashboard'))
        
        self.assertEqual(response.context['most_studied'], 'Mathematics')
    
    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        self.client.logout()
        
        response = self.client.get(reverse('tracker:dashboard'))
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))
    
    def test_dashboard_isolates_user_data(self):
        """Test users only see their own data"""
        # Create another user with data
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        other_subject = Subject.objects.create(
            user=other_user,
            name='science'
        )
        StudySession.objects.create(
            user=other_user,
            subject=other_subject,
            session_date=date.today(),
            hours_spent=10.0
        )
        
        # Login as original user
        response = self.client.get(reverse('tracker:dashboard'))
        
        # Should not see other user's data
        self.assertEqual(response.context['total_hours'], 0)
        
        # Chart should not include other user's subjects
        import json
        chart_data = json.loads(response.context['subject_chart_data'])
        self.assertNotIn('Science', chart_data['labels'])


class StudyStreakEdgeCases(TestCase):
    """Test edge cases for study streak calculation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='teststudent',
            password='testpass123'
        )
        self.subject = Subject.objects.create(
            user=self.user,
            name='maths'
        )
    
    def test_multiple_sessions_same_day_count_once(self):
        """Test multiple sessions on same day only count as 1 streak day"""
        today = date.today()
        
        # Multiple sessions today
        StudySession.objects.create(
            user=self.user,
            subject=self.subject,
            session_date=today,
            hours_spent=1.0
        )
        StudySession.objects.create(
            user=self.user,
            subject=self.subject,
            session_date=today,
            hours_spent=2.0
        )
        
        from tracker.views import calculate_study_streak
        streak = calculate_study_streak(self.user)
        
        self.assertEqual(streak, 1)
    
    def test_future_sessions_dont_count(self):
        """Test future sessions don't affect streak"""
        today = date.today()
        
        # Session today
        StudySession.objects.create(
            user=self.user,
            subject=self.subject,
            session_date=today,
            hours_spent=1.0
        )
        
        # Session in future (shouldn't count)
        StudySession.objects.create(
            user=self.user,
            subject=self.subject,
            session_date=today + timedelta(days=1),
            hours_spent=1.0
        )
        
        from tracker.views import calculate_study_streak
        streak = calculate_study_streak(self.user)
        
        self.assertEqual(streak, 1)