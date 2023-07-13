from django.urls import path
from .views import RentalCalendarView, RentalDetailView, RentalDeleteView

urlpatterns = [
    path('calendar/', RentalCalendarView.as_view(), name='rental_calendar'),
    path('info/<int:pk>/', RentalDetailView.as_view(), name='rental_detail'),
    path('create/', RentalCalendarView.as_view(), name='rental_create'),
    path('delete/<int:pk>/', RentalDeleteView.as_view(), name='rental_delete')
]
