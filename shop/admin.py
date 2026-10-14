from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Article, Category, Coupon, Order, OrderEvent, OrderItem, Product, ProductImage, Review, StockMovement, Store, Subscriber, User, Variant


@admin.register(User)
class ShopUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Vai trò shop", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Vai trò shop", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_staff", "is_active")
    actions = ["promote_to_employee"]

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_superuser

    @admin.action(description="Nâng khách hàng thành nhân viên", permissions=["change"])
    def promote_to_employee(self, request, queryset):
        if not self.has_change_permission(request):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        customers = queryset.filter(role=User.Role.CUSTOMER, is_active=True, is_staff=False, is_superuser=False)
        count = 0
        for customer in customers:
            customer.role = User.Role.EMPLOYEE
            customer.save(update_fields=["role"])
            self.log_change(request, customer, "Nâng khách hàng thành nhân viên")
            count += 1
        self.message_user(request, f"Đã nâng {count} tài khoản thành nhân viên.")


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 0
    readonly_fields = ("color", "size", "stock")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "active")
    list_filter = ("category", "active")
    search_fields = ("name",)
    inlines = [VariantInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("variant", "product_name", "size", "price", "quantity")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "total", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("customer", "recipient", "phone", "address", "note", "status", "total", "coupon_code", "discount", "created_at")
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Category)
admin.site.register([Coupon, Review, Store, Article, Subscriber])


@admin.register(StockMovement, OrderEvent)
class AuditAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
admin.site.site_header = "MENSWEAR • Quản trị"
admin.site.site_title = "MENSWEAR Admin"
