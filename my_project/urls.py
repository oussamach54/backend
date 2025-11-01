# my_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from my_project.health import health  # <-- add this import

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('product.urls')),
    path('payments/', include('payments.urls')),
    path('account/', include('account.urls')),
    path('api/newsletter/', include('newsletter.urls')),
    path('health/', health),  # <-- add this line
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
