from django.core.management.base import BaseCommand
from app.models import CalendarEvent
from datetime import date, time, timedelta

class Command(BaseCommand):
    help = 'Adds sample calendar events to the database'

    def handle(self, *args, **options):
        # Clear existing events
        CalendarEvent.objects.all().delete()
        
        # Get today's date
        today = date.today()
        
        # Create sample events
        events = [
            {
                'title': 'Team Meeting',
                'description': 'Weekly team sync-up',
                'start_date': today,
                'start_time': time(10, 0),  # 10:00 AM
                'all_day': False
            },
            {
                'title': 'Doctor Appointment',
                'description': 'Annual checkup',
                'start_date': today + timedelta(days=2),
                'start_time': time(14, 30),  # 2:30 PM
                'all_day': False
            },
            {
                'title': 'Birthday: Mom',
                'description': 'Don\'t forget to call!',
                'start_date': today + timedelta(days=5),
                'all_day': True
            },
            {
                'title': 'Project Deadline',
                'description': 'Submit final report',
                'start_date': today + timedelta(days=10),
                'all_day': True
            },
            {
                'title': 'Gym Session',
                'start_date': today + timedelta(days=1),
                'start_time': time(18, 0),  # 6:00 PM
                'all_day': False
            }
        ]
        
        # Add events to database
        for event_data in events:
            CalendarEvent.objects.create(**event_data)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully added {len(events)} sample events'))