from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(template_name='dashboard/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('api/users/', include('users.urls')),
    path('api/assets/', include('assets.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/maintenance/', include('maintenance.urls')),
    path('api/procurement/', include('procurement.urls')),
    path('api/simulation/', include('simulation.urls')),
    path('', include('dashboard.urls')),
]
