# 24ct2_MAINGOCSON_CNPM — Shop thời trang nam Django

Website tiếng Việt, responsive, sử dụng Django 5.2 và SQLite. Bộ sản phẩm mẫu dùng minh họa SVG nội bộ, chạy không cần dịch vụ hình ảnh bên ngoài.

## Chạy trên Windows / PowerShell

Yêu cầu Python 3.10 trở lên đã cài trên máy (khuyến nghị Python 3.12).

Mở terminal trong thư mục chứa README này:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe manage.py migrate
./.venv/Scripts/python.exe manage.py seed_demo
./.venv/Scripts/python.exe manage.py createsuperuser
./.venv/Scripts/python.exe manage.py runserver
```

Truy cập http://127.0.0.1:8000/ và trang admin http://127.0.0.1:8000/admin/.

Nếu lệnh python chưa khả dụng, cài Python và bật tùy chọn Add Python to PATH, hoặc thay python bằng đường dẫn đầy đủ tới python.exe.

## Ba tác nhân

| Tác nhân | Chức năng |
| --- | --- |
| Admin | Tài khoản superuser: quản lý tài khoản, cấp vai trò, danh mục, sản phẩm và xem đơn trong Django Admin; xử lý đơn qua /staff/orders/. |
| Nhân viên | Quản lý sản phẩm, giá, size và tồn kho; xem tất cả đơn; xác nhận, giao, hoàn tất hoặc hủy đơn ở /staff/. Không được vào Django Admin hay cấp quyền. |
| Khách hàng | Đăng ký, đăng nhập, tìm kiếm/lọc/sắp xếp sản phẩm, chọn size, quản lý giỏ hàng, đặt hàng COD và xem đơn của chính mình. |

Khách vãng lai có thể xem sản phẩm và thêm giỏ; cần đăng nhập để đặt hàng.

Tạo admin bằng createsuperuser. Trong /admin/shop/user/, tạo tài khoản nhân viên với Role = Nhân viên, Active = bật, Staff status = tắt, Superuser status = tắt. Tài khoản này đăng nhập ở /login/ và dùng /staff/. Với admin bổ sung, dùng tài khoản superuser; trường role hiển thị có thể đặt Admin. Quyền quản trị Django được quyết định bởi is_staff, is_superuser và quyền Django, không tự động cấp qua trường role.

Không có tài khoản hay mật khẩu mặc định. Người tự đăng ký luôn nhận vai trò khách hàng.

### Nâng khách hàng thành nhân viên

Admin đăng nhập /admin/, chọn Users (Người dùng), đánh dấu tài khoản khách hàng đang hoạt động, chọn hành động **Nâng khách hàng thành nhân viên** rồi bấm Go/Thực hiện. Có thể chọn nhiều tài khoản cùng lúc. Nhân viên đăng nhập /login/ và sử dụng /staff/; thao tác này không cấp quyền truy cập Django Admin. Thay đổi được ghi lại trong nhật ký admin. Chỉ superuser được thêm, sửa, xóa hoặc phân quyền tài khoản.

## Quy tắc đơn hàng

- Giá được lấy từ máy chủ và lưu tại thời điểm mua; giao hàng miễn phí trong demo.
- Tồn kho theo từng size, được trừ trong giao dịch nguyên tử khi đặt đơn. Nếu một sản phẩm hết hàng, toàn bộ giao dịch được hoàn tác.
- Luồng: Chờ xác nhận → Đã xác nhận → Đang giao → Hoàn tất.
- Chỉ hủy ở trạng thái chờ xác nhận hoặc đã xác nhận. Khi hủy, hệ thống hoàn tồn kho đúng một lần.
- Tổng doanh thu tính trên đơn hoàn tất.
- Dùng trạng thái Đang bán để ẩn sản phẩm. Biến thể đã được đặt hàng được bảo vệ khỏi xóa để giữ lịch sử.

## Kiểm tra

```powershell
./.venv/Scripts/python.exe manage.py check
./.venv/Scripts/python.exe manage.py test
```

## Các chức năng hoàn thiện thêm

- Ảnh: vào Quản lý cửa hàng → Ảnh để tải nhiều ảnh JPEG/PNG/WebP, tối đa 5 MB mỗi ảnh. Ảnh đầu là ảnh bìa; trang chi tiết có thư viện chọn ảnh.
- Biến thể: mỗi tổ hợp màu–size có tồn kho riêng. Màu để trống dùng màu chung sản phẩm. Có thể thêm 4 biến thể mỗi lần sửa sản phẩm.
- Tài khoản: menu Tài khoản có hồ sơ, địa chỉ mặc định và đổi mật khẩu. Trang đăng nhập có Quên mật khẩu. Local ghi email reset vào terminal; cấu hình SMTP trước khi dùng email thật.
- Đơn hàng: xem chi tiết, địa chỉ, màu–size lúc mua, voucher, vận đơn và lịch sử trạng thái. Khách chỉ được hủy đơn của mình khi chờ xác nhận. Nhân viên tìm/lọc đơn và nhập mã vận đơn.
- Checkout: hiển thị từng sản phẩm và tổng tiền; dùng mã phiên duy nhất để lần gửi lại cùng đơn không trừ kho lần nữa.
- Quản lý: admin có trang Khách hàng & nhân viên để nâng/hạ vai trò. Nhật ký admin lưu thay đổi quyền. Nhân viên có trang lịch sử tồn kho; đặt hàng, hủy đơn và điều chỉnh kho được ghi nhận.
- Django Admin xem tồn kho ở chế độ chỉ đọc; chỉnh tồn kho qua trang quản lý shop để có nhật ký. Tồn kho và đơn cũ trước nâng cấp không có nhật ký hồi tố.

### Cấu hình gửi email

Đặt DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend và các biến EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS, DEFAULT_FROM_EMAIL theo nhà cung cấp SMTP. Giữ mật khẩu email ngoài mã nguồn.

### Trước khi bán hàng thật

Nhập ảnh, mô tả, size, giá, địa chỉ cửa hàng và chính sách thật. Bản này vẫn dùng COD và phí giao hàng 0; thanh toán ngân hàng, hãng vận chuyển và hoàn tiền cần cấu hình/tích hợp riêng. Không có thông tin merchant để tự triển khai VNPay/MoMo. Media cần được máy chủ web phục vụ riêng khi DEBUG=0. Chạy trên HTTPS, cấu hình secret, sao lưu cả db.sqlite3 và media; chuyển PostgreSQL và kiểm thử tải đồng thời trước khi vận hành nhiều người. Chưa có bộ giới hạn đăng nhập chuyên dụng.

## Giao diện và chức năng tham khảo 160STORE

Đã bổ sung menu danh mục, banner chuyển trang, voucher có nút sao chép, xem nhanh sản phẩm, chọn size và số lượng, mua ngay, lọc khoảng giá/size, phân trang, sản phẩm liên quan, đánh giá từ khách đã nhận hàng, đăng ký nhận tin, tin thời trang và trang hệ thống cửa hàng. Giữ thương hiệu MENSWEAR và dùng hình minh họa riêng.

Admin quản lý Coupons, Articles, Stores, Reviews và Subscribers tại /admin/. Các mã STYLE20, STYLE50, STYLE80, STYLE120 do seed_demo tạo; mã được kiểm tra và tính giảm tại máy chủ, lưu vào đơn. Chỉ áp dụng một mã trên mỗi đơn. Trang cửa hàng chưa có địa chỉ thực; admin cần nhập thông tin của shop. Đăng ký nhận tin lưu email, chưa tự gửi bản tin. Có thể dùng URL ảnh hoặc tải ảnh lên từ trang quản lý. Mỗi tổ hợp màu và size có tồn kho riêng. Giá gốc lớn hơn giá bán sẽ đưa sản phẩm vào Outlet.

Bản chạy local hỗ trợ COD, tải ảnh và khôi phục mật khẩu qua email (cần SMTP để gửi thực tế). Thanh toán trực tuyến, hãng vận chuyển và hoàn tiền chưa được tích hợp. Quản lý tồn kho qua /staff/ để lưu nhật ký.

Trước khi vận hành thật: đặt DJANGO_DEBUG=0, DJANGO_SECRET_KEY ngẫu nhiên và DJANGO_ALLOWED_HOSTS bằng tên miền; cấu hình HTTPS, máy chủ WSGI, collectstatic, sao lưu và cơ sở dữ liệu PostgreSQL. Không dùng runserver để phục vụ production. Nên bổ sung giới hạn số lần đăng nhập, ghi nhật ký thao tác nhân viên và kiểm thử tải đồng thời.
