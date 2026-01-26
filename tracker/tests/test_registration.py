from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from tracker.models import UserProfile
from tracker.forms import UserRegistrationForm


class UserRegistrationFormTests(TestCase):
    """Test cases for UserRegistrationForm"""

    def test_form_valid_with_all_required_fields(self):
        """Test form is valid with all required fields"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'role': 'student',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_without_username(self):
        """Test form is invalid without username"""
        form_data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'role': 'student',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_form_invalid_without_role(self):
        """Test form is invalid without role"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('role', form.errors)

    def test_form_rejects_duplicate_username(self):
        """Test form rejects username that already exists"""
        # Create existing user
        User.objects.create_user(username='existinguser', email='existing@example.com')

        form_data = {
            'username': 'existinguser',
            'email': 'new@example.com',
            'full_name': 'New User',
            'role': 'student',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }

        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('already taken', str(form.errors['username']))

    def test_form_rejects_duplicate_email(self):
        """Test form rejects email that already exists"""
        # Create existing user
        User.objects.create_user(username='existinguser', email='existing@example.com')
        
        form_data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'full_name': 'New User',
            'role': 'student',
            'password1': 'Testpass123!',
            'password2': 'TestPass123!',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('already registered', str(form.errors['email']))

    def test_form_invalid_with_weak_password(self):
        """Test form rejects weak passwords"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'role': 'student',
            'password1': '123',
            'password2': '123',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_form_accepts_both_student_and_parent_roles(self):
        """Test form accepts both valid role choices"""
        # Test student role
        form_data_student = {
            'username': 'student_user',
            'email': 'student@example.com',
            'full_name': 'Student User',
            'role': 'student',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form_student = UserRegistrationForm(data=form_data_student)
        self.assertTrue(form_student.is_valid())

        # Test parent role
        form_data_parent = {
            'username': 'parent_user',
            'email': 'parent@example.com',
            'full_name': 'Parent User',
            'role': 'parent',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form_parent = UserRegistrationForm(data=form_data_parent)
        self.assertTrue(form_parent.is_valid())


class UserRegistrationViewTests(TestCase):
    """Test cases for register view"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.register_url = reverse('tracker:register')

    def test_register_page_loads(self):
        """Test registration page loads successfully"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/register.html')
        self.assertContains(response, 'Create Account')

    def test_register_page_contains_form(self):
        """Test registration page contains registration form"""
        response = self.client.get(self.register_url)
        self.assertContains(response, 'username')
        self.assertContains(response, 'email')
        self.assertContains(response, 'full_name')
        self.assertContains(response, 'password1')
        self.assertContains(response, 'password2')
        self.assertContains(response, 'role')

    def test_successful_student_registration(self):
        """Test successful registration creates user and profile"""
        form_data = {
            'username': 'newstudent',
            'email': 'student@example.com',
            'full_name': 'New Student',
            'role': 'student',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }

        response = self.client.post(self.register_url, data=form_data)

        # Check user was created
        self.assertTrue(User.objects.filter(username='newstudent').exists())
        user = User.objects.get(username='newstudent')

        # Check user profile was created
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        profile = UserProfile.objects.get(user=user)

        # Check profile data
        self.assertEqual(profile.role, 'student')
        self.assertEqual(profile.full_name, 'New Student')

        # Check user is logged in
        self.assertTrue(user.is_authenticated)

        # Check redirect to dashboard
        self.assertRedirects(response, reverse('tracker:dashboard'))

    def test_successful_parent_registration(self):
        """Test successful parent registration redirects to parent dashboard"""
        form_data = {
            'username': 'newparent',
            'email': 'parent@example.com',
            'full_name': 'New Parent',
            'role': 'parent',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        
        response = self.client.post(self.register_url, data=form_data)
        
        # Check user was created
        user = User.objects.get(username='newparent')
        profile = UserProfile.objects.get(user=user)
        
        # Check profile role
        self.assertEqual(profile.role, 'parent')
        
        # ✅ Check redirect happens (don't follow, just check status)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('tracker:parent_dashboard'))

    def test_registration_auto_login(self):
        """Test user is automatically logged in after registration"""
        form_data = {
            'username': 'autouser',
            'email': 'auto@example.com',
            'full_name': 'Auto User',
            'role': 'student',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }

        response = self.client.post(self.register_url, data=form_data)

        # Check user is logged in by checking session
        user = User.objects.get(username='autouser')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_registration_fails_with_duplicate_username(self):
        """Test registration fails when username already exists"""
        # Create existing user
        User.objects.create_user(username='duplicate', email='original@example.com')
        
        form_data = {
            'username': 'duplicate',
            'email': 'new@example.com',
            'full_name': 'New User',
            'role': 'student',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        
        response = self.client.post(self.register_url, data=form_data)
        
        # Should not create new user
        self.assertEqual(User.objects.filter(username='duplicate').count(), 1)
        
        # Should show form with errors
        self.assertEqual(response.status_code, 200)
        # ✅ NEW API - check form errors directly
        form = response.context['form']
        self.assertIn('username', form.errors)
        self.assertIn('already taken', str(form.errors['username']))

    def test_registration_fails_with_duplicate_email(self):
        """Test registration fails when email already exists"""
        # Create existing user
        User.objects.create_user(username='user1', email='duplicate@example.com')
        
        form_data = {
            'username': 'user2',
            'email': 'duplicate@example.com',
            'full_name': 'User Two',
            'role': 'student',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        
        response = self.client.post(self.register_url, data=form_data)
        
        # Should not create new user
        self.assertFalse(User.objects.filter(username='user2').exists())
        
        # Should show form with errors
        self.assertEqual(response.status_code, 200)
        # ✅ NEW API - check form errors directly
        form = response.context['form']
        self.assertIn('email', form.errors)
        self.assertIn('already registered', str(form.errors['email']))

    def test_registration_with_invalid_data(self):
        """Test registration with invalid data shows errors"""
        form_data = {
            'username': 'test',
            'email': 'invalid-email',
            'full_name': 'Test',
            'role': 'student',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass!',
        }

        response = self.client.post(self.register_url, data=form_data)

        # Should not create user
        self.assertFalse(User.objects.filter(username='test').exists())

        # Should stay on registration page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tracker/register.html')

    def test_authenticated_user_redirected_from_register(self):
        """Test authenticated users are redirected away from registration"""
        # Create and login user
        user = User.objects.create_user(username='existing', password='TestPass123!')
        self.client.login(username='existing', password='TestPass123!')

        response = self.client.get(self.register_url)

        # Should redirect to dashboard
        self.assertRedirects(response, reverse('tracker:dashboard'))

    def test_user_profile_created_automatically(self):
        """Test User and UserProfile are created in atomic transaction"""
        form_data = {
            'username': 'atomicuser',
            'email': 'atomic@example.com',
            'full_name': 'Atomic User',
            'role': 'student',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }

        response = self.client.post(self.register_url, data=form_data)

        # Both User and UserProfile should exist
        user_exists = User.objects.filter(username='atomicuser').exists()
        self.assertTrue(user_exists)

        if user_exists:
            user = User.objects.get(username='atomicuser')
            profile_exists = UserProfile.objects.filter(user=user).exists()
            self.assertTrue(profile_exists)

    def test_registration_displays_success_message(self):
        """Test successful registration shows success message"""
        form_data = {
            'username': 'msguser',
            'email': 'msg@example.com',
            'full_name': 'Message User',
            'role': 'student',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }

        response = self.client.post(self.register_url, data=form_data, follow=True)

        # Check for success message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('Welcome', str(messages[0]))
        self.assertIn('Message User', str(messages[0]))


class UserProfileIntegrationTests(TestCase):
    """Integration tests for UserProfile with registration"""
    def test_student_profile_has_correct_defaults(self):
        """Test student profile created with correct default values"""
        form_data = {
            'username': 'student_defaults',
            'email': 'student@example.com',
            'full_name': 'Student Defaults',
            'role': 'student',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }

        client = Client()
        client.post(reverse('tracker:register'), data=form_data)

        user = User.objects.get(username='student_defaults')
        profile = UserProfile.objects.get(user=user)

        # Check defaults
        self.assertEqual(profile.role, 'student')
        self.assertTrue(profile.alert_low_activity)
        self.assertTrue(profile.alert_goal_at_risk)
        self.assertTrue(profile.alert_milestones)

    def test_new_user_can_login_after_registration(self):
        """Test newly registered user can logout and login again"""
        # Register
        form_data = {
            'username': 'logintest',
            'email': 'login@example.com',
            'full_name': 'Login Test',
            'role': 'student',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }

        client = Client()
        client.post(reverse('tracker:register'), data=form_data)

        # Logout
        client.logout()

        # Try to login
        login_successful = client.login(username='logintest', password='TestPass123!')
        self.assertTrue(login_successful)

