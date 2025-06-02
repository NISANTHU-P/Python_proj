from django.db import models
import datetime

# Regular Django models for SQLite
class Quote(models.Model):
    text = models.TextField()
    author = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.text} - {self.author}"

class UserPreference(models.Model):
    location = models.CharField(max_length=100, default="New York")
    news_category = models.CharField(max_length=50, default="general")
    
    def __str__(self):
        return f"Preferences for {self.location}"

class CalendarEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    all_day = models.BooleanField(default=False)
    location = models.CharField(max_length=200, blank=True, null=True)
    priority = models.CharField(max_length=20, default='medium')
    reminder = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
