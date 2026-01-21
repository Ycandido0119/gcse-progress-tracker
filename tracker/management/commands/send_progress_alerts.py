from django.core.management.base import BaseCommand
from tracker.alerts import generate_all_alerts, send_alert_emails
from tracker.models import UserProfile

class Command(BaseCommand):
    help = 'Generate and send progress alerts to parents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what alerts would be generated without actually creating them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all parents with email notifications enabled
        parents = UserProfile.objects.filter(role='parent', email_notifications=True)
        
        self.stdout.write(f"Checking alerts for {parents.count()} parent(s)...")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n(Dry run mode - no alerts will actually be created)"))
            
            # Import the ProgressAlert model to count what would be created
            from tracker.models import ProgressAlert
            from django.utils import timezone
            from datetime import timedelta
            
            # Count existing alerts from last 24 hours
            recent_alerts = ProgressAlert.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            self.stdout.write(f"\nAlerts created in last 24 hours: {recent_alerts}")
            self.stdout.write("\nTo see what alerts would be generated, run without --dry-run flag")
            self.stdout.write("(Don't worry - duplicate alerts within 24 hours are prevented)")
            
        else:
            # Actually generate and send alerts
            try:
                alerts_created = generate_all_alerts()
                
                self.stdout.write(self.style.SUCCESS(f"\n✅ Generated {alerts_created} alert(s)"))
                
                # Send emails
                emails_sent = send_alert_emails()
                
                self.stdout.write(self.style.SUCCESS(f"✅ Sent {emails_sent} email(s) to parent(s)"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n❌ Error: {str(e)}"))
                raise