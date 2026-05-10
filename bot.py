"""
Telegram Bot Quản Lý Tài Khoản & Thời Hạn Giờ
Python 3.10+ | python-telegram-bot v21+
"""
import sqlite3
import logging
import os
import io
from datetime import datetime, time as dtime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ============================================================
# ⚠️  CẤU HÌNH — Thay đổi 2 giá trị bên dưới
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8786343416:AAHMrHFPKovkmUQzQzp49IPjyIluEDeskvQ")
OWNER_ID = int(os.getenv("OWNER_ID", "6100618600"))  # Chat ID của bạn
DEFAULT_HOURS = 8
DB_FILE = "accounts.db"
TIMER_INTERVAL = 5  # Cập nhật mỗi 5 giây
# ============================================================

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== DATABASE ====================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            max_hours REAL NOT NULL DEFAULT 8,
            elapsed INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'stopped',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def db_exec(sql, params=()):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(sql, params)
    conn.commit()
    rows = cur.fetchall()
    conn.close()
    return rows

def get_all_accounts():
    return db_exec("SELECT * FROM accounts ORDER BY id")

def get_account(name):
    rows = db_exec("SELECT * FROM accounts WHERE LOWER(name)=LOWER(?)", (name,))
    return rows[0] if rows else None

def add_account(name, hours):
    db_exec("INSERT INTO accounts (name, max_hours, created_at) VALUES (?,?,?)",
            (name, hours, datetime.now().isoformat()))

def update_status(name, status):
    db_exec("UPDATE accounts SET status=? WHERE LOWER(name)=LOWER(?)", (status, name))

def update_elapsed(name, elapsed):
    db_exec("UPDATE accounts SET elapsed=?, status=CASE WHEN ?>=max_hours*3600 THEN 'expired' ELSE status END WHERE LOWER(name)=LOWER(?)",
            (elapsed, elapsed, name))

def reset_account(name):
    db_exec("UPDATE accounts SET elapsed=0, status='stopped' WHERE LOWER(name)=LOWER(?)", (name,))

def delete_account(name):
    db_exec("DELETE FROM accounts WHERE LOWER(name)=LOWER(?)", (name,))

def delete_all_accounts():
    db_exec("DELETE FROM accounts")

def set_hours(name, hours):
    db_exec("UPDATE accounts SET max_hours=? WHERE LOWER(name)=LOWER(?)", (hours, name))

def rename_db(old, new):
    db_exec("UPDATE accounts SET name=? WHERE LOWER(name)=LOWER(?)", (new, old))

def search_accounts(keyword):
    return db_exec("SELECT * FROM accounts WHERE LOWER(name) LIKE LOWER(?)", (f"%{keyword}%",))

def get_stats():
    rows = db_exec("SELECT status, COUNT(*) as cnt FROM accounts GROUP BY status")
    stats = {"running": 0, "stopped": 0, "expired": 0}
    for r in rows:
        stats[r["status"]] = r["cnt"]
    stats["total"] = sum(stats.values())
    return stats

# ==================== HELPERS ====================

def fmt_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def owner_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if OWNER_ID != 0 and uid != OWNER_ID:
            await update.effective_message.reply_text("⛔ Bot này chỉ dành cho chủ sở hữu.")
            return
        return await func(update, context)
    return wrapper

def progress_bar(pct, length=10):
    filled = int(pct / 100 * length)
    return "█" * filled + "░" * (length - filled)

# ==================== COMMANDS ====================

@owner_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("📋 Danh sách", callback_data="list"),
         InlineKeyboardButton("➕ Hướng dẫn thêm", callback_data="help_add")],
        [InlineKeyboardButton("📊 Thống kê", callback_data="status"),
         InlineKeyboardButton("❓ Trợ giúp", callback_data="help")]
    ]
    await update.message.reply_text(
        "🤖 <b>Account Manager Bot</b>\n\n"
        "Quản lý tài khoản & thời hạn giờ cá nhân.\n"
        "Chọn chức năng bên dưới hoặc gõ /help",
        parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb)
    )

@owner_only
async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "📌 <b>Cách dùng:</b>\n<code>/add TenTK SoGio</code>\n\n"
            "Ví dụ:\n<code>/add Facebook 8</code>\n<code>/add TikTok 2.5</code>",
            parse_mode="HTML")
        return
    name = args[0]
    hours = float(args[1]) if len(args) > 1 else DEFAULT_HOURS
    if get_account(name):
        await update.message.reply_text(f"⚠️ Tài khoản <b>{name}</b> đã tồn tại!", parse_mode="HTML")
        return
    add_account(name, hours)
    await update.message.reply_text(
        f"✅ Đã thêm <b>{name}</b> — Thời hạn: <b>{hours}h</b>", parse_mode="HTML")

@owner_only
async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_account_list(update.effective_chat.id, context)

async def send_account_list(chat_id, context, edit_msg_id=None):
    accs = get_all_accounts()
    if not accs:
        text = "📭 Chưa có tài khoản nào.\nDùng /add <tên> <giờ> để thêm."
        if edit_msg_id:
            await context.bot.edit_message_text(text, chat_id=chat_id, message_id=edit_msg_id)
        else:
            await context.bot.send_message(chat_id, text)
        return

    lines = ["📋 <b>Danh Sách Tài Khoản</b>\n"]
    buttons = []
    for i, a in enumerate(accs):
        max_sec = int(a["max_hours"] * 3600)
        pct = min(a["elapsed"] / max_sec * 100, 100) if max_sec > 0 else 0
        icons = {"running": "🟢", "stopped": "⏸", "expired": "🔴"}
        icon = icons.get(a["status"], "⏸")
        bar = progress_bar(pct)
        lines.append(
            f"{i+1}. <b>{a['name']}</b> {icon}\n"
            f"   ⏱ {fmt_time(a['elapsed'])} / {a['max_hours']}h ({pct:.0f}%)\n"
            f"   {bar}"
        )
        # Buttons per account
        n = a["name"]
        if a["status"] == "running":
            row = [InlineKeyboardButton(f"⏸ {n}", callback_data=f"stop_{n}"),
                   InlineKeyboardButton(f"🗑", callback_data=f"del_{n}")]
        elif a["status"] == "expired":
            row = [InlineKeyboardButton(f"↺ Reset {n}", callback_data=f"reset_{n}"),
                   InlineKeyboardButton(f"🗑", callback_data=f"del_{n}")]
        else:
            row = [InlineKeyboardButton(f"▶ {n}", callback_data=f"run_{n}"),
                   InlineKeyboardButton(f"🗑", callback_data=f"del_{n}")]
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton("▶ Chạy tất cả", callback_data="runall"),
        InlineKeyboardButton("⏸ Dừng tất cả", callback_data="stopall")
    ])
    buttons.append([InlineKeyboardButton("🔄 Làm mới", callback_data="list")])

    text = "\n".join(lines)
    markup = InlineKeyboardMarkup(buttons)

    if edit_msg_id:
        try:
            await context.bot.edit_message_text(
                text, chat_id=chat_id, message_id=edit_msg_id,
                parse_mode="HTML", reply_markup=markup)
        except Exception:
            await context.bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
    else:
        await context.bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

@owner_only
async def cmd_run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📌 Dùng: <code>/run TenTK</code>", parse_mode="HTML")
        return
    name = context.args[0]
    acc = get_account(name)
    if not acc:
        await update.message.reply_text(f"❌ Không tìm thấy <b>{name}</b>", parse_mode="HTML")
        return
    if acc["status"] == "expired":
        await update.message.reply_text(f"🔴 <b>{name}</b> đã hết giờ. Dùng /reset {name} trước.", parse_mode="HTML")
        return
    update_status(name, "running")
    await update.message.reply_text(f"▶ <b>{name}</b> đang chạy...", parse_mode="HTML")

@owner_only
async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📌 Dùng: <code>/stop TenTK</code>", parse_mode="HTML")
        return
    name = context.args[0]
    acc = get_account(name)
    if not acc:
        await update.message.reply_text(f"❌ Không tìm thấy <b>{name}</b>", parse_mode="HTML")
        return
    update_status(name, "stopped")
    await update.message.reply_text(
        f"⏸ <b>{name}</b> đã dừng — Đã chạy: {fmt_time(acc['elapsed'])}", parse_mode="HTML")

@owner_only
async def cmd_runall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_exec("UPDATE accounts SET status='running' WHERE status='stopped'")
    await update.message.reply_text("▶ Tất cả tài khoản đã bắt đầu chạy!")

@owner_only
async def cmd_stopall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_exec("UPDATE accounts SET status='stopped' WHERE status='running'")
    await update.message.reply_text("⏸ Tất cả tài khoản đã dừng!")

@owner_only
async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📌 Dùng: <code>/delete TenTK</code>", parse_mode="HTML")
        return
    name = context.args[0]
    if not get_account(name):
        await update.message.reply_text(f"❌ Không tìm thấy <b>{name}</b>", parse_mode="HTML")
        return
    delete_account(name)
    await update.message.reply_text(f"🗑 Đã xóa <b>{name}</b>", parse_mode="HTML")

@owner_only
async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📌 Dùng: <code>/reset TenTK</code>", parse_mode="HTML")
        return
    name = context.args[0]
    if not get_account(name):
        await update.message.reply_text(f"❌ Không tìm thấy <b>{name}</b>", parse_mode="HTML")
        return
    reset_account(name)
    await update.message.reply_text(f"↺ Đã reset <b>{name}</b> về 00:00:00", parse_mode="HTML")

@owner_only
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_status(update.effective_chat.id, context)

async def send_status(chat_id, context, edit_msg_id=None):
    s = get_stats()
    text = (
        "📊 <b>Thống Kê Hệ Thống</b>\n\n"
        f"📦 Tổng tài khoản: <b>{s['total']}</b>\n"
        f"🟢 Đang chạy: <b>{s['running']}</b>\n"
        f"⏸ Đã dừng: <b>{s['stopped']}</b>\n"
        f"🔴 Hết giờ: <b>{s['expired']}</b>"
    )
    if edit_msg_id:
        try:
            await context.bot.edit_message_text(text, chat_id=chat_id, message_id=edit_msg_id, parse_mode="HTML")
        except Exception:
            await context.bot.send_message(chat_id, text, parse_mode="HTML")
    else:
        await context.bot.send_message(chat_id, text, parse_mode="HTML")

@owner_only
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML")

HELP_TEXT = (
    "❓ <b>Danh sách lệnh</b>\n\n"
    "<b>📋 Quản lý:</b>\n"
    "/add <code>tên giờ</code> — Thêm tài khoản\n"
    "/addmulti <code>tên1 tên2 giờ</code> — Thêm nhiều TK\n"
    "/list — Danh sách tài khoản\n"
    "/info <code>tên</code> — Chi tiết 1 TK\n"
    "/search <code>từ_khóa</code> — Tìm kiếm\n\n"
    "<b>⏱ Điều khiển:</b>\n"
    "/run <code>tên</code> — Bắt đầu đếm giờ\n"
    "/stop <code>tên</code> — Dừng đếm giờ\n"
    "/runall · /stopall — Chạy/Dừng tất cả\n\n"
    "<b>⚙️ Cài đặt:</b>\n"
    "/sethours <code>tên giờ</code> — Đổi số giờ\n"
    "/rename <code>tên_cũ tên_mới</code> — Đổi tên\n"
    "/reset <code>tên</code> — Reset thời gian\n"
    "/delete <code>tên</code> · /deleteall — Xóa\n\n"
    "<b>📊 Khác:</b>\n"
    "/status — Thống kê\n"
    "/export — Xuất file .txt\n"
    "/import — Import file\n"
    "/help — Trợ giúp"
)

@owner_only
async def cmd_import(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📁 <b>Import tài khoản từ file</b>\n\n"
        "Gửi file <code>.txt</code> hoặc <code>.csv</code> vào chat.\n\n"
        "Format mỗi dòng:\n"
        "<code>TenTaiKhoan</code>\n"
        "<code>TenTaiKhoan,SoGio</code>\n\n"
        "Ví dụ:\n<code>Facebook\nInstagram,4\nTikTok,2.5</code>",
        parse_mode="HTML"
    )

# ==================== NEW COMMANDS ====================

@owner_only
async def cmd_sethours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("📌 Dùng: <code>/sethours TenTK SoGio</code>", parse_mode="HTML")
        return
    name, hours = context.args[0], float(context.args[1])
    if not get_account(name):
        await update.message.reply_text(f"❌ Không tìm thấy <b>{name}</b>", parse_mode="HTML")
        return
    set_hours(name, hours)
    await update.message.reply_text(f"✅ Đã đổi <b>{name}</b> → <b>{hours}h</b>", parse_mode="HTML")

@owner_only
async def cmd_rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("📌 Dùng: <code>/rename TenCu TenMoi</code>", parse_mode="HTML")
        return
    old, new = context.args[0], context.args[1]
    if not get_account(old):
        await update.message.reply_text(f"❌ Không tìm thấy <b>{old}</b>", parse_mode="HTML")
        return
    if get_account(new):
        await update.message.reply_text(f"⚠️ <b>{new}</b> đã tồn tại!", parse_mode="HTML")
        return
    rename_db(old, new)
    await update.message.reply_text(f"✅ Đổi tên <b>{old}</b> → <b>{new}</b>", parse_mode="HTML")

@owner_only
async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📌 Dùng: <code>/info TenTK</code>", parse_mode="HTML")
        return
    acc = get_account(context.args[0])
    if not acc:
        await update.message.reply_text(f"❌ Không tìm thấy <b>{context.args[0]}</b>", parse_mode="HTML")
        return
    max_sec = int(acc['max_hours'] * 3600)
    pct = min(acc['elapsed'] / max_sec * 100, 100) if max_sec > 0 else 0
    remaining = max(max_sec - acc['elapsed'], 0)
    icons = {'running': '🟢 Đang chạy', 'stopped': '⏸ Đã dừng', 'expired': '🔴 Hết giờ'}
    await update.message.reply_text(
        f"📄 <b>Chi tiết: {acc['name']}</b>\n\n"
        f"Trạng thái: {icons.get(acc['status'], acc['status'])}\n"
        f"Đã chạy: <b>{fmt_time(acc['elapsed'])}</b>\n"
        f"Thời hạn: <b>{acc['max_hours']}h</b>\n"
        f"Còn lại: <b>{fmt_time(remaining)}</b>\n"
        f"Tiến trình: {progress_bar(pct)} {pct:.1f}%\n"
        f"Tạo lúc: {acc['created_at'][:16]}",
        parse_mode="HTML"
    )

@owner_only
async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📌 Dùng: <code>/search từ_khóa</code>", parse_mode="HTML")
        return
    results = search_accounts(context.args[0])
    if not results:
        await update.message.reply_text(f"🔍 Không tìm thấy kết quả cho <b>{context.args[0]}</b>", parse_mode="HTML")
        return
    lines = [f"🔍 Tìm thấy <b>{len(results)}</b> kết quả:\n"]
    for a in results:
        icons = {'running': '🟢', 'stopped': '⏸', 'expired': '🔴'}
        lines.append(f"{icons.get(a['status'],'⏸')} <b>{a['name']}</b> — {fmt_time(a['elapsed'])}/{a['max_hours']}h")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

@owner_only
async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accs = get_all_accounts()
    if not accs:
        await update.message.reply_text("📭 Chưa có tài khoản nào.")
        return
    lines = ["# Danh sách tài khoản - Exported"]
    for a in accs:
        lines.append(f"{a['name']},{a['max_hours']},{a['status']},{fmt_time(a['elapsed'])}")
    buf = io.BytesIO("\n".join(lines).encode('utf-8'))
    buf.name = f"accounts_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    await update.message.reply_document(buf, caption=f"📁 Xuất {len(accs)} tài khoản")

@owner_only
async def cmd_deleteall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accs = get_all_accounts()
    if not accs:
        await update.message.reply_text("📭 Không có TK nào để xóa.")
        return
    kb = [[InlineKeyboardButton("✅ Xác nhận xóa tất cả", callback_data="confirm_deleteall"),
           InlineKeyboardButton("❌ Hủy", callback_data="list")]]
    await update.message.reply_text(
        f"⚠️ Bạn có chắc muốn xóa <b>{len(accs)}</b> tài khoản?",
        parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

@owner_only
async def cmd_addmulti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "📌 Dùng: <code>/addmulti TK1 TK2 TK3 SoGio</code>\n"
            "Số cuối cùng là số giờ chung.", parse_mode="HTML")
        return
    try:
        hours = float(args[-1])
        names = args[:-1]
    except ValueError:
        hours = DEFAULT_HOURS
        names = args
    added, skipped = 0, 0
    for n in names:
        if get_account(n):
            skipped += 1
        else:
            try:
                add_account(n, hours)
                added += 1
            except Exception:
                skipped += 1
    await update.message.reply_text(
        f"✅ Thêm <b>{added}</b> TK ({hours}h)\n⏭ Bỏ qua: {skipped}", parse_mode="HTML")

# ==================== FILE HANDLER ====================

@owner_only
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        return
    fname = doc.file_name.lower()
    if not fname.endswith((".txt", ".csv")):
        await update.message.reply_text("⚠️ Chỉ hỗ trợ file .txt hoặc .csv")
        return

    file = await doc.get_file()
    content = (await file.download_as_bytearray()).decode("utf-8")
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]

    added, skipped = 0, 0
    for line in lines:
        parts = [p.strip() for p in line.replace(";", ",").split(",")]
        name = parts[0]
        hours = float(parts[1]) if len(parts) > 1 and parts[1] else DEFAULT_HOURS
        if not name:
            continue
        if get_account(name):
            skipped += 1
            continue
        try:
            add_account(name, hours)
            added += 1
        except Exception:
            skipped += 1

    await update.message.reply_text(
        f"📁 <b>Import hoàn tất</b>\n\n"
        f"✅ Đã thêm: <b>{added}</b>\n"
        f"⏭ Bỏ qua (trùng): <b>{skipped}</b>",
        parse_mode="HTML"
    )

# ==================== CALLBACK (INLINE BUTTONS) ====================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    if OWNER_ID != 0 and uid != OWNER_ID:
        return

    data = query.data
    chat_id = query.message.chat_id
    msg_id = query.message.message_id

    if data == "list":
        await send_account_list(chat_id, context, edit_msg_id=msg_id)
    elif data == "status":
        await send_status(chat_id, context, edit_msg_id=msg_id)
    elif data == "help" or data == "help_add":
        try:
            await query.edit_message_text(HELP_TEXT, parse_mode="HTML")
        except Exception:
            await context.bot.send_message(chat_id, HELP_TEXT, parse_mode="HTML")
    elif data.startswith("run_"):
        name = data[4:]
        acc = get_account(name)
        if acc and acc["status"] != "expired":
            update_status(name, "running")
        await send_account_list(chat_id, context, edit_msg_id=msg_id)
    elif data.startswith("stop_"):
        name = data[5:]
        update_status(name, "stopped")
        await send_account_list(chat_id, context, edit_msg_id=msg_id)
    elif data.startswith("reset_"):
        name = data[6:]
        reset_account(name)
        await send_account_list(chat_id, context, edit_msg_id=msg_id)
    elif data.startswith("del_"):
        name = data[4:]
        delete_account(name)
        await send_account_list(chat_id, context, edit_msg_id=msg_id)
    elif data == "runall":
        db_exec("UPDATE accounts SET status='running' WHERE status='stopped'")
        await send_account_list(chat_id, context, edit_msg_id=msg_id)
    elif data == "stopall":
        db_exec("UPDATE accounts SET status='stopped' WHERE status='running'")
        await send_account_list(chat_id, context, edit_msg_id=msg_id)
    elif data == "confirm_deleteall":
        delete_all_accounts()
        await query.edit_message_text("🗑 Đã xóa tất cả tài khoản!")

# ==================== TIMER (JOBQUEUE) ====================

async def timer_tick(context: ContextTypes.DEFAULT_TYPE):
    """Runs every TIMER_INTERVAL seconds — updates elapsed time for running accounts."""
    accs = db_exec("SELECT * FROM accounts WHERE status='running'")
    if not accs:
        return

    for a in accs:
        new_elapsed = a["elapsed"] + TIMER_INTERVAL
        max_sec = int(a["max_hours"] * 3600)

        if new_elapsed >= max_sec:
            # Account expired
            new_elapsed = max_sec
            db_exec("UPDATE accounts SET elapsed=?, status='expired' WHERE id=?",
                    (new_elapsed, a["id"]))
            # Send alert
            chat_id = OWNER_ID if OWNER_ID != 0 else None
            if chat_id:
                await context.bot.send_message(
                    chat_id,
                    f"🚨 <b>Cảnh báo!</b>\n\n"
                    f"Tài khoản <b>{a['name']}</b> đã hết <b>{a['max_hours']}h</b>!\n"
                    f"⛔ Đã tự động dừng.",
                    parse_mode="HTML"
                )
                logger.info(f"EXPIRED: {a['name']} ({a['max_hours']}h)")
        else:
            db_exec("UPDATE accounts SET elapsed=? WHERE id=?", (new_elapsed, a["id"]))

# ==================== MAIN ====================

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("=" * 50)
        print("⚠️  Chưa cấu hình BOT_TOKEN!")
        print("Mở file bot.py và thay YOUR_BOT_TOKEN_HERE")
        print("bằng token từ @BotFather")
        print("=" * 50)
        return

    init_db()
    logger.info("Database initialized")

    # Auto-register command menu in Telegram UI
    async def post_init(application):
        commands = [
            BotCommand("start", "Menu chính"),
            BotCommand("add", "Thêm TK: /add tên giờ"),
            BotCommand("addmulti", "Thêm nhiều TK"),
            BotCommand("list", "Danh sách tài khoản"),
            BotCommand("info", "Chi tiết TK: /info tên"),
            BotCommand("search", "Tìm kiếm TK"),
            BotCommand("run", "Chạy TK: /run tên"),
            BotCommand("stop", "Dừng TK: /stop tên"),
            BotCommand("runall", "Chạy tất cả"),
            BotCommand("stopall", "Dừng tất cả"),
            BotCommand("sethours", "Đổi giờ: /sethours tên giờ"),
            BotCommand("rename", "Đổi tên TK"),
            BotCommand("reset", "Reset thời gian"),
            BotCommand("delete", "Xóa TK"),
            BotCommand("deleteall", "Xóa tất cả"),
            BotCommand("export", "Xuất file danh sách"),
            BotCommand("import", "Hướng dẫn import"),
            BotCommand("status", "Thống kê tổng quan"),
            BotCommand("help", "Trợ giúp"),
        ]
        await application.bot.set_my_commands(commands)
        logger.info("Bot commands menu registered")

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("addmulti", cmd_addmulti))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("run", cmd_run))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("runall", cmd_runall))
    app.add_handler(CommandHandler("stopall", cmd_stopall))
    app.add_handler(CommandHandler("delete", cmd_delete))
    app.add_handler(CommandHandler("deleteall", cmd_deleteall))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("sethours", cmd_sethours))
    app.add_handler(CommandHandler("rename", cmd_rename))
    app.add_handler(CommandHandler("info", cmd_info))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("export", cmd_export))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("import", cmd_import))
    app.add_handler(CommandHandler("help", cmd_help))

    # Inline buttons
    app.add_handler(CallbackQueryHandler(callback_handler))

    # File upload
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    # Timer — runs every TIMER_INTERVAL seconds
    app.job_queue.run_repeating(timer_tick, interval=TIMER_INTERVAL, first=5)

    # Daily report at 8:00 AM (UTC+7)
    async def daily_report(context: ContextTypes.DEFAULT_TYPE):
        s = get_stats()
        if s['total'] == 0:
            return
        await context.bot.send_message(
            OWNER_ID,
            f"📊 <b>Báo cáo hàng ngày</b>\n\n"
            f"📦 Tổng: {s['total']} | 🟢 Chạy: {s['running']} | ⏸ Dừng: {s['stopped']} | 🔴 Hết giờ: {s['expired']}",
            parse_mode="HTML"
        )
    app.job_queue.run_daily(daily_report, time=dtime(hour=1, minute=0), chat_id=OWNER_ID)  # 1:00 UTC = 8:00 UTC+7

    logger.info("Bot is running... Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
