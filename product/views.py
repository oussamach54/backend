# backend/product/views.py
import json
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

import requests
from django.conf import settings


from .models import (
    Product,
    ProductVariant,
    WishlistItem,
    ShippingRate,
    Order,
    OrderItem,
)
from .serializers import (
    ProductSerializer,
    WishlistItemSerializer,
    ShippingRateSerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
)

# ---------------- helpers ----------------


def _to_dec(v):
    if v in (None, ""):
        return None
    s = str(v).strip().replace(",", ".")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError, TypeError):
        return None


def _to_list(v):
    """
    Accepts JSON string '["face","acne"]', CSV 'face,acne', or list.
    Returns a cleaned list of unique slugs (lowercase).
    """
    if v in (None, "", []):
        return []
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                v = parsed
            else:
                v = [x.strip() for x in v.split(",")]
        except Exception:
            v = [x.strip() for x in v.split(",")]
    if isinstance(v, (list, tuple)):
        out = []
        for x in v:
            s = (str(x or "")).strip().lower()
            if s and s not in out:
                out.append(s)
        return out
    return []


# ======================= PRODUCTS =======================


class ProductsList(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        qs = Product.objects.all().order_by("-id")

        # ... tes filtres existants (category, brand, search) ...

        # category filter
        slug = (
            request.query_params.get("type")
            or request.query_params.get("category")
            or ""
        ).lower().strip()
        if slug:
            qs = qs.filter(category=slug)

        brand = request.query_params.get("brand")
        if brand:
            qs = qs.filter(brand__iexact=brand)

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        # ⭐ NEW: ?favorite=1 pour ne prendre que les favoris
        fav = request.query_params.get("favorite")
        if fav is not None:
            s = str(fav).strip().lower()
            if s in ("1", "true", "yes", "on"):
                qs = qs.filter(is_favorite=True)

        data = ProductSerializer(qs, many=True, context={"request": request}).data
        return Response(data, status=200)



class ProductDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        data = ProductSerializer(product, context={"request": request}).data
        return Response(data, status=200)


class ProductCreateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @transaction.atomic
    def post(self, request):
        data = request.data

        # ✅ multi categories
        cats = _to_list(data.get("categories"))
        primary = (data.get("category") or (cats[0] if cats else "other")).lower()

        payload = {
            "name": data.get("name"),
            "brand": data.get("brand", ""),
            "description": data.get("description", ""),
            "price": _to_dec(data.get("price")),
            "new_price": _to_dec(data.get("new_price")),
            "stock": data.get("stock"),
            "image": request.FILES.get("image"),
            "category": primary,
            "categories": cats,
            "is_favorite": data.get("is_favorite", False),  # ⭐ AJOUT
        }

        ser = ProductSerializer(data=payload, context={"request": request})
        if not ser.is_valid():
            return Response({"detail": ser.errors}, status=400)

        product = ser.save()

        # Optional variants
        raw = data.get("variants")
        if raw:
            try:
                items = json.loads(raw) if isinstance(raw, str) else raw
                to_create = []
                for item in items or []:
                    label = (item.get("label") or "").strip()
                    price = _to_dec(item.get("price"))
                    if not label or price is None:
                        continue
                    to_create.append(
                        ProductVariant(
                            product=product,
                            label=label,
                            size_ml=(
                                item.get("size_ml")
                                if item.get("size_ml") not in ("", None)
                                else None
                            ),
                            price=price,
                            in_stock=bool(item.get("in_stock", True)),
                            sku=(item.get("sku") or "").strip(),
                        )
                    )
                if to_create:
                    ProductVariant.objects.bulk_create(to_create)
            except Exception:
                pass

        out = ProductSerializer(product, context={"request": request}).data
        return Response(out, status=201)


class ProductEditView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @transaction.atomic
    def put(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        data = request.data

        new_base = _to_dec(data.get("price"))
        new_promo = _to_dec(data.get("new_price"))

        # ✅ multi categories (keep old if none sent)
        cats = _to_list(data.get("categories"))
        if cats:
            primary = (data.get("category") or cats[0]).lower()
            categories_value = cats
        else:
            primary = (data.get("category") or product.category or "other").lower()
            categories_value = product.categories

        payload = {
            "name": data.get("name", product.name),
            "brand": data.get("brand", product.brand),
            "description": data.get("description", product.description),
            "price": new_base if new_base is not None else product.price,
            "new_price": new_promo,
            "stock": data.get("stock", product.stock),
            "category": primary,
            "categories": categories_value,
            "is_favorite": data.get("is_favorite", product.is_favorite),  # ⭐ AJOUT
        }

        image_file = request.FILES.get("image")
        if image_file is not None:
            payload["image"] = image_file

        ser = ProductSerializer(
            instance=product,
            data=payload,
            partial=True,
            context={"request": request},
        )
        if not ser.is_valid():
            return Response({"detail": ser.errors}, status=400)

        product = ser.save()

        if "variants" in data:
            ProductVariant.objects.filter(product=product).delete()
            raw = data.get("variants")
            try:
                items = json.loads(raw) if isinstance(raw, str) else raw
                to_create = []
                for item in items or []:
                    label = (item.get("label") or "").strip()
                    price = _to_dec(item.get("price"))
                    if not label or price is None:
                        continue
                    to_create.append(
                        ProductVariant(
                            product=product,
                            label=label,
                            size_ml=(
                                item.get("size_ml")
                                if item.get("size_ml") not in ("", None)
                                else None
                            ),
                            price=price,
                            in_stock=bool(item.get("in_stock", True)),
                            sku=(item.get("sku") or "").strip(),
                        )
                    )
                if to_create:
                    ProductVariant.objects.bulk_create(to_create)
            except Exception:
                pass

        out = ProductSerializer(product, context={"request": request}).data
        return Response(out, status=200)


class ProductDeleteView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        product.delete()
        return Response({"detail": "Product successfully deleted."}, status=204)


# ======================= WISHLIST / SHIPPING / BRANDS =======================


class WishlistListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = WishlistItem.objects.filter(user=request.user).select_related("product")
        ser = WishlistItemSerializer(qs, many=True, context={"request": request})
        return Response(ser.data, status=200)

    def post(self, request):
        payload = request.data.copy()
        payload["product_id"] = payload.get("product") or payload.get("product_id")
        payload["user"] = request.user.id
        serializer = WishlistItemSerializer(data=payload, context={"request": request})
        if serializer.is_valid():
            obj, created = WishlistItem.objects.get_or_create(
                user=request.user,
                product=serializer.validated_data["product"],
            )
            out = WishlistItemSerializer(obj, context={"request": request}).data
            return Response(out, status=201 if created else 200)
        return Response({"detail": serializer.errors}, status=400)


class WishlistDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        item = get_object_or_404(WishlistItem, id=pk, user=request.user)
        item.delete()
        return Response(status=204)


class WishlistToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        pid = request.data.get("product_id")
        if not pid:
            return Response({"detail": "product_id required"}, status=400)
        product = get_object_or_404(Product, id=pid)
        obj, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            obj.delete()
            state = "removed"
        else:
            state = "added"
        total = WishlistItem.objects.filter(user=request.user).count()
        return Response({"state": state, "total": total}, status=200)


class ShippingRatesPublicList(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        q = request.query_params.get("q")
        qs = ShippingRate.objects.filter(active=True)
        if q:
            qs = qs.filter(city__icontains=q)
        ser = ShippingRateSerializer(qs, many=True)
        return Response(ser.data, status=200)


class ShippingRatesAdminListCreate(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        q = request.query_params.get("q")
        qs = ShippingRate.objects.all()
        if q:
            qs = qs.filter(city__icontains=q)
        ser = ShippingRateSerializer(qs, many=True)
        return Response(ser.data, status=200)

    def post(self, request):
        ser = ShippingRateSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=201)
        return Response({"detail": ser.errors}, status=400)


class ShippingRateAdminDetail(APIView):
    permission_classes = [permissions.IsAdminUser]

    def put(self, request, pk):
        obj = get_object_or_404(ShippingRate, pk=pk)
        ser = ShippingRateSerializer(instance=obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=200)
        return Response({"detail": ser.errors}, status=400)

    def delete(self, request, pk):
        obj = get_object_or_404(ShippingRate, pk=pk)
        obj.delete()
        return Response(status=204)


class BrandsListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        brands = (
            Product.objects.exclude(brand="")
            .values_list("brand", flat=True)
            .distinct()
        )
        sorted_brands = sorted(brands, key=lambda s: s.casefold())
        return Response(sorted_brands, status=200)


# ======================= ORDERS =======================


class OrdersCreateView(APIView):
    # allow guest checkout
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OrderCreateSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response({"detail": serializer.errors}, status=400)

        try:
            order = serializer.save()
        except Product.DoesNotExist:
            return Response(
                {"detail": "Produit introuvable dans la commande."}, status=400
            )
        except ProductVariant.DoesNotExist:
            return Response(
                {"detail": "Variante de produit introuvable dans la commande."},
                status=400,
            )

        # ✅ NEW: send to Google Sheet (non-blocking)
        send_order_to_google_sheet(order)

        return Response(OrderDetailSerializer(order).data, status=201)



class MyOrdersListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Order.objects.filter(user=request.user).order_by("-created_at")
        data = OrderDetailSerializer(qs, many=True).data
        return Response(data, status=200)



from django.shortcuts import get_object_or_404

from .models import Order
from .serializers import OrderDetailSerializer


class PublicOrderDetailView(APIView):
    """
    Public guest order lookup:
    GET /api/orders/public/<id>/<token>/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk, token):
        order = get_object_or_404(Order, pk=pk)

        # token must match
        if str(order.public_token) != str(token):
            return Response({"detail": "Invalid token."}, status=403)

        return Response(OrderDetailSerializer(order).data, status=200)


class OrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if not (
            request.user.is_staff
            or request.user.is_superuser
            or (order.user_id == request.user.id)
        ):
            return Response({"detail": "Not allowed."}, status=403)
        return Response(OrderDetailSerializer(order).data, status=200)


class OrderStatusAdminView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        status_new = request.data.get("status")
        valid = [c[0] for c in Order.Status.choices]
        if status_new not in valid:
            return Response(
                {"detail": f"Invalid status. Allowed: {valid}"}, status=400
            )
        order.status = status_new
        order.save()
        return Response(OrderDetailSerializer(order).data, status=200)


class AdminOrdersListView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        qs = Order.objects.all().order_by("-created_at")
        status_param = request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        data = OrderDetailSerializer(qs, many=True).data
        return Response(data, status=200)


class AdminOrderDetailView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        return Response(OrderDetailSerializer(order).data, status=200)

    def delete(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        order.delete()
        return Response(status=204)

# -------- Google Sheets integration ---------

def send_order_to_google_sheet(order):
    """
    Send basic order info to a Google Apps Script / webhook
    that writes into Google Sheets.

    GOOGLE_SHEET_WEBHOOK_URL must be defined in settings.py
    (or .env) – otherwise this does nothing.
    """
    url = getattr(settings, "GOOGLE_SHEET_WEBHOOK_URL", "")
    if not url:
        return

    payload = {
        "id": order.id,
        "full_name": order.full_name,
        "phone": order.phone,
        "city": order.city,
        "address": order.address,
        "notes": order.notes or "",
        "items_total": str(order.items_total),
        "shipping_price": str(order.shipping_price),
        "grand_total": str(order.grand_total),
        "status": order.status,
        "created_at": order.created_at.isoformat(),
    }

    try:
        # You can also use data=payload if your script expects form-data
        requests.post(url, json=payload, timeout=5)
    except Exception:
        # We do not break checkout if Google is down
        pass
