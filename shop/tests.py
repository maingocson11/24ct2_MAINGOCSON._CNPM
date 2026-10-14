from django.test import TestCase
from django.urls import reverse
from .models import Category, Order, Product, User, Variant
from .services import place_order, transition_order


class ShopTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="customer", password="StrongPass123!")
        self.employee = User.objects.create_user(username="employee", password="StrongPass123!", role="employee")
        category = Category.objects.create(name="Áo", slug="ao")
        self.product = Product.objects.create(category=category, name="Áo mẫu", price=250000, description="Cotton")
        self.variant = Variant.objects.create(product=self.product, size="M", stock=3)
        self.details = {"recipient": "Nguyễn Văn An", "phone": "0901234567", "address": "123 Nguyễn Trãi", "note": ""}

    def test_pages_render(self):
        for url in (reverse("home"), reverse("product", args=[self.product.pk]), reverse("cart"), reverse("login"), reverse("register")):
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_role_permissions(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 403)
        self.assertEqual(self.client.get(reverse("manage_orders")).status_code, 403)
        self.assertEqual(self.client.get("/admin/").status_code, 302)
        self.client.force_login(self.employee)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("manage_orders")).status_code, 200)
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_registration_cannot_escalate_role(self):
        self.client.post(reverse("register"), {"username": "newbuyer", "email": "buyer@example.com", "password1": "UniqueStrongPass293!", "password2": "UniqueStrongPass293!", "role": "admin", "is_staff": "1", "is_superuser": "1"})
        user = User.objects.get(username="newbuyer")
        self.assertEqual(user.role, "customer")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_checkout_and_customer_order_isolation(self):
        self.client.post(reverse("add_cart", args=[self.variant.pk]), {"quantity": 2})
        self.client.force_login(self.customer)
        self.client.get(reverse("checkout"))
        details = {**self.details, "checkout_key": self.client.session["checkout_key"]}
        response = self.client.post(reverse("checkout"), details)
        self.assertRedirects(response, reverse("order_detail", args=[Order.objects.get().pk]))
        order = Order.objects.get()
        self.assertEqual(order.total, 500000)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 1)
        self.assertEqual(self.client.session["cart"], {})
        other = User.objects.create_user(username="other")
        self.client.force_login(other)
        response = self.client.get(reverse("orders"))
        self.assertNotContains(response, "Nguyễn Văn An")

    def test_failed_order_rolls_back_all_stock_changes(self):
        second = Variant.objects.create(product=self.product, size="L", stock=0)
        with self.assertRaises(ValueError):
            place_order(self.customer, {str(self.variant.pk): 2, str(second.pk): 1}, self.details)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 3)
        self.assertFalse(Order.objects.exists())

    def test_cancellation_restores_stock_once(self):
        order = place_order(self.customer, {str(self.variant.pk): 2}, self.details)
        transition_order(order.pk, "cancelled")
        with self.assertRaises(ValueError):
            transition_order(order.pk, "cancelled")
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 3)

    def test_order_state_flow(self):
        order = place_order(self.customer, {str(self.variant.pk): 1}, self.details)
        with self.assertRaises(ValueError):
            transition_order(order.pk, "done")
        for status in ("confirmed", "shipping", "done"):
            transition_order(order.pk, status)
        order.refresh_from_db()
        self.assertEqual(order.status, "done")

    def test_stock_limit_and_post_only_mutations(self):
        self.client.post(reverse("add_cart", args=[self.variant.pk]), {"quantity": 4})
        self.assertEqual(self.client.session.get("cart", {}), {})
        self.assertEqual(self.client.get(reverse("add_cart", args=[self.variant.pk])).status_code, 405)

    def test_csrf_required(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse("add_cart", args=[self.variant.pk]), {"quantity": 1}).status_code, 403)

    def test_coupon_is_validated_and_saved_on_order(self):
        from .models import Coupon
        Coupon.objects.create(code="SAVE20", discount=20000, minimum=400000)
        with self.assertRaises(ValueError):
            place_order(self.customer, {str(self.variant.pk): 1}, self.details, "SAVE20")
        self.assertFalse(Order.objects.exists())
        order = place_order(self.customer, {str(self.variant.pk): 2}, self.details, "save20")
        self.assertEqual(order.total, 480000)
        self.assertEqual(order.discount, 20000)
        self.assertEqual(order.coupon_code, "SAVE20")

    def test_review_requires_completed_purchase(self):
        from .models import Review
        self.client.force_login(self.customer)
        url = reverse("review_product", args=[self.product.pk])
        self.client.post(url, {"rating": 5, "content": "Tot"})
        self.assertFalse(Review.objects.exists())
        order = place_order(self.customer, {str(self.variant.pk): 1}, self.details)
        for status in ("confirmed", "shipping", "done"):
            transition_order(order.pk, status)
        self.client.post(url, {"rating": 5, "content": "Tot"})
        self.client.post(url, {"rating": 4, "content": "Cap nhat"})
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.get().rating, 4)

    def test_buy_now_and_filters(self):
        response = self.client.post(reverse("product", args=[self.product.pk]), {"variant": self.variant.pk, "quantity": 1, "buy_now": 1})
        self.assertRedirects(response, reverse("checkout"), fetch_redirect_response=False)
        response = self.client.get(reverse("home"), {"min_price": 260000, "size": "M"})
        self.assertEqual(response.context["page"].paginator.count, 0)

    def test_content_and_newsletter(self):
        for name in ("stores", "articles", "policies"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        from .models import Subscriber
        self.client.post(reverse("subscribe"), {"email": "bad"})
        self.assertFalse(Subscriber.objects.exists())
        self.client.post(reverse("subscribe"), {"email": "test@example.com"})
        self.assertEqual(Subscriber.objects.count(), 1)

    def test_duplicate_checkout_creates_one_order(self):
        self.client.force_login(self.customer)
        self.client.post(reverse("add_cart", args=[self.variant.pk]), {"quantity": 1})
        self.client.get(reverse("checkout"))
        details = {**self.details, "checkout_key": self.client.session["checkout_key"]}
        self.client.post(reverse("checkout"), details)
        self.client.post(reverse("checkout"), details)
        self.assertEqual(Order.objects.count(), 1)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 2)

    def test_customer_cancellation_and_order_access(self):
        order = place_order(self.customer, {str(self.variant.pk): 1}, self.details)
        self.client.force_login(self.employee)
        self.assertEqual(self.client.post(reverse("cancel_order", args=[order.pk])).status_code, 404)
        other = User.objects.create_user(username="outsider")
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse("order_detail", args=[order.pk])).status_code, 404)
        self.client.force_login(self.customer)
        self.client.post(reverse("cancel_order", args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.status, "cancelled")
        self.assertEqual(order.events.count(), 2)

    def test_profile_cannot_change_role(self):
        self.client.force_login(self.customer)
        self.client.post(reverse("profile"), {"first_name": "An", "last_name": "Nguyen", "email": "an@example.com", "phone": "0901234567", "address": "123 Pho", "role": "admin"})
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, "customer")
        self.assertEqual(self.customer.address, "123 Pho")

    def test_admin_accounts_page(self):
        self.client.force_login(self.employee)
        self.assertEqual(self.client.get(reverse("accounts")).status_code, 403)
        admin = User.objects.create_superuser(username="owner", password="StrongPass123!")
        self.client.force_login(admin)
        self.client.post(reverse("accounts"), {"user_id": self.customer.pk, "role": "employee"})
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, "employee")
        self.assertFalse(self.customer.is_staff)

    def test_multiple_colors_have_independent_stock(self):
        second = Variant.objects.create(product=self.product, color="Red", size="M", stock=5)
        order = place_order(self.customer, {str(second.pk): 2}, self.details)
        self.assertEqual(order.items.get().color, "Red")
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 3)
        second.refresh_from_db()
        self.assertEqual(second.stock, 3)

    def test_image_upload_and_invalid_file(self):
        import io
        import tempfile
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import ProductImage
        self.client.force_login(self.employee)
        url = reverse("product_images", args=[self.product.pk])
        with tempfile.TemporaryDirectory() as directory, self.settings(MEDIA_ROOT=directory):
            response = self.client.post(url, {"image": SimpleUploadedFile("invalid.png", b"not an image", content_type="image/png")})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(ProductImage.objects.exists())
            buffer = io.BytesIO()
            Image.new("RGB", (40, 40), "blue").save(buffer, format="PNG")
            response = self.client.post(url, {"image": SimpleUploadedFile("product.png", buffer.getvalue(), content_type="image/png"), "caption": "Blue shirt"})
            self.assertRedirects(response, url)
            self.assertEqual(ProductImage.objects.count(), 1)
            self.assertEqual(self.client.get(reverse("product", args=[self.product.pk])).status_code, 200)

    def test_tracking_permissions(self):
        order = place_order(self.customer, {str(self.variant.pk): 1}, self.details)
        url = reverse("tracking", args=[order.pk])
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(url, {"tracking_number": "TRACK123"}).status_code, 403)
        self.client.force_login(self.employee)
        self.client.post(url, {"tracking_number": "TRACK123"})
        order.refresh_from_db()
        self.assertEqual(order.tracking_number, "TRACK123")

    def test_password_reset_sends_email(self):
        from django.core import mail
        self.customer.email = "customer@example.com"
        self.customer.save()
        self.client.post(reverse("password_reset"), {"email": self.customer.email})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/reset/", mail.outbox[0].body)

    def test_admin_can_promote_customer_without_admin_access(self):
        administrator = User.objects.create_superuser(username="admin", password="StrongPass123!", role="admin")
        self.client.force_login(administrator)
        response = self.client.post(reverse("admin:shop_user_changelist"), {"action": "promote_to_employee", "_selected_action": [self.customer.pk, administrator.pk], "index": 0}, follow=True)
        self.assertContains(response, "Đã nâng 1 tài khoản thành nhân viên.")
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, "employee")
        self.assertFalse(self.customer.is_staff)
        self.assertFalse(self.customer.is_superuser)
        administrator.refresh_from_db()
        self.assertEqual(administrator.role, "admin")
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:shop_user_changelist")).status_code, 302)

    def test_employee_cannot_promote_customers(self):
        self.client.force_login(self.employee)
        self.client.post(reverse("admin:shop_user_changelist"), {"action": "promote_to_employee", "_selected_action": [self.customer.pk]})
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, "customer")

    def test_staff_with_user_permission_cannot_assign_roles(self):
        from django.contrib.auth.models import Permission
        self.employee.is_staff = True
        self.employee.save()
        self.employee.user_permissions.add(Permission.objects.get(codename="change_user", content_type__app_label="shop"))
        self.client.force_login(self.employee)
        response = self.client.post(reverse("admin:shop_user_change", args=[self.customer.pk]), {"role": "employee"})
        self.assertEqual(response.status_code, 403)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, "customer")
