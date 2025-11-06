# my_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from my_project.health import health

# SimpleJWT
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- PRODUCTS stay under /api/ (as before) ---
    path("api/", include("product.urls")),

    # --- Expose ACCOUNT under both /account/ and /api/account/ ---
    path("account/", include("account.urls")),
    path("api/account/", include("account.urls")),

    # --- Expose PAYMENTS under both /payments/ and /api/payments/ ---
    path("payments/", include("payments.urls")),
    path("api/payments/", include("payments.urls")),

    # Newsletter (historically under /api/)
    path("api/newsletter/", include("newsletter.urls")),

    # Health
    path("health/", health),

    # --- SimpleJWT under both /api/token/* and /token/* ---
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair_short"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh_short"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify_short"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
