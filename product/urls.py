from django.urls import path
from product import views
from .views import (
    OrdersCreateView, MyOrdersListView, OrderDetailView, OrderStatusAdminView,AdminOrdersListView,
    AdminOrderDetailView,

)


urlpatterns = [
    # list/detail
    path("products/", views.ProductsList.as_view(), name="products-list"),
    path("product/<int:pk>/", views.ProductDetailView.as_view(), name="product-details"),

    # create/update/delete
    path("product-create/", views.ProductCreateView.as_view(), name="product-create"),          # legacy
    path("products/create/", views.ProductCreateView.as_view(), name="product-create-alt"),     # ✅ new alias
    path("product-update/<int:pk>/", views.ProductEditView.as_view(), name="product-update"),
    path("product-delete/<int:pk>/", views.ProductDeleteView.as_view(), name="product-delete"),

    # wishlist
    path("wishlist/", views.WishlistListCreateView.as_view(), name="wishlist-list-create"),
    path("wishlist/toggle/", views.WishlistToggleView.as_view(), name="wishlist-toggle"),
    path("wishlist/<int:pk>/", views.WishlistDeleteView.as_view(), name="wishlist-delete"),

    # product shipping (public admin list in product app)
    path("shipping-rates/", views.ShippingRatesPublicList.as_view(), name="shipping-rates-public"),
    path("admin/shipping-rates/", views.ShippingRatesAdminListCreate.as_view(), name="shipping-rates-admin"),
    path("admin/shipping-rates/<int:pk>/", views.ShippingRateAdminDetail.as_view(), name="shipping-rate-admin-detail"),

    # brands
    path("brands/", views.BrandsListView.as_view(), name="brands-list"),

    path("orders/", OrdersCreateView.as_view(), name="orders-create"),              # POST create
    path("orders/my/", MyOrdersListView.as_view(), name="orders-my"),              # GET my orders
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="orders-detail"),     # GET detail (owner/admin)
    path("orders/<int:pk>/status/", OrderStatusAdminView.as_view(), name="orders-status"),  # PATCH status (admin)
    path("orders/admin/", AdminOrdersListView.as_view(), name="orders-admin-list"),          # GET all (admin)
    path("orders/admin/<int:pk>/", AdminOrderDetailView.as_view(), name="orders-admin-detail"),
    path("orders/public/<int:pk>/<str:token>/", views.PublicOrderDetailView.as_view()),
]
