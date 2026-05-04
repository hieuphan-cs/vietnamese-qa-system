1.Hướng dẫn cài đặt và khởi chạy
Hệ thống đã được đóng gói hoàn toàn bằng Docker. Thầy/Cô chỉ cần thực hiện 1 lệnh duy nhất:
    1. Mở Terminal tại thư mục gốc của dự án.
    2. Chạy lệnh: `docker-compose up`
    3. Chờ khoảng 2-3 phút để các container (Frontend, Backend, Database) khởi động.

Các đường dẫn truy cập:
    Ứng dụng web: http://localhost:5173/
    PhPmyadmin: http://localhost:8081/
    Django: http://localhost:8000/admin/

2.Tài khoản test

Cách 1: Sử dụng tài khoản Superadmin
  - Admin: Email: `admin@gmail.com` | Pass: `admin123`

Cách 2: Nếu Thầy dùng Google Auth để đăng nhập tài khoản mới
  1. Đăng nhập bằng tài khoản Google bất kỳ.
  2. Truy cập phpMyAdmin tại http://localhost:8081/, Thầy hãy đăng nhập tài khoản PhPmyadmin bên dưới
  3. Mở bảng `users_user`, tìm email Thầy vừa đăng nhập và đổi cột `role` thành `ADMIN`.
  4. F5 lại trang web để nhận quyền Quản trị viên.

PhPmyadmin:
    username: root
    password: Ahihihi@123

Link Demo:
https://youtu.be/TGYFavDg760