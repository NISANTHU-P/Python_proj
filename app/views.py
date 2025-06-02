from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
import requests
import datetime
import random
import os
from .models import Quote, UserPreference, CalendarEvent
import json
from datetime import timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bson import ObjectId
from app.utils.mongodb import (
    get_mongodb_db,
    get_calendar_events_from_mongodb,
    save_calendar_event_to_mongodb,
    update_calendar_event_in_mongodb,
    delete_calendar_event_from_mongodb,
    get_calendar_event_by_id
)

def index(request):
    # Get all the data for the dashboard
    weather_data = get_weather()
    news_data = get_news()  # This will now get news specific to the location
    datetime_data = get_datetime()
    quote_data = get_quote()
    calendar_data = get_calendar_events()
    
    # Ensure news is a list
    if not isinstance(news_data, list):
        news_data = get_default_news()
    
    context = {
        'weather': weather_data,
        'news': news_data,
        'datetime': datetime_data,
        'quote': quote_data,
        'calendar': calendar_data,
    }
    return render(request, 'app/index.html', context)

def calendar_view(request):
    """View for displaying calendar events"""
    # Get all the data for the dashboard
    weather_data = get_weather()
    news_data = get_news()
    datetime_data = get_datetime()
    quote_data = get_quote()
    
    # Get calendar events with debugging
    print("Fetching calendar events for display...")
    calendar_data = get_calendar_events()
    print(f"Calendar data: {calendar_data}")
    
    # Ensure news is a list
    if not isinstance(news_data, list):
        news_data = get_default_news()
    
    context = {
        'weather': weather_data,
        'news': news_data,
        'datetime': datetime_data,
        'quote': quote_data,
        'calendar': calendar_data,
    }
    return render(request, 'app/calendar.html', context)

def get_weather():
    try:
        # Get user preferences or use default
        db = get_mongodb_db()
        pref_data = db.app_userpreference.find_one()
        
        if not pref_data:
            # Create default preference if none exists
            pref_data = {"location": "New York", "news_category": "general"}
            db.app_userpreference.insert_one(pref_data)
            print("Created default user preference with location: New York")
        
        location = pref_data.get('location', 'New York')
        print(f"Getting weather for location: {location}")
        
        api_key = os.environ.get('OPENWEATHER_API_KEY')
        
        # Check if API key is available
        if not api_key:
            print("Warning: No OpenWeather API key found in environment variables")
            return get_default_weather_data(location)
        
        # Get current weather data
        current_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        print(f"Fetching weather data from: {current_url}")
        
        current_response = requests.get(current_url, timeout=10)
        
        # Check if the response is successful
        if current_response.status_code != 200:
            print(f"Weather API error for location '{location}': {current_response.status_code}")
            print(f"Response content: {current_response.text}")
            return get_default_weather_data(location)
        
        # Parse the response
        current_data = current_response.json()
        
        # Debug output
        print(f"Weather API response for {location}: {current_data.keys()}")
        
        # Verify that the response contains the expected data
        if 'coord' not in current_data:
            print(f"Missing 'coord' in weather API response: {current_data}")
            return get_default_weather_data(location)
        
        # Get coordinates for forecast
        lat = current_data['coord']['lat']
        lon = current_data['coord']['lon']
        
        # Get forecast data using OneCall API
        forecast_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={api_key}&units=metric"
        forecast_response = requests.get(forecast_url, timeout=10)
        
        # Check if forecast response is successful
        if forecast_response.status_code != 200:
            print(f"Forecast API error: {forecast_response.status_code}")
            print(f"Response content: {forecast_response.text}")
            
            # Create empty forecast if API fails
            forecast_data = {'daily': []}
        else:
            forecast_data = forecast_response.json()
        
        # Current weather
        current = {
            'temp': round(current_data['main']['temp']),
            'feels_like': round(current_data['main']['feels_like']),
            'humidity': current_data['main']['humidity'],
            'wind_speed': round(current_data['wind']['speed']),
            'wind_direction': get_wind_direction(current_data['wind']['deg']),
            'condition': current_data['weather'][0]['main'],
            'description': current_data['weather'][0]['description'],
            'icon': current_data['weather'][0]['icon'],
            'pressure': current_data['main']['pressure'],
            'visibility': current_data.get('visibility', 0) / 1000,  # Convert to km
            'rain': current_data.get('rain', {}).get('1h', 0),  # Rain in last hour, if available
            'clouds': current_data['clouds']['all'],  # Cloud coverage percentage
            'sunrise': datetime.datetime.fromtimestamp(current_data['sys']['sunrise']).strftime('%H:%M'),
            'sunset': datetime.datetime.fromtimestamp(current_data['sys']['sunset']).strftime('%H:%M'),
        }
        
        # 10-day forecast (actually 8 days including today, as that's the max from the free API)
        forecast = []
        daily_data = forecast_data.get('daily', [])
        
        if not daily_data and 'list' in forecast_data:
            # Handle case where we might get a different format
            daily_data = forecast_data['list']
        
        for i in range(min(10, len(daily_data))):
            day_data = daily_data[i]
            
            # Handle different API response formats
            if 'temp' in day_data and isinstance(day_data['temp'], dict):
                # OneCall API format
                temp_max = round(day_data['temp']['max'])
                temp_min = round(day_data['temp']['min'])
            elif 'main' in day_data:
                # 5-day forecast API format
                temp_max = round(day_data['main']['temp_max'])
                temp_min = round(day_data['main']['temp_min'])
            else:
                # Default values if format is unknown
                temp_max = 0
                temp_min = 0
            
            # Get timestamp
            timestamp = day_data.get('dt')
            date_str = datetime.datetime.fromtimestamp(timestamp).strftime('%a, %b %d')
            
            # Get weather condition
            weather = day_data.get('weather', [{}])[0]
            
            day = {
                'date': date_str,
                'temp_max': temp_max,
                'temp_min': temp_min,
                'condition': weather.get('main', 'Unknown'),
                'description': weather.get('description', 'No description available'),
                'icon': weather.get('icon', '01d'),
                'humidity': day_data.get('humidity', 0),
                'wind_speed': round(day_data.get('wind_speed', 0)),
                'wind_direction': get_wind_direction(day_data.get('wind_deg', 0)),
                'rain': day_data.get('rain', 0),  # Rain in mm, if available
                'clouds': day_data.get('clouds', 0),  # Cloud coverage percentage
                'pop': int(day_data.get('pop', 0) * 100),  # Probability of precipitation (%)
            }
            forecast.append(day)
        
        return {
            'current': current, 
            'forecast': forecast, 
            'location': current_data['name'],
            'country': current_data['sys']['country']
        }
    except KeyError as e:
        print(f"Weather API KeyError: {e}")
        return get_default_weather_data("Unknown")
    except Exception as e:
        print(f"Weather API error: {e}")
        return get_default_weather_data("Unknown")

def get_default_weather_data(location):
    """Return default weather data when API fails"""
    return {
        'error': "Could not fetch weather data",
        'current': {
            'temp': 20,
            'feels_like': 20,
            'humidity': 50,
            'wind_speed': 5,
            'wind_direction': 'N/A',
            'condition': 'Clouds',
            'description': 'Weather data unavailable',
            'icon': '01d',  # Default icon
            'pressure': 1013,
            'visibility': 10,
            'rain': 0,
            'clouds': 0,
            'sunrise': '06:00',
            'sunset': '18:00',
        },
        'forecast': [
            {
                'date': 'Today',
                'temp_max': 22,
                'temp_min': 18,
                'condition': 'Clouds',
                'description': 'Weather data unavailable',
                'icon': '01d',
                'humidity': 50,
                'wind_speed': 5,
                'wind_direction': 'N',
                'rain': 0,
                'clouds': 0,
                'pop': 0,
            }
        ],
        'location': location,
        'country': 'N/A'
    }

def get_wind_direction(degrees):
    """Convert wind direction in degrees to cardinal direction"""
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    index = round(degrees / (360 / len(directions))) % len(directions)
    return directions[index]

def get_news():
    try:
        # Get user preferences or use default
        db = get_mongodb_db()
        pref_data = db.app_userpreference.find_one()
        
        if not pref_data:
            # Create default preference if none exists
            pref_data = {"location": "New York", "news_category": "general"}
            db.app_userpreference.insert_one(pref_data)
            print("Created default user preference with location: New York")
        
        location = pref_data.get('location', 'New York')
        print(f"Getting news for location: {location}")
            
        api_key = os.environ.get('NEWS_API_KEY')
        
        # Check if API key is available
        if not api_key:
            print("Warning: No News API key found in environment variables")
            return get_default_news()
            
        # Debug output
        print(f"Fetching news specifically for location: {location}")
        
        # Try to get news by exact location name first
        url = f"https://newsapi.org/v2/everything?q=\"{location}\"&sortBy=publishedAt&language=en&apiKey={api_key}"
        print(f"Fetching news from: {url}")
        
        response = requests.get(url, timeout=10)
        
        # Debug output
        print(f"Location-specific news API response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"News API error: {response.status_code}")
            print(f"Response content: {response.text}")
            return get_default_news()
            
        data = response.json()
        
        # Debug output
        print(f"News API response: {data.keys()}")
        print(f"Total results for exact location: {data.get('totalResults', 0)}")
        
        # If no articles found with exact location, try without quotes
        if data.get('totalResults', 0) == 0:
            print(f"No news found for exact location '{location}', trying broader search")
            
            # Try with location without quotes (broader search)
            url = f"https://newsapi.org/v2/everything?q={location}&sortBy=publishedAt&language=en&apiKey={api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"Broader location news API error: {response.status_code}")
                return get_default_news()
                
            data = response.json()
            print(f"Total results for broader location search: {data.get('totalResults', 0)}")
            
            # If still no articles, try with top headlines
            if data.get('totalResults', 0) == 0:
                print("No location-specific news found, trying top headlines")
                url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
                response = requests.get(url, timeout=10)
                
                if response.status_code != 200:
                    print(f"Top headlines API error: {response.status_code}")
                    return get_default_news()
                    
                data = response.json()
                print(f"Total results for top headlines: {data.get('totalResults', 0)}")
        
        articles = []
        for article in data.get('articles', [])[:5]:  # Get top 5 headlines
            # Skip articles without required fields
            if not article.get('title') or not article.get('source', {}).get('name'):
                continue
                
            # Ensure URL is present
            if not article.get('url'):
                continue
                
            # Clean up description
            description = article.get('description', '')
            if description:
                # Limit description length
                description = description[:150] + '...' if len(description) > 150 else description
            
            articles.append({
                'title': article['title'],
                'source': article['source']['name'],
                'url': article['url'],
                'publishedAt': article.get('publishedAt', ''),
                'description': description
            })
        
        # If we still have no articles, return default news
        if not articles:
            print("No valid articles found in API response")
            return get_default_news()
            
        return articles
    except Exception as e:
        print(f"News API error: {e}")
        return get_default_news()

def get_default_news():
    """Return default news when API fails"""
    return [
        {
            'title': 'Unable to fetch news for your location',
            'source': 'System Message',
            'url': 'https://newsapi.org',
            'publishedAt': datetime.datetime.now().strftime('%Y-%m-%d'),
            'description': 'We could not retrieve location-specific news at this time. Please try updating your location or check back later.'
        },
        {
            'title': 'How to get the most from your smart mirror',
            'source': 'User Guide',
            'url': 'https://example.com/smart-mirror-guide',
            'publishedAt': datetime.datetime.now().strftime('%Y-%m-%d'),
            'description': 'Explore all the features of your virtual smart mirror including weather forecasts, calendar integration, and personalized settings.'
        }
    ]

def get_datetime():
    now = datetime.datetime.now()
    return {
        'date': now.strftime('%A, %B %d, %Y'),
        'time': now.strftime('%H:%M')
    }

def get_quote():
    """Get a random quote from MongoDB"""
    try:
        # Get quotes from MongoDB
        db = get_mongodb_db()
        quotes = list(db.app_quote.find())
        
        # If no quotes found, add default quotes
        if not quotes:
            default_quotes = [
                {"text": "Be yourself; everyone else is already taken.", "author": "Oscar Wilde"},
                {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
                {"text": "Life is what happens when you're busy making other plans.", "author": "John Lennon"},
                {"text": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt"},
                {"text": "Stay hungry, stay foolish.", "author": "Stewart Brand"}
            ]
            
            # Insert default quotes into MongoDB
            db.app_quote.insert_many(default_quotes)
            quotes = default_quotes
        
        # Select a random quote
        quote = random.choice(quotes)
        
        # Convert MongoDB _id to string if it exists
        if '_id' in quote:
            quote['_id'] = str(quote['_id'])
            
        return quote
    except Exception as e:
        print(f"Error getting quote from MongoDB: {e}")
        # Fallback to hardcoded quote if MongoDB fails
        return {
            "text": "The best way to predict the future is to invent it.",
            "author": "Alan Kay"
        }

def get_calendar_events():
    """Get calendar events from MongoDB"""
    try:
        # Get today's date
        today = datetime.date.today()
        next_month = today + timedelta(days=30)
        
        # Get events from MongoDB
        all_events = get_calendar_events_from_mongodb()
        
        # Format events for display
        events = []
        for event in all_events:
            # Parse dates from ISO format strings
            start_date = datetime.datetime.fromisoformat(event['start_date']).date()
            
            # Skip events that are too old or too far in the future
            if start_date < today - timedelta(days=1) or start_date > next_month:
                continue
                
            # Format date string
            if start_date == today:
                date_str = "Today"
            elif start_date == today + timedelta(days=1):
                date_str = "Tomorrow"
            else:
                date_str = start_date.strftime('%B %d')
            
            # Format time string
            time_str = None
            if not event.get('all_day', False) and 'start_time' in event and event['start_time']:
                try:
                    start_time = datetime.datetime.fromisoformat(event['start_time']).time()
                    time_str = start_time.strftime('%I:%M %p')
                except (ValueError, TypeError):
                    time_str = None
            
            # Calculate days until
            days_until = (start_date - today).days
            
            # Check if event is in the past
            is_past = start_date < today
            
            event_dict = {
                'id': event['_id'],
                'title': event['title'],
                'date': date_str,
                'time': time_str if not event.get('all_day', False) else "All day",
                'description': event.get('description', ''),
                'is_today': start_date == today,
                'is_past': is_past,
                'location': event.get('location', ''),
                'priority': event.get('priority', 'medium'),
                'reminder': event.get('reminder', False),
                'days_until': days_until,
                'all_day': event.get('all_day', False),
                'sort_date': start_date,  # For sorting
            }
            events.append(event_dict)
        
        # Sort events by date and time
        events.sort(key=lambda x: (x.get('sort_date'), 
                                  x.get('time', '23:59') if not x.get('all_day', False) else '00:00'))
        
        return {'events': events}
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        return {'events': []}

def get_calendar_events_by_priority(priority):
    """Get calendar events filtered by priority"""
    try:
        # Get events from database
        today = datetime.date.today()
        next_month = today + timedelta(days=30)
        
        # Get upcoming events from our database with specified priority
        db_events = CalendarEvent.objects.filter(
            start_date__gte=today - timedelta(days=1),
            start_date__lte=next_month,
            priority=priority
        ).order_by('start_date', 'start_time')
        
        # Format events for display
        events = []
        for event in db_events:
            event_dict = {
                'id': event.id,
                'title': event.title,
                'date': format_event_date(event),
                'time': format_event_time(event),
                'description': event.description,
                'is_today': event.is_today,
                'is_past': event.is_past,
                'location': event.location,
                'priority': event.priority,
                'reminder': event.reminder,
                'days_until': event.days_until,
                'all_day': event.all_day,
            }
            events.append(event_dict)
        
        return {'events': events}
    except Exception as e:
        print(f"Error fetching calendar events by priority: {e}")
        return {'events': []}

def format_event_date(event):
    """Format the event date for display"""
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    
    if event.start_date == today:
        return "Today"
    elif event.start_date == tomorrow:
        return "Tomorrow"
    else:
        return event.start_date.strftime('%A, %B %d')  # e.g. "Monday, January 1"

def format_event_time(event):
    """Format the event time for display"""
    if event.all_day:
        return "All day"
    elif event.start_time:
        time_str = event.start_time.strftime('%I:%M %p')  # e.g. "09:30 AM"
        if event.end_time:
            time_str += f" - {event.end_time.strftime('%I:%M %p')}"
        return time_str
    return None

def get_google_calendar_events():
    """Get events from Google Calendar API"""
    try:
        # Path to your service account credentials JSON file
        SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.json')
        
        # Check if credentials file exists
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            return []
            
        # Set up credentials
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            
        # Build the service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Get calendar ID from environment or use primary
        calendar_id = os.environ.get('GOOGLE_CALENDAR_ID', 'primary')
        
        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        google_events = events_result.get('items', [])
        
        # Format events for display
        formatted_events = []
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        
        for event in google_events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            # Parse the date/time
            if 'T' in start:  # This is a dateTime
                start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                event_date = start_dt.date()
                event_time = start_dt.time()
                all_day = False
            else:  # This is a date (all-day event)
                event_date = datetime.date.fromisoformat(start)
                event_time = None
                all_day = True
            
            # Format date string
            if event_date == today:
                date_str = "Today"
            elif event_date == tomorrow:
                date_str = "Tomorrow"
            else:
                date_str = event_date.strftime('%B %d')
            
            # Format time string
            if all_day:
                time_str = "All day"
            elif event_time:
                time_str = event_time.strftime('%I:%M %p')
            else:
                time_str = None
            
            formatted_events.append({
                'title': event.get('summary', 'Untitled Event'),
                'date': date_str,
                'time': time_str,
                'description': event.get('description', ''),
                'is_today': event_date == today,
                'sort_date': event_date,  # For sorting
            })
        
        return formatted_events
    except Exception as e:
        print(f"Error fetching Google Calendar events: {e}")
    return {'events': events}

# Add these new views for event management
def get_event(request, event_id):
    """API endpoint to get event details"""
    try:
        event = get_calendar_event_by_id(event_id)
        if not event:
            return JsonResponse({'error': 'Event not found'}, status=404)
            
        return JsonResponse({
            'id': event['_id'],
            'title': event['title'],
            'description': event.get('description', ''),
            'start_date': event['start_date'],
            'start_time': event.get('start_time', None),
            'end_date': event.get('end_date', None),
            'end_time': event.get('end_time', None),
            'all_day': event.get('all_day', False),
            'location': event.get('location', ''),
            'priority': event.get('priority', 'medium'),
            'reminder': event.get('reminder', False),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_POST
def save_event(request):
    """Save a new event or update an existing one"""
    try:
        event_id = request.POST.get('event_id', '')
        redirect_to = request.POST.get('redirect_to', 'index')
        
        # Debug output
        print(f"Saving event with ID: '{event_id}' (empty string means new event)")
        print(f"Form data: {request.POST}")
        
        # Collect event data from form
        event_data = {
            'title': request.POST.get('title'),
            'description': request.POST.get('description', ''),
            'start_date': request.POST.get('start_date'),
            'all_day': 'all_day' in request.POST,
            'location': request.POST.get('location', ''),
            'priority': request.POST.get('priority', 'medium'),
            'reminder': 'reminder' in request.POST,
        }
        
        # Handle time fields if not all-day event
        if not event_data['all_day']:
            event_data['start_time'] = request.POST.get('start_time') or None
            event_data['end_date'] = request.POST.get('end_date') or None
            event_data['end_time'] = request.POST.get('end_time') or None
        else:
            event_data['start_time'] = None
            event_data['end_time'] = None
        
        # Print event data for debugging
        print(f"Event data to save: {event_data}")
        
        if event_id and event_id.strip():  # Check if event_id is not empty
            # Validate ObjectId format
            if not ObjectId.is_valid(event_id):
                error_msg = f'Invalid event ID format: {event_id}'
                print(error_msg)
                messages.error(request, error_msg)
                return redirect(redirect_to)
                
            # Update existing event
            success = update_calendar_event_in_mongodb(event_id, event_data)
            print(f"Update result: {success}")
            if success:
                messages.success(request, 'Event updated successfully')
            else:
                messages.error(request, 'Failed to update event')
        else:
            # Create new event
            new_id = save_calendar_event_to_mongodb(event_data)
            print(f"New event ID: {new_id}")
            if new_id:
                messages.success(request, 'Event added successfully')
            else:
                messages.error(request, 'Failed to add event')
    except Exception as e:
        error_msg = f'Error saving event: {str(e)}'
        print(error_msg)
        messages.error(request, error_msg)
    
    # Redirect to the appropriate page
    if redirect_to == 'calendar':
        return redirect('/calendar-events/')
    return redirect('/')

@require_POST
def delete_event(request, event_id):
    """Delete an event"""
    try:
        success = delete_calendar_event_from_mongodb(event_id)
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Event not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def update_location(request):
    """Update the user's preferred location"""
    location = request.POST.get('location')
    if location:
        # Verify the location is valid by checking with the weather API
        api_key = os.environ.get('OPENWEATHER_API_KEY')
        url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        
        try:
            response = requests.get(url, timeout=10)
            
            # Debug output
            print(f"Location update API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Location update API response: {data.keys()}")
                
                if 'coord' in data:
                    # Location is valid, update preferences in MongoDB
                    db = get_mongodb_db()
                    result = db.app_userpreference.update_one(
                        {}, 
                        {'$set': {'location': location}},
                        upsert=True
                    )
                    
                    if result.acknowledged:
                        print(f"Successfully updated location to {location} in MongoDB")
                        messages.success(request, f'Location updated to {location}')
                    else:
                        print(f"Failed to update location in MongoDB")
                        messages.error(request, f'Failed to save location preference')
                else:
                    # Response is OK but missing expected data
                    print(f"Missing 'coord' in location API response: {data}")
                    messages.error(request, f'Invalid location data received for "{location}"')
            else:
                # Location not found or invalid response
                try:
                    data = response.json()
                    error_msg = data.get('message', 'Unknown error')
                except:
                    error_msg = f"HTTP {response.status_code}"
                
                print(f"Location update error: {error_msg}")
                messages.error(request, f'Location "{location}" not found. Error: {error_msg}')
        except requests.exceptions.Timeout:
            print(f"Timeout error when updating location to {location}")
            messages.error(request, f'Request timed out when checking location "{location}"')
        except requests.exceptions.RequestException as e:
            print(f"Request error when updating location to {location}: {e}")
            messages.error(request, f'Network error when checking location "{location}"')
        except Exception as e:
            print(f"Error updating location to {location}: {e}")
            messages.error(request, f'Error updating location: {str(e)}')
    else:
        messages.error(request, 'Please enter a valid location')
        
    return redirect('index')

def get_location_by_coords(request):
    """Get location name from coordinates using reverse geocoding"""
    try:
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')
        
        if not lat or not lon:
            return JsonResponse({'error': 'Missing coordinates'}, status=400)
            
        api_key = os.environ.get('OPENWEATHER_API_KEY')
        
        # Debug output
        print(f"Reverse geocoding for coordinates: {lat}, {lon}")
        
        # Use OpenWeatherMap's reverse geocoding API
        url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={api_key}"
        response = requests.get(url, timeout=10)
        
        # Debug output
        print(f"Reverse geocoding API response status: {response.status_code}")
        
        # Check if the response is successful
        if response.status_code != 200:
            print(f"Reverse geocoding API error: {response.status_code}")
            print(f"Response content: {response.text}")
            return JsonResponse({
                'error': f'API returned status code {response.status_code}'
            }, status=500)
            
        data = response.json()
        print(f"Reverse geocoding API response: {data}")
        
        # Check if data is valid and contains location information
        if not data or len(data) == 0:
            print("Empty response from reverse geocoding API")
            return JsonResponse({'error': 'Location not found'}, status=404)
            
        location = data[0].get('name')
        if not location:
            print(f"No location name in reverse geocoding response: {data}")
            # Try to use the state or country name if city name is not available
            location = data[0].get('state', data[0].get('country', 'Unknown location'))
            
        print(f"Location found: {location}")
        return JsonResponse({'location': location})
    except Exception as e:
        print(f"Error in reverse geocoding: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def get_quotes_from_mongodb():
    """Get quotes from MongoDB"""
    db = get_mongodb_db()
    quotes = list(db.app_quote.find())
    # Convert ObjectId to string for JSON serialization
    for quote in quotes:
        quote['_id'] = str(quote['_id'])
    return quotes

def save_quote_to_mongodb(text, author):
    """Save a quote to MongoDB"""
    db = get_mongodb_db()
    result = db.app_quote.insert_one({
        'text': text,
        'author': author
    })
    return str(result.inserted_id)

def get_user_preferences_from_mongodb():
    """Get user preferences from MongoDB"""
    db = get_mongodb_db()
    preferences = list(db.app_userpreference.find())
    # Return the first one or a default if none exists
    if preferences:
        pref = preferences[0]
        pref['_id'] = str(pref['_id'])
        return pref
    return {'location': 'New York', 'news_category': 'general'}

def save_user_preferences_to_mongodb(location, news_category):
    """Save user preferences to MongoDB"""
    db = get_mongodb_db()
    # Update the first one or insert if none exists
    result = db.app_userpreference.update_one(
        {}, 
        {'$set': {'location': location, 'news_category': news_category}},
        upsert=True
    )
    return result.acknowledged
