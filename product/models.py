from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.db import models
from django.conf import settings

class Product(models.Model):
    class Category(models.TextChoices):
        FACE = "face", "Face"
        LIPS = "lips", "Lips"
        EYES = "eyes", "Eyes"
        EYEBROW = "eyebrow", "Eyebrow"
        HAIR = "hair", "Hair"
        # NEW
        BODY = "body", "Corps"
        PACKS = "packs", "Packs"
        ACNE = "acne", "Acné"
        HYPER_PIGMENTATION = "hyper_pigmentation", "Hyper pigmentation"
        BRIGHTENING = "brightening", "Éclaircissement"
        DRY_SKIN = "dry_skin", "Peau sèche"
        COMBINATION_OILY = "combination_oily", "Peau mixte/grasse"
        OTHER = "other", "Other"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    new_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    stock = models.BooleanField(default=False)
    image = models.ImageField(upload_to="products/", null=True, blank=True)

    # legacy single category (kept for compatibility)
    category = models.CharField(max_length=32, choices=Category.choices, default=Category.OTHER, db_index=True)
    # NEW: multi-categories as a JSON list of slugs
    categories = models.JSONField(default=list, blank=True)

    brand = models.CharField(max_length=120, blank=True, default="", db_index=True)

    @property
    def has_discount(self):
        try:
            return bool(self.new_price and self.new_price < self.price)
        except (TypeError, InvalidOperation):
            return False

    @property
    def discount_percent(self):
        if self.has_discount:
            try:
                return int(round((self.price - self.new_price) / self.price * 100))
            except (TypeError, InvalidOperation, ZeroDivisionError):
                return 0
        return 0

    def _biggest_variant(self):
        vs = list(self.variants.all())
        if not vs:
            return None
        with_size = [v for v in vs if v.size_ml not in (None, 0)]
        if with_size:
            return max(with_size, key=lambda v: v.size_ml)
        return max(vs, key=lambda v: v.price)

    @property
    def promo_variant(self):
        if not self.has_discount:
            return None
        return self._biggest_variant()

    @property
    def promo_variant_id(self):
        v = self.promo_variant
        return v.id if v else None

    @property
    def promo_variant_new_price(self):
        v = self.promo_variant
        if not v:
            return None
        pct = Decimal(self.discount_percent) / Decimal(100)
        return (Decimal(v.price) * (Decimal(1) - pct)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def promo_variant_old_price(self):
        v = self.promo_variant
        return v.price if v else None

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    label = models.CharField(max_length=80)
    size_ml = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    in_stock = models.BooleanField(default=True)
    sku = models.CharField(max_length=64, blank=True, default="", db_index=True)

    class Meta:
        unique_together = ("product", "label")
        ordering = ["price", "label"]

    def __str__(self):
        return f"{self.product.name} – {self.label}"


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} → {self.product}"


class ShippingRate(models.Model):
    city = models.CharField(max_length=120, unique=True, db_index=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["city"]

    def __str__(self):
        return f"{self.city} — {self.price} DH"
