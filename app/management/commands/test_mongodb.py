from django.core.management.base import BaseCommand
from app.utils.mongodb import get_mongodb_client, get_mongodb_db
import pymongo
from django.conf import settings

class Command(BaseCommand):
    help = 'Test MongoDB connection'

    def handle(self, *args, **options):
        self.stdout.write('Testing MongoDB connection...')
        
        try:
            # Try to connect to MongoDB
            client = get_mongodb_client()
            
            # Print server info to verify connection
            server_info = client.server_info()
            self.stdout.write(f"Connected to MongoDB version: {server_info.get('version', 'unknown')}")
            
            # Get database
            db = get_mongodb_db()
            
            # List collections
            collections = db.list_collection_names()
            self.stdout.write(f"Collections in {settings.MONGODB_NAME}: {', '.join(collections) if collections else 'None'}")
            
            # Create a test collection
            test_collection = db.test_collection
            
            # Insert a test document
            result = test_collection.insert_one({"test": "document", "source": "Django"})
            self.stdout.write(f"Inserted test document with ID: {result.inserted_id}")
            
            # Retrieve the document
            doc = test_collection.find_one({"_id": result.inserted_id})
            self.stdout.write(f"Retrieved document: {doc}")
            
            # Clean up - remove test document
            test_collection.delete_one({"_id": result.inserted_id})
            self.stdout.write("Test document removed")
            
            self.stdout.write(self.style.SUCCESS('MongoDB connection test successful!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'MongoDB connection test failed: {str(e)}'))
            
            # Print more detailed connection information for debugging
            self.stdout.write("\nConnection details:")
            self.stdout.write(f"URI: {settings.MONGODB_URI}")
            self.stdout.write(f"Database: {settings.MONGODB_NAME}")
            self.stdout.write(f"Username: {settings.MONGODB_USERNAME}")
            self.stdout.write(f"Password: {'*' * len(settings.MONGODB_PASSWORD) if settings.MONGODB_PASSWORD else 'Not set'}")
            self.stdout.write(f"Auth Source: {settings.MONGODB_AUTH_SOURCE}")
