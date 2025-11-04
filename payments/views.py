from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from django.urls import reverse
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http
from rest_framework.permissions import IsAuthenticated

from .models import PaymentOrder, ShippingRate
from .serializers import ShippingRateSerializer


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _frontend_success_url(request, order_id: int) -> str:
    base = getattr(settings, "CMI_SUCCESS_URL", None)
    if base:
        sep = "&" if "?" in base else "?"
        return f"{base}{sep}order={order_id}"

    frontend = getattr(settings, "FRONTEND_BASE_URL", "")
    if frontend:
        return f"{frontend.rstrip('/')}/payment-status?order={order_id}"

    return f"/payment-status?order={order_id}"


def _frontend_fail_url(request, order_id: int) -> str:
    base = getattr(settings, "CMI_FAIL_URL", None)
    if base:
        sep = "&" if "?" in base else "?"
        return f"{base}{sep}order={order_id}"

    frontend = getattr(settings, "FRONTEND_BASE_URL", "")
    if frontend:
        return f"{frontend.rstrip('/')}/payment-status?order={order_id}&status=failed"

    return f"/payment-status?order={order_id}&status=failed"


class Health(APIView):
    def get(self, request):
        return Response({"ok": True, "now": timezone.now().isoformat()}, status=200)


class CreatePayment(APIView):
    """
    POST /api/payments/create/
    {
      "items":    [{ "price": 199.0, "qty": 1 }, ...],
      "shipping": { "price": 20 },
      "email":    "client@email.com",
      "method":   "card" | "cod"   (optional, default: "card")
    }

    - "card": simulate a bank page redirect to OK (replace later with real CMI HPP)
    - "cod" : returns frontend success URL immediately (order stays PENDING)
    """
    def post(self, request):
        data = request.data or {}
        items = data.get("items") or []
        shipping = data.get("shipping") or {}
        email = data.get("email") or ""
        method = (data.get("method") or "card").lower()

        if not items:
            return Response({"detail": "Aucun article."}, status=http.HTTP_400_BAD_REQUEST)

        try:
            total_items = sum(float(i.get("price", 0)) * int(i.get("qty", 1)) for i in items)
            shipping_price = float(shipping.get("price", 0))
            amount = round(total_items + shipping_price, 2)
        except Exception:
            return Response({"detail": "Payload invalide."}, status=http.HTTP_400_BAD_REQUEST)

        order = PaymentOrder.objects.create(
            amount=amount,
            currency="MAD",
            email=email,
            status=PaymentOrder.Status.PENDING,
            payload={"items": items, "shipping": shipping, "method": method},
            customer_ip=_client_ip(request),
        )

        ok_url_internal = request.build_absolute_uri(
            reverse("payments-cmi-ok", kwargs={"pk": order.id})
        )
        # fail_url_internal = request.build_absolute_uri(
        #     reverse("payments-cmi-fail", kwargs={"pk": order.id})
        # )

        if method == "cod":
            return Response(
                {"order_id": order.id, "payment_url": _frontend_success_url(request, order.id)},
                status=http.HTTP_201_CREATED,
            )

        # For now, simulate a successful bank page
        payment_url = ok_url_internal
        return Response({"order_id": order.id, "payment_url": payment_url}, status=http.HTTP_201_CREATED)


class OrderStatus(APIView):
    def get(self, request, pk):
        try:
            order = PaymentOrder.objects.get(pk=pk)
        except PaymentOrder.DoesNotExist:
            return Response({"status": "unknown"}, status=http.HTTP_404_NOT_FOUND)
        return Response(
            {"status": order.status, "amount": str(order.amount), "currency": order.currency},
            status=200,
        )


class CmiOk(APIView):
    def get(self, request, pk):
        try:
            order = PaymentOrder.objects.get(pk=pk)
        except PaymentOrder.DoesNotExist:
            return redirect(_frontend_success_url(request, pk))
        if order.status == PaymentOrder.Status.PENDING:
            order.status = PaymentOrder.Status.PAID
            order.save(update_fields=["status", "updated_at"])
        return redirect(_frontend_success_url(request, order.id))


class CmiFail(APIView):
    def get(self, request, pk):
        try:
            order = PaymentOrder.objects.get(pk=pk)
        except PaymentOrder.DoesNotExist:
            return redirect(_frontend_fail_url(request, pk))
        if order.status == PaymentOrder.Status.PENDING:
            order.status = PaymentOrder.Status.FAILED
            order.save(update_fields=["status", "updated_at"])
        return redirect(_frontend_fail_url(request, order.id))


class ShippingRateListCreate(APIView):
    """
    GET  /api/shipping-rates/   -> list active rates (public)
    POST /api/shipping-rates/   -> create (admin only)
    """
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get(self, request):
        qs = ShippingRate.objects.filter(active=True).order_by("city")
        return Response(ShippingRateSerializer(qs, many=True).data, status=200)

    def post(self, request):
        data = request.data.copy()
        try:
            data["price"] = float(data.get("price", 0))
        except Exception:
            return Response({"detail": "price must be numeric"}, status=400)

        ser = ShippingRateSerializer(data=data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=201)
        return Response(ser.errors, status=400)


class ShippingRateAdminUpdateDelete(APIView):
    """Optional admin endpoints to edit/delete a rate."""
    permission_classes = [permissions.IsAdminUser]

    def put(self, request, pk):
        try:
            obj = ShippingRate.objects.get(pk=pk)
        except ShippingRate.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        ser = ShippingRateSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=400)

    def delete(self, request, pk):
        try:
            obj = ShippingRate.objects.get(pk=pk)
        except ShippingRate.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        obj.delete()
        return Response(status=204)

class CheckToken(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"valid": True, "user": request.user.id}, status=200)