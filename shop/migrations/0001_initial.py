import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True, verbose_name='Tên danh mục')),
                ('slug', models.SlugField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('role', models.CharField(choices=[('customer', 'Khách hàng'), ('employee', 'Nhân viên'), ('admin', 'Admin')], default='customer', max_length=16)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipient', models.CharField(max_length=100, verbose_name='Người nhận')),
                ('phone', models.CharField(max_length=15, verbose_name='Số điện thoại')),
                ('address', models.CharField(max_length=300, verbose_name='Địa chỉ giao hàng')),
                ('note', models.TextField(blank=True, verbose_name='Ghi chú')),
                ('status', models.CharField(choices=[('new', 'Chờ xác nhận'), ('confirmed', 'Đã xác nhận'), ('shipping', 'Đang giao'), ('done', 'Hoàn tất'), ('cancelled', 'Đã hủy')], default='new', max_length=16)),
                ('total', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=160, verbose_name='Tên sản phẩm')),
                ('description', models.TextField(verbose_name='Mô tả')),
                ('price', models.PositiveIntegerField(verbose_name='Giá (VNĐ)')),
                ('color', models.CharField(default='Đen', max_length=60, verbose_name='Màu')),
                ('artwork', models.CharField(choices=[('shirt', 'Áo'), ('pants', 'Quần')], default='shirt', max_length=12, verbose_name='Minh họa')),
                ('active', models.BooleanField(default=True, verbose_name='Đang bán')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shop.category', verbose_name='Danh mục')),
            ],
        ),
        migrations.CreateModel(
            name='Variant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size', models.CharField(max_length=8, verbose_name='Size')),
                ('stock', models.PositiveIntegerField(default=0, verbose_name='Tồn kho')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='shop.product')),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=160)),
                ('size', models.CharField(max_length=8)),
                ('price', models.PositiveIntegerField()),
                ('quantity', models.PositiveIntegerField()),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='shop.order')),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shop.variant')),
            ],
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(condition=models.Q(('price__gt', 0)), name='product_price_positive'),
        ),
        migrations.AddConstraint(
            model_name='variant',
            constraint=models.UniqueConstraint(fields=('product', 'size'), name='unique_product_size'),
        ),
    ]
