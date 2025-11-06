# my_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from my_project.health import health

# SimpleJWT (refresh/verify)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Products under /api/
    path("api/", include("product.urls")),

    # Expose ACCOUNT under both /account/ and /api/account/
    path("account/", include("account.urls")),
    path("api/account/", include("account.urls")),

    # Expose PAYMENTS under both /payments/ and /api/payments/
    path("payments/", include("payments.urls")),
    path("api/payments/", include("payments.urls")),

    # Newsletter under /api/
    path("api/newsletter/", include("newsletter.urls")),

    # Health
    path("health/", health),

    # SimpleJWT refresh/verify (obtain handled by account/login/)
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    # optional short aliases
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh_short"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify_short"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
