from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from support.models import Ticket

class Command(BaseCommand):
    help = 'Computes and automatically closes answered tickets that have been inactive for > 3 days.'

    def handle(self, *args, **options):
        # We define inactive as 3 days ago.
        cutoff_date = timezone.now() - timedelta(days=3)
        
        # Find all ANSWERED tickets whose last update was before the cutoff
        expired_tickets = Ticket.objects.filter(
            status='ANSWERED',
            updated_at__lt=cutoff_date
        )
        
        count = expired_tickets.count()
        if count > 0:
            expired_tickets.update(status='CLOSED')
            self.stdout.write(self.style.SUCCESS(f'Successfully auto-closed {count} inactive tickets.'))
        else:
            self.stdout.write(self.style.SUCCESS('No inactive tickets found to close. All good.'))
