from functools import wraps
import uuid
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Q, Sum
from django.core.paginator import Paginator
from django import forms
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import CheckoutForm, ProductForm, ProductImageForm, ProfileForm, RegisterForm, ReviewForm, VariantFormSet
from .models import Article, Category, Order, Product, Review, StockMovement, Store, Subscriber, User, Variant
from .services import cart_lines, cart_summary, place_order, transition_order


def employee_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.can_manage:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def home(request):
    products = Product.objects.filter(active=True).select_related("category").prefetch_related("variants", "images")
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category:
        products = products.filter(category__slug=category)
    group = request.GET.get("group", "")
    if group in ("shirt", "pants"):
        products = products.filter(artwork=group)
    if request.GET.get("sale"):
        from django.db.models import F
        products = products.filter(original_price__gt=F("price"))
    size = request.GET.get("size", "")
    if size:
        products = products.filter(variants__size=size, variants__stock__gt=0).distinct()
    for parameter, lookup in (("min_price", "price__gte"), ("max_price", "price__lte")):
        value = request.GET.get(parameter, "")
        if value.isdigit():
            products = products.filter(**{lookup: int(value)})
    sort = request.GET.get("sort", "new")
    products = products.order_by({"price_up": "price", "price_down": "-price", "name": "name", "old": "pk"}.get(sort, "-pk"))
    page = Paginator(products, 12).get_page(request.GET.get("page"))
    parameters = request.GET.copy()
    parameters.pop("page", None)
    return render(request, "shop/home.html", {"products": page, "page": page, "page_query": parameters.urlencode(), "query": query, "selected_category": category, "sort": sort, "category_sections": [{"category": category_item, "products": category_item.product_set.filter(active=True).prefetch_related("variants")[:4]} for category_item in Category.objects.all()], "landing": not request.GET, "articles": Article.objects.filter(published=True).order_by("-pk")[:3]})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, active=True)
    if request.method == "POST":
        variant = get_object_or_404(Variant, pk=request.POST.get("variant") if request.POST.get("variant", "").isdigit() else 0, product=product)
        return add_cart(request, variant.pk)
    return render(request, "shop/product.html", {"product": product, "related": Product.objects.filter(active=True, category=product.category).exclude(pk=pk).prefetch_related("variants")[:4], "reviews": product.reviews.select_related("customer").order_by("-pk"), "rating": product.reviews.aggregate(value=Avg("rating"))["value"], "review_form": ReviewForm()})


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Tạo tài khoản thành công. Chào mừng bạn đến với MENSWEAR!")
        return redirect("home")
    return render(request, "shop/form.html", {"form": form, "title": "Tạo tài khoản", "button": "Đăng ký"})


@require_POST
def add_cart(request, pk):
    variant = get_object_or_404(Variant, pk=pk, product__active=True)
    cart = request.session.get("cart", {}).copy()
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 0
    combined = cart.get(str(pk), 0) + quantity
    if quantity < 1 or combined > variant.stock or combined > 99:
        messages.error(request, "Số lượng không hợp lệ hoặc vượt quá tồn kho.")
    else:
        cart[str(pk)] = combined
        request.session["cart"] = cart
        messages.success(request, "Đã thêm sản phẩm vào giỏ hàng.")
    return redirect("checkout" if request.POST.get("buy_now") and quantity > 0 and combined <= min(variant.stock, 99) else "cart")


def cart_view(request):
    return render(request, "shop/cart.html", session_summary(request))


def session_summary(request):
    try:
        return cart_summary(request.session.get("cart", {}), request.session.get("coupon", ""))
    except ValueError as error:
        messages.warning(request, str(error))
        request.session.pop("coupon", None)
        return cart_summary(request.session.get("cart", {}))


@require_POST
def apply_coupon(request):
    code = request.POST.get("code", "").strip()
    try:
        cart_summary(request.session.get("cart", {}), code)
    except ValueError as error:
        messages.error(request, str(error))
    else:
        request.session["coupon"] = code
        messages.success(request, "Đã cập nhật mã giảm giá." if code else "Đã bỏ mã giảm giá.")
    return redirect("cart")


@require_POST
def update_cart(request, pk):
    cart = request.session.get("cart", {}).copy()
    variant = get_object_or_404(Variant, pk=pk)
    try:
        quantity = int(request.POST.get("quantity", 0))
    except (ValueError, TypeError):
        quantity = -1
    if quantity == 0:
        cart.pop(str(pk), None)
    elif 1 <= quantity <= min(variant.stock, 99) and str(pk) in cart:
        cart[str(pk)] = quantity
    else:
        messages.error(request, "Số lượng không hợp lệ hoặc không đủ tồn kho.")
    request.session["cart"] = cart
    return redirect("cart")


@login_required
def checkout(request):
    if request.method == "POST" and request.POST.get("checkout_key"):
        try:
            key = uuid.UUID(request.POST["checkout_key"])
        except ValueError:
            key = None
        existing = request.user.orders.filter(checkout_key=key).first() if key else None
        if existing:
            return redirect("order_detail", pk=existing.pk)
    cart = request.session.get("cart", {})
    if not cart:
        messages.info(request, "Hãy thêm sản phẩm vào giỏ hàng trước.")
        return redirect("cart")
    key = request.session.setdefault("checkout_key", str(uuid.uuid4()))
    form = CheckoutForm(request.POST or None, initial={"recipient": request.user.get_full_name() or request.user.username, "phone": request.user.phone, "address": request.user.address})
    summary = session_summary(request)
    if request.method == "POST" and form.is_valid():
        if request.POST.get("checkout_key") != key:
            form.add_error(None, "Phiên đặt hàng đã thay đổi. Vui lòng tải lại trang.")
            return render(request, "shop/checkout.html", {"form": form, "checkout_key": key, **summary})
        try:
            order = place_order(request.user, cart, form.cleaned_data, request.session.get("coupon", ""), uuid.UUID(key))
        except ValueError as error:
            form.add_error(None, str(error))
        else:
            request.session["cart"] = {}
            request.session.pop("coupon", None)
            request.session.pop("checkout_key", None)
            messages.success(request, f"Đặt hàng thành công! Mã đơn #{order.pk}. Thanh toán khi nhận hàng (COD).")
            return redirect("order_detail", pk=order.pk)
    return render(request, "shop/checkout.html", {"form": form, "checkout_key": key, **summary})


@login_required
@require_POST
def review_product(request, pk):
    product = get_object_or_404(Product, pk=pk, active=True)
    purchased = request.user.orders.filter(status="done", items__variant__product=product).exists()
    if not purchased:
        messages.error(request, "Bạn có thể đánh giá sau khi mua và nhận sản phẩm.")
    else:
        form = ReviewForm(request.POST)
        if form.is_valid():
            Review.objects.update_or_create(product=product, customer=request.user, defaults=form.cleaned_data)
            messages.success(request, "Đã lưu đánh giá của bạn.")
        else:
            messages.error(request, "Chọn số sao 1–5 và nhập đánh giá tối đa 1500 ký tự.")
    return redirect("product", pk=pk)


def stores(request):
    return render(request, "shop/content.html", {"title": "Hệ thống cửa hàng", "stores": Store.objects.all()})


def articles(request):
    return render(request, "shop/content.html", {"title": "Tin thời trang", "articles": Article.objects.filter(published=True).order_by("-pk")})


def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk, published=True)
    return render(request, "shop/content.html", {"title": article.title, "article": article})


def policies(request):
    return render(request, "shop/policies.html")


@require_POST
def subscribe(request):
    try:
        email = forms.EmailField().clean(request.POST.get("email"))
    except forms.ValidationError:
        messages.error(request, "Vui lòng nhập email hợp lệ.")
    else:
        Subscriber.objects.get_or_create(email=email.lower())
        messages.success(request, "Đã đăng ký nhận tin. Bạn có thể yêu cầu admin xóa email bất cứ lúc nào.")
    return redirect("home")


@login_required
def orders(request):
    return render(request, "shop/orders.html", {"orders": request.user.orders.prefetch_related("items"), "management": False})


@employee_required
def dashboard(request):
    return render(request, "shop/dashboard.html", {"products": Product.objects.select_related("category").prefetch_related("variants"), "order_count": Order.objects.count(), "pending_count": Order.objects.filter(status="new").count(), "revenue": Order.objects.filter(status="done").aggregate(total=Sum("total"))["total"] or 0})


@employee_required
def product_edit(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else Product()
    form = ProductForm(request.POST or None, instance=product)
    formset = VariantFormSet(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        from django.db import transaction
        with transaction.atomic():
            form.save()
            for variant_form in formset:
                if variant_form.cleaned_data and variant_form.has_changed():
                    variant = variant_form.instance
                    old = Variant.objects.select_for_update().filter(pk=variant.pk).first() if variant.pk else None
                    delta = variant_form.cleaned_data["stock"] - old.stock if old else variant_form.cleaned_data["stock"]
                    variant.product = product
                    if old:
                        from django.db.models import F
                        updated = Variant.objects.filter(pk=old.pk, stock=old.stock).update(color=variant.color, size=variant.size, stock=F("stock") + delta)
                        if not updated:
                            raise ValueError("Tồn kho vừa thay đổi. Vui lòng tải lại trước khi lưu.")
                    else:
                        variant.save()
                    if delta:
                        StockMovement.objects.create(variant=variant, actor=request.user, delta=delta, reason="Điều chỉnh tồn kho từ trang sản phẩm")
        messages.success(request, "Đã lưu sản phẩm và tồn kho.")
        return redirect("dashboard")
    return render(request, "shop/form.html", {"form": form, "formset": formset, "title": "Sửa sản phẩm" if pk else "Thêm sản phẩm", "button": "Lưu sản phẩm"})


@employee_required
def manage_orders(request):
    orders = Order.objects.select_related("customer").prefetch_related("items")
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    if status:
        orders = orders.filter(status=status)
    if query:
        orders = orders.filter(Q(recipient__icontains=query) | Q(phone__icontains=query) | Q(customer__username__icontains=query) | Q(pk=int(query) if query.isdigit() else 0))
    return render(request, "shop/orders.html", {"orders": orders, "management": True, "statuses": Order.Status.choices})


@employee_required
@require_POST
def order_status(request, pk):
    get_object_or_404(Order, pk=pk)
    try:
        transition_order(pk, request.POST.get("status"), actor=request.user)
    except ValueError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Đã cập nhật trạng thái đơn hàng.")
    return redirect("manage_orders")


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật hồ sơ và địa chỉ mặc định.")
        return redirect("profile")
    return render(request, "shop/form.html", {"form": form, "title": "Hồ sơ của tôi", "button": "Lưu thông tin"})


@login_required
def order_detail(request, pk):
    queryset = Order.objects.all() if request.user.can_manage else request.user.orders.all()
    order = get_object_or_404(queryset.prefetch_related("items", "events__actor"), pk=pk)
    return render(request, "shop/order_detail.html", {"order": order})


@login_required
@require_POST
def cancel_order(request, pk):
    get_object_or_404(request.user.orders, pk=pk)
    try:
        transition_order(pk, "cancelled", actor=request.user, customer_cancel=True)
    except ValueError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Đã hủy đơn và hoàn tồn kho.")
    return redirect("order_detail", pk=pk)


@employee_required
@require_POST
def tracking(request, pk):
    order = get_object_or_404(Order, pk=pk)
    number = request.POST.get("tracking_number", "").strip()
    if len(number) > 100:
        messages.error(request, "Mã vận đơn tối đa 100 ký tự.")
    else:
        order.tracking_number = number
        order.save(update_fields=["tracking_number"])
        messages.success(request, "Đã cập nhật vận đơn.")
    return redirect("order_detail", pk=pk)


@employee_required
def product_images(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductImageForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        image = form.save(commit=False)
        image.product = product
        image.save()
        messages.success(request, "Đã thêm ảnh sản phẩm.")
        return redirect("product_images", pk=pk)
    return render(request, "shop/images.html", {"product": product, "form": form})


@employee_required
def inventory(request):
    movements = StockMovement.objects.select_related("variant__product", "actor").order_by("-pk")
    return render(request, "shop/inventory.html", {"page": Paginator(movements, 30).get_page(request.GET.get("page"))})


@login_required
def accounts(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    if request.method == "POST":
        target = get_object_or_404(User, pk=request.POST.get("user_id") if request.POST.get("user_id", "").isdigit() else 0, is_superuser=False, is_staff=False)
        role = request.POST.get("role")
        if role in (User.Role.CUSTOMER, User.Role.EMPLOYEE):
            target.role = role
            target.save(update_fields=["role"])
            from django.contrib.admin.models import CHANGE, LogEntry
            LogEntry.objects.log_actions(user_id=request.user.pk, queryset=[target], action_flag=CHANGE, change_message="Cập nhật vai trò: " + role)
            messages.success(request, "Đã cập nhật vai trò tài khoản.")
        return redirect("accounts")
    users = User.objects.filter(is_superuser=False, is_staff=False).order_by("username")
    query = request.GET.get("q", "").strip()
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))
    return render(request, "shop/accounts.html", {"page": Paginator(users, 25).get_page(request.GET.get("page"))})
