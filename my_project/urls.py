# my_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import TokenRefreshView
from account.views import MyTokenObtainPairView
from my_project.health import health

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # App routers (all under /api/)
    path('api/products/', include('product.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/account/', include('account.urls')),
    path('api/newsletter/', include('newsletter.urls')),

    # Health
    path('health/', health),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
