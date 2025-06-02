from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CalendarEvent
from .utils.mongodb import get_mongodb_db

class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'start_time', 'all_day')
    list_filter = ('start_date', 'all_day')
    search_fields = ('title', 'description')

# Only register non-abstract models
admin.site.register(CalendarEvent, CalendarEventAdmin)
