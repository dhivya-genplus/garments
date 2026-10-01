from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # API v1 Endpoints
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/administration/', include('apps.authentication.urls')),
    path('api/v1/masters/', include('apps.masters.urls')),
]
