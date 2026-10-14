import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_article_coupon_store_subscriber_order_coupon_code_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('new', 'Chờ xác nhận'), ('confirmed', 'Đã xác nhận'), ('shipping', 'Đang giao'), ('done', 'Hoàn tất'), ('cancelled', 'Đã hủy')], max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='products/%Y/%m/', verbose_name='Ảnh')),
                ('caption', models.CharField(blank=True, max_length=160, verbose_name='Chú thích')),
            ],
        ),
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delta', models.IntegerField(verbose_name='Thay đổi')),
                ('reason', models.CharField(max_length=200, verbose_name='Lý do')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RemoveConstraint(
            model_name='variant',
            name='unique_product_size',
        ),
        migrations.AddField(
            model_name='order',
            name='checkout_key',
            field=models.UUIDField(blank=True, editable=False, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='order',
            name='tracking_number',
            field=models.CharField(blank=True, max_length=100, verbose_name='Mã vận đơn'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='color',
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name='user',
            name='address',
            field=models.CharField(blank=True, max_length=300, verbose_name='Địa chỉ mặc định'),
        ),
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=15, verbose_name='Điện thoại'),
        ),
        migrations.AddField(
            model_name='variant',
            name='color',
            field=models.CharField(blank=True, max_length=60, verbose_name='Màu'),
        ),
        migrations.AddConstraint(
            model_name='variant',
            constraint=models.UniqueConstraint(fields=('product', 'color', 'size'), name='unique_product_color_size'),
        ),
        migrations.AddField(
            model_name='orderevent',
            name='actor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='orderevent',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='shop.order'),
        ),
        migrations.AddField(
            model_name='productimage',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='shop.product'),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='actor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='stockmovement',
            name='variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shop.variant'),
        ),
    ]
