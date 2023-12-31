from django.urls import path
from .views import RentalCalendarView, RentalDetailView, RentalDeleteView, CarListView, CarDetailView, ClientListView, \
    ShiftCreateView, RentalListView, logout_view, get_build_objects, ClientDetailView

urlpatterns = [
    path('calendar/', RentalCalendarView.as_view(), name='rental_calendar'),
    path('info/<int:pk>/', RentalDetailView.as_view(), name='rental_detail'),
    path('rental/info/<int:pk>/add_shift/', ShiftCreateView.as_view(), name='add_shift'),
    path('create/', RentalCalendarView.as_view(), name='rental_create'),
    path('delete/<int:pk>/', RentalDeleteView.as_view(), name='rental_delete'),
    path('list/cars', CarListView.as_view(), name='car_list'),
    path('list/cars/<int:pk>/', CarDetailView.as_view(), name='car_detail'),
    path('list/clients', ClientListView.as_view(), name='client_list'),
    path('list/clients/<int:pk>/', ClientDetailView.as_view(), name='client_detail'),
    path('list/rentals', RentalListView.as_view(), name='rental_list'),
    path('logout/', logout_view, name='logout'),
]

