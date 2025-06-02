from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('calendar-events/', views.calendar_view, name='calendar'),
    # Put the save path BEFORE the event ID path to prevent conflicts
    path('event/save/', views.save_event, name='save_event'),
    path('event/<str:event_id>/', views.get_event, name='get_event'),
    path('event/<str:event_id>/delete/', views.delete_event, name='delete_event'),
    path('update-location/', views.update_location, name='update_location'),
    path('get-location-by-coords/', views.get_location_by_coords, name='get_location_by_coords'),
]


