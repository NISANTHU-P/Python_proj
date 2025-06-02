import os
import pymongo
from bson import ObjectId
import datetime

def get_mongodb_client():
    """Get a MongoDB client connection"""
    # Build connection string with authentication if credentials are provided
    if settings.MONGODB_USERNAME and settings.MONGODB_PASSWORD:
        client = pymongo.MongoClient(
            settings.MONGODB_URI,
            username=settings.MONGODB_USERNAME,
            password=settings.MONGODB_PASSWORD,
            authSource=settings.MONGODB_AUTH_SOURCE
        )
    else:
        # Connect without authentication
        client = pymongo.MongoClient(settings.MONGODB_URI)
    
    return client

def get_mongodb_db():
    """Get MongoDB database connection"""
    try:
        # Get MongoDB connection details from environment variables
        uri = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
        db_name = os.environ.get('MONGODB_NAME', 'vsm_db')
        
        # Connect to MongoDB
        client = pymongo.MongoClient(uri)
        db = client[db_name]
        print(f"Connected to MongoDB: {db_name}")
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise

def get_calendar_events_from_mongodb():
    """Get calendar events from MongoDB"""
    try:
        print("Fetching events from MongoDB...")
        db = get_mongodb_db()
        events = list(db.app_calendarevent.find())
        print(f"Found {len(events)} events in MongoDB")
        
        # Convert ObjectId to string for JSON serialization
        for event in events:
            event['_id'] = str(event['_id'])
        
        return events
    except Exception as e:
        print(f"Error fetching events from MongoDB: {e}")
        return []

def save_calendar_event_to_mongodb(event_data):
    """Save a calendar event to MongoDB"""
    try:
        print("Attempting to save event to MongoDB...")
        db = get_mongodb_db()
        
        # Ensure dates are in ISO format
        if 'start_date' in event_data and event_data['start_date']:
            # No need to convert if already a string
            if not isinstance(event_data['start_date'], str):
                event_data['start_date'] = event_data['start_date'].isoformat()
                
        if 'end_date' in event_data and event_data['end_date']:
            if not isinstance(event_data['end_date'], str):
                event_data['end_date'] = event_data['end_date'].isoformat()
                
        if 'start_time' in event_data and event_data['start_time']:
            if not isinstance(event_data['start_time'], str):
                event_data['start_time'] = event_data['start_time'].isoformat()
                
        if 'end_time' in event_data and event_data['end_time']:
            if not isinstance(event_data['end_time'], str):
                event_data['end_time'] = event_data['end_time'].isoformat()
        
        print(f"Formatted event data: {event_data}")
        result = db.app_calendarevent.insert_one(event_data)
        inserted_id = str(result.inserted_id)
        print(f"Event saved with ID: {inserted_id}")
        return inserted_id
    except Exception as e:
        print(f"Error saving calendar event to MongoDB: {e}")
        return None

def update_calendar_event_in_mongodb(event_id, event_data):
    """Update a calendar event in MongoDB"""
    try:
        db = get_mongodb_db()
        # Ensure dates are in ISO format
        if 'start_date' in event_data and event_data['start_date']:
            if not isinstance(event_data['start_date'], str):
                event_data['start_date'] = event_data['start_date'].isoformat()
                
        if 'end_date' in event_data and event_data['end_date']:
            if not isinstance(event_data['end_date'], str):
                event_data['end_date'] = event_data['end_date'].isoformat()
                
        if 'start_time' in event_data and event_data['start_time']:
            if not isinstance(event_data['start_time'], str):
                event_data['start_time'] = event_data['start_time'].isoformat()
                
        if 'end_time' in event_data and event_data['end_time']:
            if not isinstance(event_data['end_time'], str):
                event_data['end_time'] = event_data['end_time'].isoformat()
        
        # Ensure event_id is a valid ObjectId
        if not ObjectId.is_valid(event_id):
            print(f"Invalid ObjectId format: {event_id}")
            return False
            
        result = db.app_calendarevent.update_one(
            {"_id": ObjectId(event_id)},
            {"$set": event_data}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating calendar event in MongoDB: {e}")
        return False

def delete_calendar_event_from_mongodb(event_id):
    """Delete a calendar event from MongoDB"""
    db = get_mongodb_db()
    result = db.app_calendarevent.delete_one({"_id": ObjectId(event_id)})
    return result.deleted_count > 0

def get_calendar_event_by_id(event_id):
    """Get a calendar event by ID from MongoDB"""
    db = get_mongodb_db()
    event = db.app_calendarevent.find_one({"_id": ObjectId(event_id)})
    if event:
        event['_id'] = str(event['_id'])
    return event







