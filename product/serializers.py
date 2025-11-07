from rest_framework import serializers
from .models import Product, ProductVariant, WishlistItem, ShippingRate

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ["id", "label", "size_ml", "price", "in_stock", "sku"]

class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)

    promo_variant_id = serializers.ReadOnlyField()
    promo_variant_old_price = serializers.ReadOnlyField()
    promo_variant_new_price = serializers.ReadOnlyField()

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "description",
            "price", "new_price",
            "stock", "image", "image_url",
            "category", "brand",
            "has_discount", "discount_percent",
            "promo_variant_id", "promo_variant_old_price", "promo_variant_new_price",
            "variants",
        ]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url  # e.g. /images/products/xxx.jpg (because MEDIA_URL=/images/)
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
