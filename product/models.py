# product/models.py
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.db import models
from django.conf import settings


class Product(models.Model):
    class Category(models.TextChoices):
        # existing
        FACE = "face", "Visage"
        LIPS = "lips", "Lèvres"
        EYES = "eyes", "Yeux"
        EYEBROW = "eyebrow", "Sourcils"
        HAIR = "hair", "Cheveux"
        OTHER = "other", "Other"

        # NEW additions (single select still)
        BODY = "body", "Corps"
        PACKS = "packs", "Packs"
        ACNE = "acne", "Acné"
        HYPER_PIGMENTATION = "hyper_pigmentation", "Hyper pigmentation"
        BRIGHTENING = "brightening", "Éclaircissement"
        DRY_SKIN = "dry_skin", "Peau sèche"
        COMBINATION_OILY = "combination_oily", "Peau mixte/grasse"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Base price (original)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    # Promo price (optional). If set and < price ⇒ discount active
    new_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    stock = models.BooleanField(default=False)
    image = models.ImageField(upload_to="products/", null=True, blank=True)

    category = models.CharField(
        max_length=30,  # keep >= longest slug ("hyper_pigmentation" length 19; 30 is safe)
        choices=Category.choices,
        default=Category.OTHER,
        db_index=True,
    )
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

    # ----- variant-promo helpers (promo applies ONLY to biggest variant) -----
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
        newp = (Decimal(v.price) * (Decimal(1) - pct)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return newp

    @property
    def promo_variant_old_price(self):
        v = self.promo_variant
        return v.price if v else None

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    label = models.CharField(max_length=80)  # e.g. "500 ml"
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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} → {self.product}"


class ShippingRate(models.Model):
    city = models.CharField(max_length=120, unique=True, db_index=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)  # DH
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["city"]

    def __str__(self):
        return f"{self.city} — {self.price} DH"

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING   = "pending", "En attente"
        PAID      = "paid", "Payée"
        SHIPPED   = "shipped", "Expédiée"
        DELIVERED = "delivered", "Livrée"
        CANCELED  = "canceled", "Annulée"

    class PaymentMethod(models.TextChoices):
        COD  = "cod", "Paiement à la livraison"
        CARD = "card", "Carte/En ligne"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )

    # snapshot of who/where to ship
    full_name = models.CharField(max_length=120)
    email     = models.EmailField(blank=True, default="")
    phone     = models.CharField(max_length=32)
    city      = models.CharField(max_length=120)
    address   = models.CharField(max_length=255)
    notes     = models.TextField(blank=True, default="")

    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.COD)
    status         = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)

    # money snapshots
    shipping_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    items_total    = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    grand_total    = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} — {self.full_name} — {self.status}"


class OrderItem(models.Model):
    order   = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("product.Product", on_delete=models.SET_NULL, null=True, blank=True)
    variant = models.ForeignKey("product.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True)

    # snapshots for resilience
    name          = models.CharField(max_length=200)
    variant_label = models.CharField(max_length=80, blank=True, default="")
    unit_price    = models.DecimalField(max_digits=10, decimal_places=2)
    quantity      = models.PositiveIntegerField(default=1)
    line_total    = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} x{self.quantity} ({self.unit_price})"