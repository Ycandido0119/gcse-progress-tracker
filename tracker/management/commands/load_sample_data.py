"""
Management command to populate database with sample data
Save this file as: tracker/management/commands/load_sample_data.py
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from tracker.models import (
    UserProfile, Subject, TermGoal, Feedback,
    Roadmap, RoadmapStep, ChecklistItem, Resource, StudySession
)


class Command(BaseCommand):
    help = 'Loads sample data for GCSE Progress Tracker'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Loading sample data...'))

        # Create users
        student, created = User.objects.get_or_create(
            username='student_brother',
            defaults={
                'email': 'brother@example.com',
                'first_name': 'Brother',
                'last_name': 'Student'
            }
        )
        if created:
            student.set_password('password123')
            student.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created student user: {student.username}'))

        parent, created = User.objects.get_or_create(
            username='parent_mum',
            defaults={
                'email': 'mum@example.com',
                'first_name': 'Parent',
                'last_name': 'Mum'
            }
        )
        if created:
            parent.set_password('password123')
            parent.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created parent user: {parent.username}'))

        # Create user profiles
        student_profile, created = UserProfile.objects.get_or_create(
            user=student,
            defaults={
                'role': 'student',
                'full_name': 'Your Brother',
                'year_group': 9,
                'email_notifications': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created student profile'))

        parent_profile, created = UserProfile.objects.get_or_create(
            user=parent,
            defaults={
                'role': 'parent',
                'full_name': 'Your Mum',
                'linked_student': student,
                'email_notifications': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created parent profile'))

        # Sample data for each subject
        subjects_data = {
            'maths': {
                'description': 'Core GCSE Mathematics covering algebra, geometry, and statistics',
                'current_level': 'Grade 5',
                'target_level': 'Grade 7',
                'feedback': {
                    'strengths': 'Shows strong understanding of algebraic manipulation and can solve complex equations confidently. Excellent problem-solving skills when working with fractions and decimals.',
                    'weaknesses': 'Struggles with geometry proofs and spatial reasoning. Sometimes makes careless errors in calculations under time pressure. Needs to show more working out.',
                    'areas_to_improve': 'Practice more geometry problems, especially circle theorems and angles. Work on exam technique and time management. Complete past papers under timed conditions.'
                }
            },
            'english': {
                'description': 'GCSE English Language and Literature',
                'current_level': 'Grade 6',
                'target_level': 'Grade 8',
                'feedback': {
                    'strengths': 'Excellent creative writing with sophisticated vocabulary. Strong analytical skills when discussing texts. Good understanding of literary techniques and can identify them effectively.',
                    'weaknesses': 'Sometimes struggles to structure analytical essays coherently. Needs to develop arguments more fully with deeper textual evidence. Handwriting speed affects completion of timed essays.',
                    'areas_to_improve': 'Practice essay planning techniques. Work on using PEE (Point, Evidence, Explain) structure consistently. Read more widely to expand vocabulary and understanding of different writing styles.'
                }
            },
            'science': {
                'description': 'Combined Science (Biology, Chemistry, Physics)',
                'current_level': 'Grade 5',
                'target_level': 'Grade 6',
                'feedback': {
                    'strengths': 'Strong practical skills in lab work. Good understanding of biological concepts, especially cells and organs. Asks thoughtful questions during lessons.',
                    'weaknesses': 'Finds physics equations challenging, particularly electricity and forces. Chemistry calculations need more practice. Sometimes confuses key terminology between the three sciences.',
                    'areas_to_improve': 'Create flashcards for key terms and equations. Practice calculations regularly, especially moles and forces. Watch videos to visualize abstract physics concepts.'
                }
            },
            'mandarin': {
                'description': 'GCSE Mandarin Chinese',
                'current_level': 'Grade 4',
                'target_level': 'Grade 6',
                'feedback': {
                    'strengths': 'Good pronunciation and tone accuracy. Shows enthusiasm for learning Chinese culture. Confident in speaking activities and role plays.',
                    'weaknesses': 'Character writing needs significant improvement - struggles to remember stroke order. Limited vocabulary for essay writing. Grammar patterns not yet fully internalized.',
                    'areas_to_improve': 'Practice writing characters daily using apps like Skritter. Read simple Chinese texts regularly. Create vocabulary lists organized by themes. Watch Chinese TV shows with subtitles.'
                }
            }
        }

        # Create subjects, term goals, and feedback
        deadline = date.today() + timedelta(days=90)  # 3 months from now
        
        for subject_key, data in subjects_data.items():
            # Create subject
            subject, created = Subject.objects.get_or_create(
                user=student,
                name=subject_key,
                defaults={'description': data['description']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created subject: {subject.get_name_display()}'))

            # Create term goal
            term_goal, created = TermGoal.objects.get_or_create(
                subject=subject,
                term='spring_2025',
                defaults={
                    'current_level': data['current_level'],
                    'target_level': data['target_level'],
                    'deadline': deadline
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created term goal: {data["current_level"]} → {data["target_level"]}'))

            # Create feedback
            feedback, created = Feedback.objects.get_or_create(
                subject=subject,
                feedback_date=date.today(),
                defaults={
                    'strengths': data['feedback']['strengths'],
                    'weaknesses': data['feedback']['weaknesses'],
                    'areas_to_improve': data['feedback']['areas_to_improve']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created teacher feedback'))

            # Create sample study sessions (last 2 weeks)
            for i in range(5):
                session_date = date.today() - timedelta(days=i*2)
                hours = 1.5 if i % 2 == 0 else 2.0
                
                StudySession.objects.get_or_create(
                    user=student,
                    subject=subject,
                    session_date=session_date,
                    defaults={
                        'hours_spent': hours,
                        'notes': f'Studied {subject.get_name_display()} focusing on recent feedback areas'
                    }
                )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created 5 study sessions'))

        # Create a sample roadmap for Mathematics
        maths_subject = Subject.objects.get(user=student, name='maths')
        maths_goal = TermGoal.objects.get(subject=maths_subject, term='spring_2025')
        
        roadmap, created = Roadmap.objects.get_or_create(
            subject=maths_subject,
            term_goal=maths_goal,
            defaults={
                'title': 'Mathematics Grade 5 → 7 Improvement Plan',
                'overview': 'This roadmap focuses on strengthening geometry skills, improving exam technique, and building confidence in problem-solving. The plan prioritizes weaknesses while maintaining current strengths. Current Grade 5 shows solid algebraic foundation but geometry understanding needs significant development. To reach Grade 7, must master circle theorems, angle relationships, and geometric proofs.',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created sample roadmap for Maths'))
            
            # Create roadmap steps
            steps_data = [
                {
                    'order': 1,
                    'title': 'Master Angle Relationships',
                    'description': 'Focus on angles in parallel lines, triangles, and polygons. Understand alternate, corresponding, and co-interior angles.',
                    'category': 'weakness',
                    'difficulty': 'medium',
                    'hours': 8,
                    'checklist': [
                        'Watch BBC Bitesize videos on angles in parallel lines',
                        'Complete 20 practice problems on angle calculations',
                        'Create a visual reference sheet for all angle rules',
                        'Take a practice quiz and score 80%+'
                    ],
                    'resources': [
                        {
                            'type': 'video',
                            'title': 'Angles in Parallel Lines - BBC Bitesize',
                            'url': 'https://www.bbc.co.uk/bitesize/guides/zshb97h/revision/1',
                            'description': 'Comprehensive video covering all angle relationships'
                        },
                        {
                            'type': 'exercise',
                            'title': 'Angles Practice Worksheet',
                            'url': 'https://www.mathsisfun.com/geometry/parallel-lines.html',
                            'description': 'Interactive exercises with instant feedback'
                        }
                    ]
                },
                {
                    'order': 2,
                    'title': 'Circle Theorems Deep Dive',
                    'description': 'Learn all major circle theorems including angles at center, angles in semicircle, and tangent properties.',
                    'category': 'weakness',
                    'difficulty': 'hard',
                    'hours': 12,
                    'checklist': [
                        'Memorize all 8 main circle theorems',
                        'Create flashcards for each theorem',
                        'Complete 30 circle theorem problems',
                        'Explain each theorem to someone else',
                        'Complete a past paper section on circles'
                    ],
                    'resources': [
                        {
                            'type': 'video',
                            'title': 'Circle Theorems Explained - Corbettmaths',
                            'url': 'https://corbettmaths.com/contents/',
                            'description': 'Step-by-step explanations with examples'
                        }
                    ]
                },
                {
                    'order': 3,
                    'title': 'Develop Exam Technique',
                    'description': 'Practice showing working out, time management, and checking answers. Build confidence in exam conditions.',
                    'category': 'level_up',
                    'difficulty': 'medium',
                    'hours': 10,
                    'checklist': [
                        'Complete 3 full past papers under timed conditions',
                        'Review marking schemes for all practice papers',
                        'Create a checklist for showing working out',
                        'Practice quick mental arithmetic daily (10 mins)',
                        'Learn to estimate answers before calculating'
                    ],
                    'resources': []
                },
                {
                    'order': 4,
                    'title': 'Strengthen Algebra Skills',
                    'description': 'Continue building on current strength in algebra to ensure Grade 7 level mastery.',
                    'category': 'strength',
                    'difficulty': 'easy',
                    'hours': 6,
                    'checklist': [
                        'Complete 10 challenging algebraic problems weekly',
                        'Practice quadratic equations including factorizing',
                        'Work on simultaneous equations',
                        'Try GCSE Grade 7-9 algebra questions'
                    ],
                    'resources': []
                }
            ]
            
            for step_data in steps_data:
                step = RoadmapStep.objects.create(
                    roadmap=roadmap,
                    order_number=step_data['order'],
                    title=step_data['title'],
                    description=step_data['description'],
                    category=step_data['category'],
                    difficulty=step_data['difficulty'],
                    estimated_hours=step_data['hours']
                )
                
                # Create checklist items
                for task in step_data['checklist']:
                    ChecklistItem.objects.create(
                        roadmap_step=step,
                        task_description=task
                    )
                
                # Create resources
                for resource_data in step_data['resources']:
                    Resource.objects.create(
                        roadmap_step=step,
                        resource_type=resource_data['type'],
                        title=resource_data['title'],
                        url=resource_data['url'],
                        description=resource_data['description']
                    )
            
            roadmap.update_total_steps()
            self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(steps_data)} roadmap steps with checklists'))

        self.stdout.write(self.style.SUCCESS('\n========================================'))
        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully! 🎉'))
        self.stdout.write(self.style.SUCCESS('========================================'))
        self.stdout.write(self.style.WARNING('\nLogin Credentials:'))
        self.stdout.write(self.style.WARNING('Student - username: student_brother, password: password123'))
        self.stdout.write(self.style.WARNING('Parent  - username: parent_mum, password: password123'))
        self.stdout.write(self.style.SUCCESS('\nYou can now view the data at: http://127.0.0.1:8000/admin'))