# my_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from my_project.health import health

urlpatterns = [
    path("admin/", admin.site.urls),

    # Product API (unchanged)
    path("api/", include("product.urls")),

    # ✅ Payments under /api/payments/... (what the frontend expects)
    path("api/payments/", include("payments.urls")),
    # (optional backward-compat so /payments/... continues to work)
    path("payments/", include("payments.urls")),

    # ✅ Expose account routes at BOTH /account/... and root
    # This makes /account/login/ work AND also /api/token/ etc. from account/urls.py.
    path("", include("account.urls")),
    path("account/", include("account.urls")),

    # Newsletter (unchanged)
    path("api/newsletter/", include("newsletter.urls")),

    # Health (unchanged)
    path("health/", health),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
