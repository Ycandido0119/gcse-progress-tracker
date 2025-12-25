from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError
from tracker.models import Subject, UserProfile, StudySession
from datetime import date



class SubjectModelTest(TestCase):
    """Test cases for the Subject model."""

    def setUp(self):
        """Set up test data before each test"""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Create user profile
        self.profile = UserProfile.objects.create(
            user=self.user,
            role='student',
            full_name='Test Student',
            year_group=9,
        )

    def test_create_subject(self):
        """Testt creating a subject successfully."""
        subject = Subject.objects.create(
            user=self.user,
            name='maths',
            description='Test maths subject'
        )

        self.assertEqual(subject.name, 'maths')
        self.assertEqual(subject.user, self.user)
        self.assertEqual(subject.description, 'Test maths subject')
        self.assertIsNotNone(subject.created_at)
        self.assertIsNotNone(subject.updated_at)

    def test_subject_str_method(self):
        """Test the string representation of a subject."""
        subject = Subject.objects.create(
            user=self.user,
            name='English',
        )

        expected_str = f"English - {self.user.username}"
        self.assertEqual(str(subject), expected_str)

    def test_subject_get_name_display(self):
        """Test that get_name_display returns the human-readable name."""
        subject = Subject.objects.create(
            user=self.user,
            name='maths',
        )

        self.assertEqual(subject.get_name_display(), 'Mathematics')

    def test_cannot_create_duplicate_subjects(self):
        """Test that a user cannot create duplicate subjects."""
        Subject.objects.create(
            user=self.user,
            name='science',
        )

        # Trying to create the same subject again should raise an IntegrityError
        with self.assertRaises(IntegrityError):
            Subject.objects.create(
                user=self.user,
                name='science',
            )

    def test_different_users_can_have_same_subject(self):
        """Test that different users can have the same subject"""
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )

        subject1 = Subject.objects.create(
            user=self.user,
            name='maths',
        )

        subject2 = Subject.objects.create(
            user=user2,
            name='maths',
        )

        self.assertNotEqual(subject1.id, subject2.id)
        self.assertEqual(subject1.name, subject2.name)

    def test_get_total_study_hours_with_no_sessions(self):
        """Test that get_total_study_hours return 0 for new subject"""
        subject = Subject.objects.create(
            user=self.user,
            name='mandarin',
        )

        self.assertEqual(subject.get_total_study_hours(), 0)

    def test_get_total_study_hours_with_sessions(self):
        """Test calculating total study hours"""
        subject = Subject.objects.create(
            user=self.user,
            name='maths',
        )

        # Create some study sessions
        StudySession.objects.create(
            user=self.user,
            subject=subject,
            hours_spent=2.5,
            session_date=date.today()
        )

        StudySession.objects.create(
            user=self.user,
            subject=subject,
            hours_spent=1.5,
            session_date=date.today()
        )

        self.assertEqual(subject.get_total_study_hours(), 4.0)

    def test_get_completion_percentage_no_roadmap(self):
        """Test that completion percentage is with no active roadmap"""
        subject = Subject.objects.create(
            user=self.user,
            name='english',
        )

        self.assertEqual(subject.get_completion_percentage(), 0)
    
    def test_subject_cascade_delete(self):
        """Test that deleting a subject cascades to related objects"""
        subject = Subject.objects.create(
            user=self.user,
            name='science',
        )

        # Create a study session
        session = StudySession.objects.create(
            user=self.user,
            subject=subject,
            hours_spent=1.0,
            session_date=date.today()
        )

        subject_id = subject.id
        session_id = session.id

        # Delete the subject
        subject.delete()

        # Check that subject and session are both deleted
        self.assertFalse(Subject.objects.filter(id=subject_id).exists())
        self.assertFalse(StudySession.objects.filter(id=session_id).exists())

    def test_subject_ordering(self):
        """Test that subjects are ordered by name"""
        Subject.objects.create(user=self.user, name='science')
        Subject.objects.create(user=self.user, name='english')
        Subject.objects.create(user=self.user, name='maths')

        subjects = Subject.objects.filter(user=self.user)
        name = [s.name for s in subjects]

        # Should be ordered alphabetically by name
        self.assertEqual(name, ['english', 'maths', 'science'])
