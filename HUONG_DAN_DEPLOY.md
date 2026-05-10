# 📘 Hướng Dẫn Deploy Website Lên GitHub Pages (Miễn Phí)

## Mục Lục
1. [Chuẩn Bị](#1-chuẩn-bị)
2. [Tạo Repository trên GitHub](#2-tạo-repository-trên-github)
3. [Upload Code lên GitHub](#3-upload-code-lên-github)
4. [Bật GitHub Pages](#4-bật-github-pages)
5. [Cấu Hình Telegram Bot](#5-cấu-hình-telegram-bot)
6. [Kiểm Tra Website](#6-kiểm-tra-website)
7. [Cập Nhật Website](#7-cập-nhật-website)
8. [FAQ & Xử Lý Lỗi](#8-faq--xử-lý-lỗi)

---

## 1. Chuẩn Bị

### Tài khoản cần có:
- ✅ **Tài khoản GitHub** — Đăng ký miễn phí tại [github.com](https://github.com)
- ✅ **Tài khoản Telegram** — Để tạo Bot

### Cài đặt (tùy chọn — nếu dùng Git):
- [Git](https://git-scm.com/downloads) — Để push code bằng dòng lệnh

### File cần deploy (chỉ 3 file):
```
webquanlytaikhoan/
├── index.html    ← Giao diện chính
├── style.css     ← CSS styling
└── app.js        ← Logic JavaScript
```

> ⚠️ **Lưu ý:** File `server.py` và `requirements.txt` KHÔNG cần deploy lên GitHub Pages.
> Website đã được tối ưu để gọi trực tiếp Telegram API từ JavaScript, không cần backend.

---

## 2. Tạo Repository Trên GitHub

### Bước 1: Đăng nhập GitHub
Truy cập [github.com](https://github.com) và đăng nhập.

### Bước 2: Tạo Repository mới
1. Click nút **"+"** ở góc phải trên → **"New repository"**
2. Điền thông tin:
   - **Repository name:** `account-manager` (hoặc tên bạn muốn)
   - **Description:** `Hệ thống quản lý tài khoản với thông báo Telegram`
   - **Visibility:** chọn **Public** (bắt buộc cho GitHub Pages miễn phí)
   - ✅ Tích **"Add a README file"**
3. Click **"Create repository"**

---

## 3. Upload Code Lên GitHub

### Cách 1: Upload trực tiếp qua giao diện web (Đơn giản nhất)

1. Vào repository vừa tạo
2. Click nút **"Add file"** → **"Upload files"**
3. Kéo thả 3 file vào:
   - `index.html`
   - `style.css`
   - `app.js`
4. Ở mục **"Commit changes"**, ghi: `Upload website files`
5. Click **"Commit changes"**

### Cách 2: Dùng Git (Cho người quen dòng lệnh)

Mở Terminal/PowerShell trong thư mục `webquanlytaikhoan`:

```bash
# Khởi tạo Git
git init

# Thêm remote (thay YOUR_USERNAME bằng tên GitHub của bạn)
git remote add origin https://github.com/YOUR_USERNAME/account-manager.git

# Thêm files
git add index.html style.css app.js

# Commit
git commit -m "Upload website quản lý tài khoản"

# Push lên GitHub
git branch -M main
git push -u origin main
```

---

## 4. Bật GitHub Pages

### Bước 1: Vào Settings
1. Trong repository, click tab **"Settings"** (biểu tượng bánh răng)
2. Ở menu bên trái, click **"Pages"**

### Bước 2: Cấu hình Source
1. Tại mục **"Source"**, chọn:
   - **Source:** `Deploy from a branch`
   - **Branch:** `main`
   - **Folder:** `/ (root)`
2. Click **"Save"**

### Bước 3: Chờ Deploy
- GitHub sẽ tự động build và deploy
- Sau 1-3 phút, refresh trang Settings → Pages
- Bạn sẽ thấy URL:
  ```
  ✅ Your site is live at https://YOUR_USERNAME.github.io/account-manager/
  ```

### Bước 4: Truy cập website
- Mở link trên trong trình duyệt
- Website đã sẵn sàng sử dụng! 🎉

---

## 5. Cấu Hình Telegram Bot

### Bước 1: Tạo Bot trên Telegram

1. Mở Telegram, tìm **@BotFather**
2. Gửi lệnh: `/newbot`
3. Đặt tên cho bot: `Account Manager Bot` (hoặc tên khác)
4. Đặt username: `acc_manager_xyz_bot` (phải kết thúc bằng `_bot`)
5. BotFather sẽ gửi cho bạn **Bot Token**, ví dụ:
   ```
   7123456789:AAH1234567890abcdefghijklmnopqrstuv
   ```
6. **Copy Token này**

### Bước 2: Lấy Chat ID

**Cách A: Chat riêng**
1. Gửi tin nhắn bất kỳ cho bot
2. Truy cập URL (thay TOKEN bằng token vừa nhận):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. Tìm trường `"chat":{"id": 123456789}` → đây là Chat ID

**Cách B: Group chat**
1. Thêm bot vào group
2. Gửi tin nhắn bất kỳ trong group
3. Truy cập URL `getUpdates` như trên
4. Tìm Chat ID (thường bắt đầu bằng `-100...`)

### Bước 3: Nhập vào Website

1. Truy cập website đã deploy
2. Click **"Cài đặt"** trong sidebar
3. Nhập **Bot Token** và **Chat ID**
4. Click **"Lưu cài đặt"**
5. Click **"Gửi tin nhắn test"** để kiểm tra

> ✅ Nếu nhận được tin nhắn test trên Telegram → Cấu hình thành công!

---

## 6. Kiểm Tra Website

### Checklist sau khi deploy:

- [ ] Truy cập URL GitHub Pages → Website hiển thị đúng
- [ ] Thêm tài khoản thủ công → Hiển thị trong bảng
- [ ] Upload file .txt → Import nhiều tài khoản
- [ ] Bấm "Bắt đầu" → Timer đếm realtime
- [ ] Vào "Cài đặt" → Nhập Telegram config
- [ ] Bấm "Gửi tin nhắn test" → Nhận tin trên Telegram
- [ ] Vào "Thông báo" → Xem lịch sử cảnh báo

### Tạo file test để upload:

Tạo file `test_accounts.txt` với nội dung:
```
TaiKhoan_01
TaiKhoan_02,2
TaiKhoan_03,4.5
TaiKhoan_04
TaiKhoan_05,1
```

Format: mỗi dòng là `tên` hoặc `tên,số_giờ`

---

## 7. Cập Nhật Website

Khi muốn sửa code:

### Cách 1: Trực tiếp trên GitHub
1. Vào repository
2. Click vào file cần sửa (ví dụ `index.html`)
3. Click biểu tượng ✏️ (Edit)
4. Sửa code
5. Click **"Commit changes"**
6. GitHub Pages tự động re-deploy sau 1-2 phút

### Cách 2: Dùng Git
```bash
# Sửa file trên máy local
# Sau đó:
git add .
git commit -m "Cập nhật giao diện"
git push
```

---

## 8. FAQ & Xử Lý Lỗi

### ❓ Website hiện trang trắng?
- Kiểm tra file `index.html` đã ở **thư mục gốc** (root) của repository
- Không được đặt trong subfolder

### ❓ CSS/JS không load?
- Kiểm tra tên file đúng chính xác: `style.css` và `app.js`
- Tên file phân biệt chữ HOA/thường

### ❓ Telegram không gửi được?
- Kiểm tra Bot Token không có khoảng trắng thừa
- Chat ID phải là số (có thể có dấu `-` ở đầu cho group)
- Bot phải được **thêm vào group** trước khi gửi được tin nhắn vào group

### ❓ Dữ liệu mất khi đổi máy?
- Dữ liệu lưu trong localStorage của trình duyệt
- Mỗi máy/trình duyệt sẽ có dữ liệu riêng
- Dùng nút **"Xuất dữ liệu (JSON)"** trong Cài đặt để backup

### ❓ GitHub Pages có giới hạn gì?
- Miễn phí cho repository Public
- Bandwidth: 100GB/tháng
- Giới hạn file: 100MB/file
- Website tĩnh (HTML/CSS/JS) — không chạy backend

### ❓ Muốn dùng tên miền riêng?
1. Mua domain (ví dụ: Namecheap, GoDaddy)
2. Vào Settings → Pages → **Custom domain**
3. Nhập domain của bạn
4. Cấu hình DNS (CNAME hoặc A record) theo hướng dẫn GitHub

---

## 📋 Tóm Tắt Nhanh

```
1. Tạo repo GitHub (Public)
2. Upload 3 file: index.html, style.css, app.js
3. Settings → Pages → Branch: main → Save
4. Chờ 1-3 phút → Website live!
5. Vào Cài đặt → Nhập Telegram Bot Token + Chat ID
6. Done! ✅
```

**Link website của bạn:**
```
https://YOUR_USERNAME.github.io/account-manager/
```
