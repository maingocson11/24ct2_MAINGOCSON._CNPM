import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=180, verbose_name='Tiêu đề')),
                ('content', models.TextField(verbose_name='Nội dung')),
                ('published', models.BooleanField(default=True, verbose_name='Đã xuất bản')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=40, unique=True, verbose_name='Mã')),
                ('discount', models.PositiveIntegerField(verbose_name='Giảm (VNĐ)')),
                ('minimum', models.PositiveIntegerField(default=0, verbose_name='Đơn tối thiểu')),
                ('active', models.BooleanField(default=True, verbose_name='Đang áp dụng')),
            ],
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Tên cửa hàng')),
                ('address', models.CharField(max_length=300, verbose_name='Địa chỉ')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Điện thoại')),
                ('hours', models.CharField(default='08:30 – 22:00', max_length=100, verbose_name='Giờ mở cửa')),
            ],
        ),
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='coupon_code',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='order',
            name='discount',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='product',
            name='image_url',
            field=models.URLField(blank=True, verbose_name='URL ảnh sản phẩm'),
        ),
        migrations.AddField(
            model_name='product',
            name='original_price',
            field=models.PositiveIntegerField(default=0, verbose_name='Giá gốc'),
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], verbose_name='Số sao')),
                ('content', models.TextField(max_length=1500, verbose_name='Nội dung')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='shop.product')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('product', 'customer'), name='one_review_per_customer'), models.CheckConstraint(condition=models.Q(('rating__gte', 1), ('rating__lte', 5)), name='review_rating_range')],
            },
        ),
    ]
