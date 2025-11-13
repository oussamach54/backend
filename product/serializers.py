from rest_framework import serializers
from .models import Product, ProductVariant, WishlistItem, ShippingRate


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ["id", "label", "size_ml", "price", "in_stock", "sku"]


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    # expose promo fields so the UI can show promo only on the biggest variant
    promo_variant_id = serializers.ReadOnlyField()
    promo_variant_old_price = serializers.ReadOnlyField()
    promo_variant_new_price = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "description",
            "price", "new_price",
            "stock", "image", "category", "brand",
            "has_discount", "discount_percent",
            "promo_variant_id", "promo_variant_old_price", "promo_variant_new_price",
            "variants",
        ]


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




from .models import  Order, OrderItem

class OrderItemWriteSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity   = serializers.IntegerField(min_value=1)

class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemWriteSerializer(many=True)

    class Meta:
        model  = Order
        fields = [
            "id", "full_name", "email", "phone", "city", "address", "notes",
            "payment_method", "items",
        ]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Items list cannot be empty.")
        return value

    def _unit_price_for(self, product, variant):
        # promo logic mirrors your Product helpers
        if variant:
            if product.has_discount and product.promo_variant_id and str(variant.id) == str(product.promo_variant_id):
                return product.promo_variant_new_price or variant.price
            return variant.price
        else:
            return product.new_price if product.has_discount else product.price

    def create(self, validated):
        user  = self.context["request"].user if self.context and self.context.get("request") else None
        items = validated.pop("items", [])

        # shipping by active city rate (case-insensitive)
        city = validated.get("city", "")
        rate = ShippingRate.objects.filter(active=True, city__iexact=city).first()
        shipping_price = rate.price if rate else 0

        order = Order.objects.create(
            user=user if user and user.is_authenticated else None,
            shipping_price=shipping_price,
            items_total=0,
            grand_total=0,
            **validated,
        )

        items_total = Decimal("0.00")
        for item in items:
            pid = item["product_id"]
            vid = item.get("variant_id")
            qty = item["quantity"]

            product = Product.objects.get(id=pid)
            variant = ProductVariant.objects.get(id=vid, product=product) if vid else None

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
        model  = OrderItem
        fields = ["id", "product", "variant", "name", "variant_label", "unit_price", "quantity", "line_total"]


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True)

    class Meta:
        model  = Order
        fields = [
            "id", "status", "payment_method",
            "full_name", "email", "phone", "city", "address", "notes",
            "shipping_price", "items_total", "grand_total",
            "created_at", "items",
        ]