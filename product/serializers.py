# backend/product/serializers.py
from decimal import Decimal, ROUND_HALF_UP
import pytz

from rest_framework import serializers

from .models import (
    Product,
    ProductVariant,
    WishlistItem,
    ShippingRate,
    Order,
    OrderItem,
)


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ["id", "label", "size_ml", "price", "new_price", "in_stock", "sku"]


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)

    promo_variant_id = serializers.ReadOnlyField()
    promo_variant_old_price = serializers.ReadOnlyField()
    promo_variant_new_price = serializers.ReadOnlyField()

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "new_price",
            "stock",
            "image",
            "image_url",
            "brand",
            "category",
            "categories",
            "is_favorite",
            "has_discount",
            "discount_percent",
            "promo_variant_id",
            "promo_variant_old_price",
            "promo_variant_new_price",
            "variants",
        ]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        source="product", queryset=Product.objects.all(), write_only=True
    )

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "product_id", "created_at"]


class ShippingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingRate
        fields = ["id", "city", "price", "active", "created_at"]
        read_only_fields = ["id", "created_at"]


# ======================= ORDERS =======================

class OrderItemWriteSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemWriteSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "city",
            "address",
            "notes",
            "payment_method",
            "shipping_price",
            "items",
        ]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Items list cannot be empty.")
        return value

    def _unit_price_for(self, product, variant):
        if variant:
            # ✅ variant-level promo first
            try:
                if (
                    variant.new_price is not None
                    and Decimal(str(variant.new_price)) > Decimal("0")
                    and Decimal(str(variant.new_price)) < Decimal(str(variant.price))
                ):
                    return variant.new_price
            except Exception:
                pass

            # fallback promo variant system
            if (
                product.has_discount
                and product.promo_variant_id
                and str(variant.id) == str(product.promo_variant_id)
            ):
                return product.promo_variant_new_price or variant.price

            return variant.price

        return product.new_price if product.has_discount else product.price

    def create(self, validated):
        request = self.context.get("request")
        user = request.user if request and getattr(request, "user", None) else None
        items = validated.pop("items", [])

        raw_shipping = validated.pop("shipping_price", None)
        if raw_shipping not in (None, ""):
            try:
                shipping_price = Decimal(str(raw_shipping))
            except Exception:
                shipping_price = Decimal("0.00")
        else:
            from .models import ShippingRate
            city = validated.get("city", "")
            rate = ShippingRate.objects.filter(active=True, city__iexact=city).first()
            shipping_price = rate.price if rate else Decimal("0.00")

        validated_items = []
        for item in items:
            pid = item["product_id"]
            vid = item.get("variant_id")
            qty = item["quantity"]

            try:
                product = Product.objects.get(id=pid)
            except Product.DoesNotExist:
                raise serializers.ValidationError({"detail": f"Produit avec id={pid} introuvable."})

            variant = None
            if vid is not None:
                try:
                    variant = ProductVariant.objects.get(id=vid, product=product)
                except ProductVariant.DoesNotExist:
                    raise serializers.ValidationError(
                        {"detail": f"Variante sélectionnée introuvable pour le produit « {product.name} »."}
                    )

            if not product.stock:
                raise serializers.ValidationError({"detail": f"Le produit « {product.name} » est en rupture de stock."})
            if variant is not None and not variant.in_stock:
                raise serializers.ValidationError(
                    {"detail": f"La variante « {variant.label} » du produit « {product.name} » est en rupture de stock."}
                )

            validated_items.append((product, variant, qty))

        order = Order.objects.create(
            user=user if user and user.is_authenticated else None,
            shipping_price=shipping_price,
            items_total=Decimal("0.00"),
            grand_total=Decimal("0.00"),
            **validated,
        )

        items_total = Decimal("0.00")

        for product, variant, qty in validated_items:
            unit_price = Decimal(self._unit_price_for(product, variant))
            line_total = (unit_price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                name=product.name,
                variant_label=(variant.label if variant else ""),
                unit_price=unit_price,
                quantity=qty,
                line_total=line_total,
            )
            items_total += line_total

        order.items_total = items_total.quantize(Decimal("0.01"))
        order.grand_total = (order.items_total + Decimal(order.shipping_price)).quantize(Decimal("0.01"))
        order.save()
        return order


class OrderItemReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "variant",
            "name",
            "variant_label",
            "unit_price",
            "quantity",
            "line_total",
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True)
    created_at_local = serializers.SerializerMethodField()

    # ✅ NEW: expose public_token so thank-you can fetch order for guests
    public_token = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = [
            "id",
            "public_token",  # ✅ NEW
            "status",
            "payment_method",
            "full_name",
            "email",
            "phone",
            "city",
            "address",
            "notes",
            "shipping_price",
            "items_total",
            "grand_total",
            "created_at",
            "created_at_local",
            "items",
        ]

    def get_created_at_local(self, obj):
        tz = pytz.timezone("Africa/Casablanca")
        local_dt = obj.created_at.astimezone(tz)
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
