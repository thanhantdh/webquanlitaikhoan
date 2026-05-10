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
| `/info TK01` | Chi tiết 1 TK |
| `/search facebook` | Tìm kiếm TK |
| `/run TK01` | Bắt đầu đếm giờ |
| `/stop TK01` | Dừng đếm giờ |
| `/runall` | Chạy tất cả |
| `/stopall` | Dừng tất cả |
| `/sethours TK01 12` | Đổi số giờ tối đa |
| `/rename TK_cu TK_moi` | Đổi tên TK |
| `/reset TK01` | Reset thời gian về 0 |
| `/delete TK01` | Xóa 1 TK |
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

## 6. Tự động

- ⏱ Timer cập nhật mỗi 5 giây
- 🚨 Thông báo **đúng khi hết giờ** (không cảnh báo sớm)
- 📊 Báo cáo hàng ngày lúc 8:00 sáng (UTC+7)
- 🔒 Chỉ OWNER_ID mới dùng được bot

## 7. Deploy (Render.com)

1. Push lên GitHub: `bot.py` + `requirements.txt`
2. Vào render.com → New → Background Worker
3. Build: `pip install -r requirements.txt`
4. Start: `python bot.py`
5. Env vars: `BOT_TOKEN`, `OWNER_ID`
