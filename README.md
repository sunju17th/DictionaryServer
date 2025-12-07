# 📚 TỪ ĐIỂN TRỰC TUYẾN (Client-Server)

Một dự án mẫu cho môn Lập trình Mạng: hệ thống từ điển Anh–Việt hoạt động theo mô hình Client–Server, hỗ trợ phân quyền (User / Admin), giao diện Tkinter cho client và lưu trữ bằng file JSON.

---

## 🔖 Mục Lục
- **Giới thiệu**
- **Tính năng chính**
- **Kiến trúc & Công nghệ**
- **Cài đặt & Chạy thử (Windows / PowerShell)**
- **Tài khoản mẫu**
- **Hướng phát triển**

---

## 1. Giới thiệu
Dự án xây dựng một hệ thống từ điển hoạt động theo mô hình Client–Server. Nhiều client có thể kết nối đồng thời tới server để tra cứu, gửi yêu cầu thêm/sửa từ (yêu cầu được lưu vào hàng đợi `pending.json` và cần admin duyệt).

## 2. Tính năng chính
- Tra cứu từ (User & Admin)
- Gửi yêu cầu THÊM / SỬA (User → vào hàng đợi pending)
- Duyệt / Từ chối yêu cầu (Admin)
- Lưu trữ dữ liệu bền vững bằng JSON (`dictionary.json`, `pending.json`)
- Hỗ trợ đa kết nối (multithreading) và khóa (Locks) để tránh xung đột ghi file

## 3. Kiến trúc & Công nghệ
- Ngôn ngữ: Python 3.x
- Giao thức: TCP socket (custom text protocol: `LOGIN`, `TRA`, `THEM`, `SUA`, `LIST`, `PENDING`, `APPROVE`, `REJECT`, `QUIT`)
- Giao diện client: Tkinter (tabs, Treeview)
- Lưu trữ: JSON files (`dictionary.json`, `pending.json`)

---

## 4. Cài đặt & Chạy thử (Windows / PowerShell)
Yêu cầu: Python 3.6+ đã cài.

1) Mở PowerShell, di chuyển đến thư mục dự án:

```
cd D:\\BT_LAP_TRINH_MANG\\DoAnCuoiKi
```

2) Chạy server:

```
python .\\server_auth.py
```

Server sẽ tạo `dictionary.json` và `pending.json` nếu chưa tồn tại và bắt đầu lắng nghe trên `localhost:5555`.

3) Chạy client (có thể mở nhiều cửa sổ để thử user/admin đồng thời):

```
python .\\client_gui.py
```

4) Đăng nhập từ giao diện client bằng tài khoản mẫu (dưới mục **Tài khoản mẫu**).

---

## 5. Tài khoản mẫu (dùng để demo)
- `admin` / `admin123` → role: Admin (duyệt yêu cầu)
- `user1` / `user123` → role: User (tra cứu, gửi yêu cầu)
- `user2` / `user123` → role: User

Lưu ý: Trong bản mẫu này mật khẩu lưu dạng plaintext — nên hash khi đưa vào thực tế.

---


## 6. Giao thức nhanh (tổng quan)
- `LOGIN|username|password` → trả về `SUCCESS|role|message` hoặc `ERROR|message`
- `TRA|word` → tra từ
- `THEM|word:meaning` → yêu cầu thêm (User)
- `SUA|word:meaning` → yêu cầu sửa (User)
- `LIST` → lấy toàn bộ từ dưới dạng JSON (LIST_DATA|...)
- `PENDING` → (Admin) lấy danh sách chờ
- `APPROVE|id` / `REJECT|id` → (Admin) duyệt/từ chối

---


