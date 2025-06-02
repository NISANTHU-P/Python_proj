from django.core.management.base import BaseCommand
from app.models import Quote, UserPreference, CalendarEvent
import json
import os
import pymongo
from django.conf import settings

class Command(BaseCommand):
    help = 'Migrates data from SQLite to MongoDB'

    def handle(self, *args, **options):
        self.stdout.write('Starting migration to MongoDB...')
        
        # Export data from SQLite models
        quotes = list(Quote.objects.all().values())
        preferences = list(UserPreference.objects.all().values())
        events = list(CalendarEvent.objects.all().values())
        
        self.stdout.write(f'Found {len(quotes)} quotes, {len(preferences)} preferences, and {len(events)} events')
        
        # Connect to MongoDB
        client = pymongo.MongoClient(
            settings.DATABASES['default']['CLIENT']['host'],
            username=settings.DATABASES['default']['CLIENT'].get('username', None),
            password=settings.DATABASES['default']['CLIENT'].get('password', None),
            authSource=settings.DATABASES['default']['CLIENT'].get('authSource', 'admin')
        )
        
        # Create database and collections
        db = client[settings.DATABASES['default']['NAME']]
        
        # Clear existing collections
        db.app_quote.drop()
        db.app_userpreference.drop()
        db.app_calendarevent.drop()
        
        # Convert date and time objects to strings for JSON serialization
        for event in events:
            if event.get('start_date'):
                event['start_date'] = event['start_date'].isoformat()
            if event.get('end_date'):
                event['end_date'] = event['end_date'].isoformat()
            if event.get('start_time'):
                event['start_time'] = event['start_time'].isoformat()
            if event.get('end_time'):
                event['end_time'] = event['end_time'].isoformat()
        
        # Insert data into MongoDB
        if quotes:
            db.app_quote.insert_many(quotes)
        if preferences:
            db.app_userpreference.insert_many(preferences)
        if events:
            db.app_calendarevent.insert_many(events)
        
        self.stdout.write(self.style.SUCCESS('Successfully migrated data to MongoDB'))