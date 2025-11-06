# payments/views.py (only the helper functions changed)
from django.conf import settings
# ... imports stay the same ...

def _frontend_success_url(request, order_id: int) -> str:
    base = getattr(settings, "CMI_SUCCESS_URL", None)
    if base:
        sep = "&" if "?" in base else "?"
        return f"{base}{sep}order={order_id}"

    # ✅ use FRONTEND_URL (exists in settings)
    frontend = getattr(settings, "FRONTEND_URL", "")
    if frontend:
        return f"{frontend.rstrip('/')}/payment-status?order={order_id}"

    return f"/payment-status?order={order_id}"

def _frontend_fail_url(request, order_id: int) -> str:
    base = getattr(settings, "CMI_FAIL_URL", None)
    if base:
        sep = "&" if "?" in base else "?"
        return f"{base}{sep}order={order_id}"

    # ✅ use FRONTEND_URL
    frontend = getattr(settings, "FRONTEND_URL", "")
    if frontend:
        return f"{frontend.rstrip('/')}/payment-status?order={order_id}&status=failed"

    return f"/payment-status?order={order_id}&status=failed"
