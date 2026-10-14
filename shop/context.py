from .models import Category, Coupon


def navigation(request):
    cart = request.session.get("cart", {})
    return {"nav_categories": Category.objects.all(), "cart_count": sum(cart.values()), "coupons": Coupon.objects.filter(active=True).order_by("minimum")}
