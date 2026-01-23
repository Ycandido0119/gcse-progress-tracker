from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tracker.models import UserProfile

class Command(BaseCommand):
    help = 'Create demo users for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo user...')

        # Create student account
        if not User.objects.filter(username='student_brother').exists():
            student = User.objects.create_user(
                username='student_brother',
                password='password123',
                email='student@example.com',
                first_name='Your',
                last_name='Brother'
            )
            UserProfile.objects.create(
                user=student,
                role='student'
            )
            self.stdout.write(self.style.SUCCESS('✅ Created student_brother account'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  student_brother already exists'))

        # Create parent account
        if not User.objects.filter(username='parent_mum').exists():
            parent = User.objects.create_user(
                username='parent_mum',
                password='password123',
                email='parent@example.com',
                first_name='Test',
                last_name='Parent'
            )
            parent_profile = UserProfile.objects.create(
                user=parent,
                role='parent',
                email_notifications=True,
                alert_low_activity=True,
                alert_low_activity_days=3,
                alert_goal_at_risk=True,
                alert_goal_at_risk_days=7,
                alert_milestones=True,
                alert_roadmap_completed=True,
                alert_streak_broken=True,
                alert_new_feedback=True
            )

            # Link parent to student
            try:
                student_user = User.objects.get(username='student_brother')
                parent_profile.linked_students.add(student_user)
                self.stdout.write(self.style.SUCCESS('✅ Created parent_mum and linked to student'))
            except User.DoesNotExist:
                self.stdout.write(self.style.SUCCESS('✅ Created parent_mum (student not found yet)'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  parent_mum already exists'))

        self.stdout.write(self.style.SUCCESS('\n🎉 Demo users setup complete!'))