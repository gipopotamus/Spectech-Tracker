from django.urls import path
from .views import rental_calendar, RentalDetailView

urlpatterns = [
    path('calendar/', rental_calendar, name='rental_calendar'),
    path('info/<int:pk>/', RentalDetailView.as_view(), name='booking_delete'),
    path('create/', rental_calendar, name='create_rental'),
]

