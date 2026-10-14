from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class User(AbstractUser):
    phone = models.CharField("Điện thoại", max_length=15, blank=True)
    address = models.CharField("Địa chỉ mặc định", max_length=300, blank=True)
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Khách hàng"
        EMPLOYEE = "employee", "Nhân viên"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.CUSTOMER)

    @property
    def can_manage(self):
        return self.is_active and (self.is_superuser or self.role in (self.Role.EMPLOYEE, self.Role.ADMIN))


class Category(models.Model):
    name = models.CharField("Tên danh mục", max_length=80, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    image_url = models.URLField("URL ảnh sản phẩm", blank=True)
    original_price = models.PositiveIntegerField("Giá gốc", default=0)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="Danh mục")
    name = models.CharField("Tên sản phẩm", max_length=160)
    description = models.TextField("Mô tả")
    price = models.PositiveIntegerField("Giá (VNĐ)")
    color = models.CharField("Màu", max_length=60, default="Đen")
    artwork = models.CharField("Minh họa", max_length=12, choices=[("shirt", "Áo"), ("pants", "Quần")], default="shirt")
    active = models.BooleanField("Đang bán", default=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(price__gt=0), name="product_price_positive")]

    def __str__(self):
        return self.name


class Variant(models.Model):
    color = models.CharField("Màu", max_length=60, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField("Size", max_length=8)
    stock = models.PositiveIntegerField("Tồn kho", default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["product", "color", "size"], name="unique_product_color_size")]

    def __str__(self):
        return f"{self.product.name} / {self.size}"


class Order(models.Model):
    checkout_key = models.UUIDField(unique=True, null=True, blank=True, editable=False)
    tracking_number = models.CharField("Mã vận đơn", max_length=100, blank=True)
    coupon_code = models.CharField(max_length=40, blank=True)
    discount = models.PositiveIntegerField(default=0)
    class Status(models.TextChoices):
        NEW = "new", "Chờ xác nhận"
        CONFIRMED = "confirmed", "Đã xác nhận"
        SHIPPING = "shipping", "Đang giao"
        DONE = "done", "Hoàn tất"
        CANCELLED = "cancelled", "Đã hủy"

    customer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    recipient = models.CharField("Người nhận", max_length=100)
    phone = models.CharField("Số điện thoại", max_length=15)
    address = models.CharField("Địa chỉ giao hàng", max_length=300)
    note = models.TextField("Ghi chú", blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)
    total = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class OrderItem(models.Model):
    color = models.CharField(max_length=60, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(Variant, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=160)
    size = models.CharField(max_length=8)
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.price * self.quantity


class Coupon(models.Model):
    code = models.CharField("Mã", max_length=40, unique=True)
    discount = models.PositiveIntegerField("Giảm (VNĐ)")
    minimum = models.PositiveIntegerField("Đơn tối thiểu", default=0)
    active = models.BooleanField("Đang áp dụng", default=True)

    def __str__(self):
        return self.code


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField("Số sao", choices=[(number, str(number)) for number in range(1, 6)])
    content = models.TextField("Nội dung", max_length=1500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["product", "customer"], name="one_review_per_customer"), models.CheckConstraint(condition=Q(rating__gte=1, rating__lte=5), name="review_rating_range")]


class Store(models.Model):
    name = models.CharField("Tên cửa hàng", max_length=100)
    address = models.CharField("Địa chỉ", max_length=300)
    phone = models.CharField("Điện thoại", max_length=20, blank=True)
    hours = models.CharField("Giờ mở cửa", max_length=100, default="08:30 – 22:00")

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField("Tiêu đề", max_length=180)
    content = models.TextField("Nội dung")
    published = models.BooleanField("Đã xuất bản", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("Ảnh", upload_to="products/%Y/%m/")
    caption = models.CharField("Chú thích", max_length=160, blank=True)


class StockMovement(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.PROTECT)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    delta = models.IntegerField("Thay đổi")
    reason = models.CharField("Lý do", max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


class OrderEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=16, choices=Order.Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)
