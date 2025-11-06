# account/views.py
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.conf import settings

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

# Google token verification
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist

# Models & Serializers
from .models import StripeModel, BillingAddress, OrderModel
from .serializers import (
    UserSerializer,
    CardsListSerializer,
    BillingAddressSerializer,
    AllOrdersListSerializer,
    OrderCODCreateSerializer,
)


# ============================================================
# Registration (no auto-login)
# ============================================================
class UserRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data or {}
        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip()
        password = data.get("password") or ""

        if not username or not email or not password:
            return Response(
                {"detail": "username, email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username__iexact=username).exists():
            return Response(
                {"detail": "A user with that username already exists!"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {"detail": "A user with that email address already exists!"},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
        )
        return Response(
            {"id": user.id, "username": user.username, "email": user.email},
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# JWT Login — accepts EMAIL or USERNAME + password
# ============================================================
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Accepts JSON body with either:
      { "email": "...", "password": "..." }
    or
      { "username": "...", "password": "..." }
    """
    def validate(self, attrs):
        ident = (self.initial_data.get("email") or self.initial_data.get("username") or "").strip()
        password = (self.initial_data.get("password") or "").strip()

        if not ident or not password:
            # Use the parent error to keep response format
            raise self.error_messages.get("no_active_account", Exception("No active account"))

        try:
            user = User.objects.get(Q(email__iexact=ident) | Q(username__iexact=ident))
            attrs["username"] = user.username
        except User.DoesNotExist:
            # Let SimpleJWT try (will 401)
            attrs["username"] = ident

        data = super().validate(attrs)
        data.update(
            {
                "id": self.user.id,
                "username": self.user.username,
                "email": self.user.email,
                "is_staff": self.user.is_staff,
            }
        )
        return data


class MyTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = MyTokenObtainPairSerializer


# ============================================================
# Google Login
# ============================================================
class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = (request.data or {}).get("id_token")
        if not token:
            return Response({"detail": "id_token required"}, status=400)

        try:
            idinfo = google_id_token.verify_oauth2_token(
                token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            )
            if idinfo.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
                return Response({"detail": "Wrong issuer"}, status=400)

            email = idinfo.get("email")
            name = idinfo.get("name") or (email.split("@")[0] if email else "")
            if not email:
                return Response({"detail": "No email in token"}, status=400)

            user, _created = User.objects.get_or_create(
                email__iexact=email,
                defaults={"username": name, "email": email},
            )

            refresh = RefreshToken.for_user(user)
            data = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
            }
            return Response(data, status=200)

        except ValueError:
            return Response({"detail": "Invalid Google token"}, status=400)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)


# ============================================================
# Cards for current user
# ============================================================
class CardsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cards = StripeModel.objects.filter(user=request.user)
        serializer = CardsListSerializer(cards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# User account details / update / delete
# ============================================================
class UserAccountDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        if request.user.id != pk and not request.user.is_staff:
            return Response({"details": "Permission Denied."}, status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, id=pk)
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserAccountUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        if request.user.id != pk:
            return Response({"details": "Permission Denied."}, status=status.HTTP_403_FORBIDDEN)

        user = get_object_or_404(User, id=pk)
        data = request.data or {}

        new_email = data.get("email", user.email)
        if new_email and new_email.lower() != (user.email or "").lower():
            if User.objects.filter(email__iexact=new_email).exclude(id=user.id).exists():
                return Response({"detail": "Email already in use"}, status=status.HTTP_400_BAD_REQUEST)

        user.username = data.get("username", user.username)
        user.email = new_email

        new_pw = data.get("password") or ""
        if new_pw:
            user.password = make_password(new_pw)

        user.save()
        serializer = UserSerializer(user, many=False)
        return Response(
            {"details": "User Successfully Updated.", "user": serializer.data},
            status=status.HTTP_200_OK,
        )


class UserAccountDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if request.user.id != pk:
            return Response({"details": "Permission Denied."}, status=status.HTTP_403_FORBIDDEN)

        user = get_object_or_404(User, id=pk)
        password = (request.data or {}).get("password") or ""
        if not check_password(password, user.password):
            return Response({"details": "Incorrect password."}, status=status.HTTP_401_UNAUTHORIZED)

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# Addresses (current user)
# ============================================================
class UserAddressesListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        addresses = BillingAddress.objects.filter(user=request.user)
        serializer = BillingAddressSerializer(addresses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateUserAddressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data or {}
        payload = {
            "name": data.get("name", ""),
            "user": request.user.id,
            "phone_number": data.get("phone_number", ""),
            "pin_code": data.get("pin_code", ""),
            "house_no": data.get("house_no", ""),
            "landmark": data.get("landmark", ""),
            "city": data.get("city", ""),
            "state": data.get("state", ""),
        }
        serializer = BillingAddressSerializer(data=payload)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserAddressDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        address = get_object_or_404(BillingAddress, id=pk, user=request.user)
        serializer = BillingAddressSerializer(address, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateUserAddressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        addr = get_object_or_404(BillingAddress, id=pk, user=request.user)
        data = request.data or {}
        payload = {
            "name": data.get("name", addr.name),
            "user": request.user.id,
            "phone_number": data.get("phone_number", addr.phone_number),
            "pin_code": data.get("pin_code", addr.pin_code),
            "house_no": data.get("house_no", addr.house_no),
            "landmark": data.get("landmark", addr.landmark),
            "city": data.get("city", addr.city),
            "state": data.get("state", addr.state),
        }
        serializer = BillingAddressSerializer(addr, data=payload)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteUserAddressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        addr = get_object_or_404(BillingAddress, id=pk, user=request.user)
        addr.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# Orders list & change status
# ============================================================
class OrdersListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            orders = OrderModel.objects.all().order_by("-created_at")
        else:
            orders = OrderModel.objects.filter(user=request.user).order_by("-created_at")
        serializer = AllOrdersListSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangeOrderStatus(APIView):
    permission_classes = [permissions.IsAdminUser]

    def put(self, request, pk):
        order = get_object_or_404(OrderModel, id=pk)
        data = request.data or {}

        if "status" in data:
            order.status = data.get("status")

        if "is_delivered" in data:
            order.is_delivered = bool(data.get("is_delivered"))

        if "delivered_at" in data:
            order.delivered_at = data.get("delivered_at")

        order.save()
        serializer = AllOrdersListSerializer(order, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# Password Reset (email with HTML fallback)
# ============================================================
class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = (request.data or {}).get("email", "").strip()
        # Always return 200 to avoid enumeration
        if not email:
            return Response({"detail": "Si un compte existe, un email a été envoyé."}, status=200)

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({"detail": "Si un compte existe, un email a été envoyé."}, status=200)

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}"

        subject = "Réinitialisation de votre mot de passe"
        text_body = (
            f"Bonjour {user.username or ''},\n\n"
            "Vous avez demandé à réinitialiser votre mot de passe.\n"
            f"Cliquez sur ce lien pour continuer : {reset_url}\n\n"
            "Si vous n’êtes pas à l’origine de cette demande, ignorez cet email."
        )

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )

        try:
            html_body = render_to_string("emails/password_reset.html", {"user": user, "reset_url": reset_url})
            msg.attach_alternative(html_body, "text/html")
        except TemplateDoesNotExist:
            pass

        try:
            msg.send(fail_silently=False)
        except Exception as e:
            print("Erreur d’envoi d’email:", e)

        return Response({"detail": "Si un compte existe, un email a été envoyé."}, status=200)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data or {}
        uidb64 = data.get("uid")
        token = data.get("token")
        new_pw = data.get("new_password") or data.get("password")

        if not (uidb64 and token and new_pw):
            return Response({"detail": "Paramètres manquants."}, status=400)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({"detail": "Lien invalide."}, status=400)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({"detail": "Lien expiré ou invalide."}, status=400)

        user.password = make_password(new_pw)
        user.save()
        return Response({"detail": "Mot de passe mis à jour avec succès."}, status=200)


# ============================================================
# Create COD order -> returns WhatsApp URL
# ============================================================
class CreateCODOrderView(APIView):
    """
    POST /account/orders/cod/
    Body:
    {
      "items": [{ "id":1, "name":"Crème X", "qty":2, "price":89.9 }],
      "total_price": 179.8,
      "customer_name": "Nom Prénom",
      "phone": "06XXXXXXXX",
      "address": "Adresse complète",
      "city": "Casablanca",
      "notes": "Optionnel"
    }
    """
    permission_classes = [permissions.IsAuthenticated]  # change to AllowAny to allow guest orders

    def post(self, request):
        serializer = OrderCODCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order = OrderModel.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=(request.user.username if request.user.is_authenticated else "client"),
            payment_method="COD",
            status="PENDING",
            whatsapp_to=getattr(settings, "WHATSAPP_ADMIN", ""),
            **serializer.validated_data,
        )
        data = AllOrdersListSerializer(order).data
        if hasattr(order, "build_whatsapp_url"):
            data["whatsapp_url"] = order.build_whatsapp_url()
        else:
            data["whatsapp_url"] = ""
        return Response(data, status=status.HTTP_201_CREATED)
