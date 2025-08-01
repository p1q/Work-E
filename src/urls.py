from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from src.views import api_root

from users.interfaces.views_auth import (CustomTokenObtainPairView, CustomTokenRefreshView)

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),

    path('api/users/', include('users.interfaces.urls')),
    path('api/cvs/', include('cvs.interfaces.urls')),
    path('api/language/', include('language.interfaces.urls')),
    path('api/chatgpt/', include('chatgpt.interfaces.urls')),
    path('api/vacancies/', include('vacancy.interfaces.urls')),
    path('api/matching/', include('matching.interfaces.urls')),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('api-auth/', include('rest_framework.urls')),

    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/openapi/', include('openapi.urls')),
]
