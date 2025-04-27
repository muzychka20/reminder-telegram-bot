
from rest_framework.permissions import AllowAny
from django.urls import path, include, re_path
from drf_yasg.views import get_schema_view
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from drf_yasg import openapi


# Create schema view for Swagger documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Reminders API",
        default_version='v1',
        description="API for managing articles and categories with image upload functionality",
        terms_of_service="https://www.yourapp.com/terms/",
        contact=openapi.Contact(email="contact@yourapp.com"),
        license=openapi.License(name="Your License"),
    ),
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),    
    path('api/', include('reminders.urls')),
    
    # Swagger documentation URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
