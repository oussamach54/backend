from decimal import Decimal, ROUND_HALF_UP
from django.contrib import admin
from .models import Product, ProductVariant, WishlistItem, ShippingRate


def _round_money(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "brand", "category", "price", "new_price",
                    "discount_percent", "has_discount", "stock")
    list_filter = ("brand", "category", "stock")
    search_fields = ("name", "brand")
    readonly_fields = ("has_discount", "discount_percent")
    fields = (
        "name", "brand", "category", "image", "description",
        "price", "new_price",
        "stock",
        "has_discount", "discount_percent",
    )

    actions = ["discount_10", "discount_20", "discount_30", "clear_discount"]

    def _apply_pct(self, queryset, pct: int):
        for p in queryset:
            if p.price and p.price > 0:
                p.new_price = _round_money(Decimal(p.price) * Decimal(100 - pct) / Decimal(100))
                p.save()

    def discount_10(self, request, queryset):
        self._apply_pct(queryset, 10)
        self.message_user(request, f"Applied 10% discount to {queryset.count()} products.")
    discount_10.short_description = "Apply 10% discount (set new_price)"

    def discount_20(self, request, queryset):
        self._apply_pct(queryset, 20)
        self.message_user(request, f"Applied 20% discount to {queryset.count()} products.")
    discount_20.short_description = "Apply 20% discount (set new_price)"

    def discount_30(self, request, queryset):
        self._apply_pct(queryset, 30)
        self.message_user(request, f"Applied 30% discount to {queryset.count()} products.")
    discount_30.short_description = "Apply 30% discount (set new_price)"

    def clear_discount(self, request, queryset):
        queryset.update(new_price=None)
        self.message_user(request, f"Cleared discounts on {queryset.count()} products.")
    clear_discount.short_description = "Clear discount (unset new_price)"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "label", "price", "in_stock", "sku")
    list_filter = ("in_stock",)
    search_fields = ("product__name", "label", "sku")


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "product__name")


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ("id", "city", "price", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("city",)



from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("name", "variant_label", "unit_price", "quantity", "line_total")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "phone", "city", "status", "grand_total", "created_at")
    list_filter  = ("status", "payment_method", "city")
    search_fields = ("full_name", "phone", "city", "email")
    inlines = [OrderItemInline]