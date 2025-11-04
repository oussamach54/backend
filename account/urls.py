# account/urls.py
from django.urls import path
from .views import (
    UserRegisterView,
    MyTokenObtainPairView,
    GoogleLoginView,
    CardsListView,
    UserAccountDetailsView,
    UserAccountUpdateView,
    UserAccountDeleteView,
    UserAddressesListView,
    CreateUserAddressView,
    UserAddressDetailsView,
    UpdateUserAddressView,
    DeleteUserAddressView,
    OrdersListView,
    ChangeOrderStatus,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    CreateCODOrderView,
)

urlpatterns = [
    # --- Optional alias (not required by your frontend, but harmless) ---
    path("login/", MyTokenObtainPairView.as_view(), name="account_login"),

    # --- Registration / Google ---
    path("register/", UserRegisterView.as_view(), name="register"),
    path("google-login/", GoogleLoginView.as_view(), name="google_login"),

    # --- Users (these match your frontend calls) ---
    path("user/<int:pk>/", UserAccountDetailsView.as_view(), name="user_details"),
    path("user_update/<int:pk>/", UserAccountUpdateView.as_view(), name="user_update"),
    path("user_delete/<int:pk>/", UserAccountDeleteView.as_view(), name="user_delete"),

    # --- Addresses (match your frontend) ---
    path("all-address-details/", UserAddressesListView.as_view(), name="addr_list"),
    path("create-address/", CreateUserAddressView.as_view(), name="addr_create"),
    path("address-details/<int:pk>/", UserAddressDetailsView.as_view(), name="addr_detail"),
    path("update-address/<int:pk>/", UpdateUserAddressView.as_view(), name="addr_update"),
    path("delete-address/<int:pk>/", DeleteUserAddressView.as_view(), name="addr_delete"),

    # --- Orders (match your frontend) ---
    path("all-orders-list/", OrdersListView.as_view(), name="orders_list"),
    path("orders/<int:pk>/status/", ChangeOrderStatus.as_view(), name="order_change_status"),
    path("orders/cod/", CreateCODOrderView.as_view(), name="create_cod_order"),

    # --- Password reset (match your frontend) ---
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]
