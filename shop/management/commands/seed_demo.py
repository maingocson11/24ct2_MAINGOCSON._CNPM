from django.core.management.base import BaseCommand
from shop.models import Article, Category, Coupon, Product, Variant


class Command(BaseCommand):
    help = "Tạo danh mục và sản phẩm mẫu; không tạo tài khoản hoặc mật khẩu mặc định."

    def handle(self, *args, **options):
        catalog = [
            ("Áo thun", "ao-thun", "Essential Cotton Tee", 249000, "Áo thun cotton mềm thoáng, phom regular dễ phối đồ.", "Trắng", "shirt"),
            ("Áo sơ mi", "ao-so-mi", "Oxford Everyday Shirt", 459000, "Sơ mi Oxford thanh lịch, phù hợp đi làm và dạo phố.", "Xanh", "shirt"),
            ("Quần", "quan", "Urban Straight Pants", 549000, "Quần ống đứng, chất vải bền và thoải mái suốt ngày dài.", "Be", "pants"),
            ("Áo polo", "ao-polo", "Signature Piqué Polo", 349000, "Áo polo dệt piqué thoáng mát với cổ áo chỉn chu.", "Đen", "shirt"),
            ("Áo thun", "ao-thun", "Heavyweight Relaxed Tee", 299000, "Cotton dày dặn, phom rộng dành cho phong cách hiện đại.", "Nâu", "shirt"),
            ("Quần", "quan", "Weekend Chino", 499000, "Quần chino tối giản với độ co giãn nhẹ.", "Xanh", "pants"),
        ]
        for category_name, slug, name, price, description, color, artwork in catalog:
            category, _ = Category.objects.get_or_create(slug=slug, defaults={"name": category_name})
            product, _ = Product.objects.get_or_create(name=name, defaults={"category": category, "price": price, "description": description, "color": color, "artwork": artwork})
            for size in ("S", "M", "L", "XL"):
                Variant.objects.get_or_create(product=product, size=size, defaults={"stock": 20})
        for code, discount, minimum in [("STYLE20", 20000, 419000), ("STYLE50", 50000, 699000), ("STYLE80", 80000, 899000), ("STYLE120", 120000, 1299000)]:
            Coupon.objects.get_or_create(code=code, defaults={"discount": discount, "minimum": minimum})
        Article.objects.get_or_create(title="3 cách phối áo thun cho một tuần năng động", defaults={"content": "Áo thun cotton là thiết kế thiết yếu cho tủ đồ nam. Phối cùng chino cho ngày đi làm, quần jeans cho ngày dạo phố hoặc quần short cho cuối tuần. Ưu tiên màu trung tính để dễ kết hợp và chọn phom vừa với vai để tạo vẻ ngoài chỉn chu."})
        Article.objects.get_or_create(title="Chọn phom quần phù hợp với bạn", defaults={"content": "Quần ống đứng giúp tạo đường nét cân đối và dễ phối với áo sơ mi, polo. Phom rộng mang lại cảm giác thoải mái. Hãy kiểm tra vòng eo và chiều dài trước khi chọn size; cân nặng chỉ là một thông số tham khảo."})
        self.stdout.write(self.style.SUCCESS("Created 6 demo products with size-based stock."))
