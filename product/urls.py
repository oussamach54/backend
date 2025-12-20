from django.urls import path
from product import views
from .views import (
    OrdersCreateView,
    MyOrdersListView,
    OrderDetailView,
    OrderStatusAdminView,
    AdminOrdersListView,
    AdminOrderDetailView,
)

urlpatterns = [
    path("products/", views.ProductsList.as_view(), name="products-list"),
    path("product/<int:pk>/", views.ProductDetailView.as_view(), name="product-details"),

    path("product-create/", views.ProductCreateView.as_view(), name="product-create"),
    path("products/create/", views.ProductCreateView.as_view(), name="product-create-alt"),
    path("product-update/<int:pk>/", views.ProductEditView.as_view(), name="product-update"),
    path("product-delete/<int:pk>/", views.ProductDeleteView.as_view(), name="product-delete"),

    path("wishlist/", views.WishlistListCreateView.as_view(), name="wishlist-list-create"),
    path("wishlist/toggle/", views.WishlistToggleView.as_view(), name="wishlist-toggle"),
    path("wishlist/<int:pk>/", views.WishlistDeleteView.as_view(), name="wishlist-delete"),

    path("shipping-rates/", views.ShippingRatesPublicList.as_view(), name="shipping-rates-public"),
    path("admin/shipping-rates/", views.ShippingRatesAdminListCreate.as_view(), name="shipping-rates-admin"),
    path("admin/shipping-rates/<int:pk>/", views.ShippingRateAdminDetail.as_view(), name="shipping-rate-admin-detail"),

    path("brands/", views.BrandsListView.as_view(), name="brands-list"),

    # ORDERS
    path("orders/", OrdersCreateView.as_view(), name="orders-create"),
    path("orders/my/", MyOrdersListView.as_view(), name="orders-my"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="orders-detail"),
    path("orders/<int:pk>/status/", OrderStatusAdminView.as_view(), name="orders-status"),
    path("orders/admin/", AdminOrdersListView.as_view(), name="orders-admin-list"),
    path("orders/admin/<int:pk>/", AdminOrderDetailView.as_view(), name="orders-admin-detail"),

    # ✅ PUBLIC guest order
    path("orders/public/<int:pk>/<str:token>/", views.PublicOrderDetailView.as_view(), name="orders-public"),
]
