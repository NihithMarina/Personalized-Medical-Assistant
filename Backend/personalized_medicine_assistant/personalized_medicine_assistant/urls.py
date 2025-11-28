"""
URL configuration for personalized_medicine_assistant project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('patients/', include('patients.urls')),
    path('doctors/', include('doctors.urls')),
    path('predict/', include('ml_prediction.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Note: In DEBUG, django.contrib.staticfiles serves STATICFILES_DIRS automatically.
    # Avoid mapping STATIC_URL to STATIC_ROOT here to ensure assets load from /static/ without collectstatic.