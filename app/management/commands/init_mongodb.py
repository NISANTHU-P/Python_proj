from django.core.management.base import BaseCommand
import pymongo
from django.conf import settings
from datetime import date, time, timedelta
import json
from app.utils.mongodb import get_mongodb_client, get_mongodb_db

class Command(BaseCommand):
    help = 'Initializes MongoDB with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Initializing MongoDB with sample data...')
        
        try:
            # Connect to MongoDB using our utility function
            db = get_mongodb_db()
            
            # Clear existing collections
            db.app_quote.drop()
            db.app_userpreference.drop()
            db.app_calendarevent.drop()
            
            # Create sample quotes
            quotes = [
                {"text": "The best way to predict the future is to invent it.", "author": "Alan Kay"},
                {"text": "Innovation distinguishes between a leader and a follower.", "author": "Steve Jobs"},
                {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
                {"text": "Stay hungry, stay foolish.", "author": "Stewart Brand"},
                {"text": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt"}
            ]
            
            # Create default user preference
            preferences = [
                {"location": "New York", "news_category": "general"}
            ]
            
            # Create sample calendar events
            today = date.today()
            events = [
                {
                    "title": "Team Meeting",
                    "description": "Weekly team sync-up",
                    "start_date": today.isoformat(),
                    "start_time": time(10, 0).isoformat(),
                    "all_day": False,
                    "priority": "medium"
                },
                {
                    "title": "Doctor Appointment",
                    "description": "Annual checkup",
                    "start_date": (today + timedelta(days=2)).isoformat(),
                    "start_time": time(14, 30).isoformat(),
                    "all_day": False,
                    "priority": "high"
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
                    "priority": "high"
                },
                {
                    "title": "Gym Session",
                    "start_date": (today + timedelta(days=1)).isoformat(),
                    "start_time": time(18, 0).isoformat(),
                    "all_day": False,
                    "priority": "medium"
                }
            ]
            
            # Insert data into MongoDB
            if quotes:
                db.app_quote.insert_many(quotes)
                self.stdout.write(f"Inserted {len(quotes)} quotes")
            
            if preferences:
                db.app_userpreference.insert_many(preferences)
                self.stdout.write(f"Inserted {len(preferences)} preferences")
            
            if events:
                db.app_calendarevent.insert_many(events)
                self.stdout.write(f"Inserted {len(events)} events")
            
            self.stdout.write(self.style.SUCCESS('Successfully initialized MongoDB with sample data'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to initialize MongoDB: {str(e)}'))
            
            # Print more detailed connection information for debugging
            self.stdout.write("\nConnection details:")
            self.stdout.write(f"URI: {settings.MONGODB_URI}")
            self.stdout.write(f"Database: {settings.MONGODB_NAME}")
            self.stdout.write(f"Username: {settings.MONGODB_USERNAME}")
            self.stdout.write(f"Password: {'*' * len(settings.MONGODB_PASSWORD) if settings.MONGODB_PASSWORD else 'Not set'}")
            self.stdout.write(f"Auth Source: {settings.MONGODB_AUTH_SOURCE}")
