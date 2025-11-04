# account/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
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
    # ------------------------------------------------------
    # JWT (add both canonical & aliases the frontend expects)
    # ------------------------------------------------------
    path("api/token/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("account/login/", MyTokenObtainPairView.as_view(), name="account_login"),

    # ----------------
    # Registration
    # ----------------
    path("register/", UserRegisterView.as_view(), name="register"),
    path("account/register/", UserRegisterView.as_view(), name="account-register"),

    path("google-login/", GoogleLoginView.as_view(), name="google_login"),
    path("account/google-login/", GoogleLoginView.as_view(), name="account_google_login"),

    # --------------
    # Cards (me)
    # --------------
    path("cards/", CardsListView.as_view(), name="cards"),

    # ----------------------------
    # Users (keep your originals)
    # ----------------------------
    path("users/<int:pk>/", UserAccountDetailsView.as_view(), name="user_details"),
    path("users/<int:pk>/update/", UserAccountUpdateView.as_view(), name="user_update"),
    path("users/<int:pk>/delete/", UserAccountDeleteView.as_view(), name="user_delete"),

    # ---- Aliases used by the old frontend code ----
    path("account/user/<int:pk>", UserAccountDetailsView.as_view(), name="user_details_alias"),
    path("account/user_update/<int:pk>/", UserAccountUpdateView.as_view(), name="user_update_alias"),
    path("account/user_delete/<int:pk>/", UserAccountDeleteView.as_view(), name="user_delete_alias"),

    # ----------------
    # Addresses (me)
    # ----------------
    path("addresses/", UserAddressesListView.as_view(), name="addresses_list"),
    path("addresses/create/", CreateUserAddressView.as_view(), name="address_create"),
    path("addresses/<int:pk>/", UserAddressDetailsView.as_view(), name="address_details"),
    path("addresses/<int:pk>/update/", UpdateUserAddressView.as_view(), name="address_update"),
    path("addresses/<int:pk>/delete/", DeleteUserAddressView.as_view(), name="address_delete"),

    # ---- Aliases the frontend calls ----
    path("account/all-address-details/", UserAddressesListView.as_view(), name="addr_list_alias"),
    path("account/create-address/", CreateUserAddressView.as_view(), name="addr_create_alias"),
    path("account/address-details/<int:pk>/", UserAddressDetailsView.as_view(), name="addr_detail_alias"),
    path("account/update-address/<int:pk>/", UpdateUserAddressView.as_view(), name="addr_update_alias"),
    path("account/delete-address/<int:pk>/", DeleteUserAddressView.as_view(), name="addr_delete_alias"),

    # --------------
    # Orders
    # --------------
    path("orders/", OrdersListView.as_view(), name="orders_list"),
    path("orders/<int:pk>/status/", ChangeOrderStatus.as_view(), name="order_change_status"),
    path("orders/cod/", CreateCODOrderView.as_view(), name="create_cod_order"),

    # ---- Alias the frontend calls ----
    path("account/all-orders-list/", OrdersListView.as_view(), name="orders_list_alias"),

    # ---------------------
    # Password reset (keep)
    # ---------------------
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("account/password-reset/", PasswordResetRequestView.as_view(), name="password_reset_alias"),
    path("account/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm_alias"),
]
