# my_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from my_project.health import health

# ✅ import the JWT views
from account.views import MyTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),

    # ✅ Make /api/token/ and /api/token/refresh/ unambiguous
    path("api/token/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # APIs
    path("api/payments/", include("payments.urls")),
    path("payments/", include("payments.urls")),
    path("", include("account.urls")),
    path("account/", include("account.urls")),
    path("api/", include("product.urls")),
    path("api/newsletter/", include("newsletter.urls")),

    # health
    path("health/", health),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
