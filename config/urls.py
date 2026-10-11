"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve
from django.contrib.auth import views as auth_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),
    
    # Authentication (login, logout, etc.)
    #path('accounts/login/', auth_views.LoginView.as_view(template_name='admin/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # API v1
    path('api/v1/', include('api.v1.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('drafts/', include('apps.gemini_drafts.urls')),
    
    # Documentation OpenAPI/Swagger
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # REST Framework auth
    path('api-auth/', include('rest_framework.urls')),
    
    # Web templates - React Frontend (must come after specific paths)
    path('', include('web.urls')),
]

# Les fichiers statiques sont servis par WhiteNoise (WhiteNoiseMiddleware).
# Les médias (uploads) sont servis par Django via une route explicite, y compris
# lorsque DEBUG=False — en production, préférer un stockage objet ou un proxy.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
