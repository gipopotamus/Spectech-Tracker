"""
URL configuration for spectech project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from tracker.views import CustomLoginView

from tracker.views import get_build_objects

from tracker.views import special_equipment_info

urlpatterns = [
    path('admin/', admin.site.urls),
    path('rental/', include('tracker.urls')),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('', RedirectView.as_view(url='/rental/calendar/')),
    path('get_build_objects/', get_build_objects, name='get_build_objects'),
    path('rental_report/', special_equipment_info, name='special_equipment_info')
]

