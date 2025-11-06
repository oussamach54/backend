from django.urls import path
from . import views

urlpatterns = [
    # payments
    path("create/", views.CreatePayment.as_view(), name="payments-create"),
    path("order/<int:pk>/status/", views.OrderStatus.as_view(), name="payments-order-status"),
    path("cmi/ok/<int:pk>/", views.CmiOk.as_view(), name="payments-cmi-ok"),
    path("cmi/fail/<int:pk>/", views.CmiFail.as_view(), name="payments-cmi-fail"),
    path("health/", views.Health.as_view(), name="payments-health"),

    # NEW: token check used by frontend
    path("check-token/", views.CheckToken.as_view(), name="payments-check-token"),

    # shipping rates
    path("shipping-rates/", views.ShippingRateListCreate.as_view(), name="shipping-rates"),
    path("admin/shipping-rates/<int:pk>/", views.ShippingRateAdminUpdateDelete.as_view(),
         name="shipping-rate-admin"),
]
