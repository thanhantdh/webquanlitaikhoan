# 🤖 Hướng Dẫn Bot Telegram Quản Lý Tài Khoản

## 1. Cài đặt

```bash
# Cài Python 3.10+ từ python.org (tick "Add to PATH")
# Cài thư viện:
python -m pip install -r requirements.txt
```

## 2. Cấu hình

Mở `bot.py`, sửa dòng 18-19:
```python
BOT_TOKEN = "TOKEN_TỪ_BOTFATHER"
OWNER_ID = CHAT_ID_CỦA_BẠN
```

## 3. Chạy bot

```bash
python bot.py
```

## 4. Tất cả lệnh

| Lệnh | Mô tả |
|-------|--------|
| `/start` | Menu chính |
| `/add TK01 8` | Thêm TK, thời hạn 8 giờ |
| `/addmulti TK1 TK2 TK3 8` | Thêm nhiều TK cùng lúc |
| `/list` | Xem danh sách + nút bấm |
| `/info Tên_hoặc_STT` | Chi tiết 1 TK |
| `/search facebook` | Tìm kiếm TK |
| `/run Tên_hoặc_STT` | Bắt đầu đếm giờ |
| `/stop Tên_hoặc_STT` | Dừng đếm giờ |
| `/runall` | Chạy tất cả |
| `/stopall` | Dừng tất cả |
| `/sethours Tên_hoặc_STT 12` | Đổi số giờ tối đa |
| `/rename Tên_hoặc_STT TK_moi` | Đổi tên TK |
| `/reset Tên_hoặc_STT` | Reset thời gian về 0 |
| `/delete Tên_hoặc_STT` | Xóa 1 TK |
| `/deleteall` | Xóa tất cả (có xác nhận) |
| `/export` | Xuất file .txt danh sách |
| `/import` | Hướng dẫn import file |
| `/status` | Thống kê tổng quan |
| `/help` | Xem trợ giúp |

## 5. Import file

Gửi file `.txt` trực tiếp vào chat:
```
TaiKhoan01
TaiKhoan02,4
TaiKhoan03,2.5
```

## 6. Tính năng Tự động & Tiện ích

- ⏱ **Cập nhật thời gian:** Timer quét mỗi 5 giây.
- ⚠️ **Cảnh báo sớm:** Nhắn tin thông báo trước 15 phút khi tài khoản sắp hết giờ.
- 🚨 **Hết giờ:** Tự động dừng và gửi thông báo khi tài khoản chạm mốc 0.
- 📑 **Phân trang danh sách:** Lệnh `/list` tự động chia thành nhiều trang (10 TK/trang) nếu số lượng lớn.
- 🔢 **Hỗ trợ Số Thứ Tự (STT):** Có thể dùng STT trong `/list` thay cho tên tài khoản ở mọi lệnh (vd: `/run 1`).
- 📊 **Báo cáo hàng ngày:** Tự động gửi lúc 8:00 sáng (UTC+7).
- 🔒 **Bảo mật:** Chỉ OWNER_ID mới dùng được bot.

## 7. Deploy (Render.com)

1. Push lên GitHub: `bot.py` + `requirements.txt`
2. Vào render.com → New → Background Worker
3. Build: `pip install -r requirements.txt`
4. Start: `python bot.py`
5. Env vars: `BOT_TOKEN`, `OWNER_ID`
