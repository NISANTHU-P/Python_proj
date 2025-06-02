from django.core.management.base import BaseCommand
from datetime import date, time, timedelta
from app.utils.mongodb import get_mongodb_db

class Command(BaseCommand):
    help = 'Initializes MongoDB with sample calendar events'

    def handle(self, *args, **options):
        self.stdout.write('Initializing MongoDB with sample calendar events...')
        
        try:
            # Connect to MongoDB
            db = get_mongodb_db()
            
            # Clear existing calendar events
            db.app_calendarevent.drop()
            
            # Create sample calendar events
            today = date.today()
            events = [
                {
                    "title": "Team Meeting",
                    "description": "Weekly team sync-up",
                    "start_date": today.isoformat(),
                    "start_time": time(10, 0).isoformat(),
                    "all_day": False,
                    "priority": "medium",
                    "location": "Conference Room A"
                },
                {
                    "title": "Doctor Appointment",
                    "description": "Annual checkup",
                    "start_date": (today + timedelta(days=2)).isoformat(),
                    "start_time": time(14, 30).isoformat(),
                    "all_day": False,
                    "priority": "high",
                    "location": "City Hospital"
                },
                {
                    "title": "Birthday: Mom",
                    "description": "Don't forget to call!",
                    "start_date": (today + timedelta(days=5)).isoformat(),
                    "all_day": True,
                    "priority": "high"
                },
                {
                    "title": "Project Deadline",
                    "description": "Submit final report",
                    "start_date": (today + timedelta(days=10)).isoformat(),
                    "all_day": True,
                    "priority": "high",
                    "location": "Office"
                },
                {
                    "title": "Gym Session",
                    "start_date": (today + timedelta(days=1)).isoformat(),
                    "start_time": time(18, 0).isoformat(),
                    "all_day": False,
                    "priority": "medium",
                    "location": "Fitness Center"
                }
            ]
            
            # Insert events into MongoDB
            if events:
                db.app_calendarevent.insert_many(events)
                self.stdout.write(f"Inserted {len(events)} calendar events")
            
            self.stdout.write(self.style.SUCCESS('Successfully initialized MongoDB with sample calendar events'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to initialize MongoDB calendar events: {str(e)}'))