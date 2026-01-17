from django.core.management.base import BaseCommand
from django.utils import timezone
from tracker.alerts import general_all_alerts, send_alert_emails


class Command(BaseCommand):
    help = 'Generate and send progress alerts to parents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Generate alerts but don\'t send emails',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            f'Starting alert generation at {timezone.now()}'
        ))

        # Generate alerts
        self.stdout.write('Generating alerts...')
        alerts_created = general_all_alerts()

        self.stdout.write(self.style.SUCCESS(
            f'✓ Created {alerts_created} new alert(s)'
        ))

        # Send emails
        if not options['dry_run']:
            self.stdout.write('Sending email notifications...')
            emails_sent = send_alert_emails()

            self.stdout.write(self.style.SUCCESS(
                f'✓ Sent {emails_sent} email notification(s)'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                '⚠ Dry run mode - emails not sent'
            ))
        self.stdout.write(self.style.SUCCESS(
            f'Alert generation completed at {timezone.now()}'
        ))