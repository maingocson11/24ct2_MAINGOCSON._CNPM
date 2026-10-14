from django.db import transaction
from django.db.models import F
from .models import Coupon, Order, OrderEvent, OrderItem, StockMovement, Variant


def cart_summary(cart, code=""):
    lines = cart_lines(cart)
    subtotal = sum(line["subtotal"] for line in lines)
    coupon = None
    if code:
        coupon = Coupon.objects.filter(code__iexact=code.strip(), active=True).first()
        if not coupon or subtotal < coupon.minimum:
            raise ValueError("Mã giảm giá không hợp lệ hoặc đơn chưa đạt mức tối thiểu.")
    discount = min(coupon.discount, subtotal) if coupon else 0
    return {"lines": lines, "subtotal": subtotal, "discount": discount, "total": subtotal - discount, "coupon": coupon}


def cart_lines(cart):
    variants = Variant.objects.select_related("product").filter(pk__in=cart.keys())
    lines = []
    for variant in variants:
        quantity = cart.get(str(variant.pk), 0)
        if quantity > 0:
            lines.append({"variant": variant, "quantity": quantity, "subtotal": variant.product.price * quantity})
    return lines


@transaction.atomic
def place_order(customer, cart, details, code="", checkout_key=None):
    if checkout_key:
        existing = Order.objects.filter(customer=customer, checkout_key=checkout_key).first()
        if existing:
            return existing
    lines = cart_lines(cart)
    if not lines or len(lines) != len(cart):
        raise ValueError("Giỏ hàng trống hoặc có sản phẩm không còn tồn tại.")
    summary = cart_summary(cart, code)
    order = Order.objects.create(customer=customer, checkout_key=checkout_key, total=summary["total"], discount=summary["discount"], coupon_code=summary["coupon"].code if summary["coupon"] else "", **details)
    for line in lines:
        variant = line["variant"]
        quantity = line["quantity"]
        updated = Variant.objects.filter(pk=variant.pk, stock__gte=quantity, product__active=True).update(stock=F("stock") - quantity)
        if not updated:
            raise ValueError(f"{variant.product.name} size {variant.size} không còn đủ hàng. Vui lòng cập nhật giỏ hàng.")
        OrderItem.objects.create(order=order, variant=variant, product_name=variant.product.name, color=variant.color or variant.product.color, size=variant.size, price=variant.product.price, quantity=quantity)
        StockMovement.objects.create(variant=variant, actor=customer, delta=-quantity, reason=f"Đặt đơn #{order.pk}")
    OrderEvent.objects.create(order=order, actor=customer, status=order.status)
    return order


@transaction.atomic
def transition_order(order_id, target, actor=None, customer_cancel=False):
    order = Order.objects.select_for_update().get(pk=order_id)
    if customer_cancel and (not actor or actor.pk != order.customer_id or order.status != "new" or target != "cancelled"):
        raise ValueError("Bạn chỉ có thể hủy đơn của mình khi đang chờ xác nhận.")
    allowed = {"new": ["confirmed", "cancelled"], "confirmed": ["shipping", "cancelled"], "shipping": ["done"], "done": [], "cancelled": []}
    if target not in allowed[order.status]:
        raise ValueError("Không thể chuyển sang trạng thái này.")
    changed = Order.objects.filter(pk=order.pk, status=order.status).update(status=target)
    if not changed:
        raise ValueError("Đơn hàng vừa được cập nhật. Vui lòng tải lại trang.")
    if target == Order.Status.CANCELLED:
        for item in order.items.all():
            Variant.objects.filter(pk=item.variant_id).update(stock=F("stock") + item.quantity)
            StockMovement.objects.create(variant=item.variant, actor=actor, delta=item.quantity, reason=f"Hủy đơn #{order.pk}")
    OrderEvent.objects.create(order=order, actor=actor, status=target)
