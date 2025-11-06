# account/urls.py
from django.urls import path
from .views import (
    UserRegisterView,
    MyTokenObtainPairView,   # custom login (kept)
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
    # auth
    path("register/", UserRegisterView.as_view(), name="register"),
    path("login/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),  # kept for compatibility
    path("google-login/", GoogleLoginView.as_view(), name="google_login"),

    # cards
    path("cards/", CardsListView.as_view(), name="cards"),

    # users
    path("users/<int:pk>/", UserAccountDetailsView.as_view(), name="user_details"),
    path("users/<int:pk>/update/", UserAccountUpdateView.as_view(), name="user_update"),
    path("users/<int:pk>/delete/", UserAccountDeleteView.as_view(), name="user_delete"),

    # addresses
    path("addresses/", UserAddressesListView.as_view(), name="addresses_list"),
    path("addresses/create/", CreateUserAddressView.as_view(), name="address_create"),
    path("addresses/<int:pk>/", UserAddressDetailsView.as_view(), name="address_details"),
    path("addresses/<int:pk>/update/", UpdateUserAddressView.as_view(), name="address_update"),
    path("addresses/<int:pk>/delete/", DeleteUserAddressView.as_view(), name="address_delete"),

    # orders
    path("orders/", OrdersListView.as_view(), name="orders_list"),
    path("orders/<int:pk>/status/", ChangeOrderStatus.as_view(), name="order_change_status"),
    path("orders/cod/", CreateCODOrderView.as_view(), name="create_cod_order"),

    # password reset
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
]
