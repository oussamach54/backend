# my_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from my_project.health import health
from account.views import MyTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- Auth (SimpleJWT) ---
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # --- Apps (mounted under /api/ so frontend calls /api/...) ---
    path('api/', include('product.urls')),          # /api/products/...
    path('api/payments/', include('payments.urls')),# /api/payments/...
    path('api/account/', include('account.urls')),  # /api/account/...

    # Newsletter as you had it
    path('api/newsletter/', include('newsletter.urls')),

    # Health
    path('health/', health),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
