"""
server.py — FastAPI Backend for Account Manager
Provides API endpoint to send Telegram Bot notifications.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import os

# ================================================================
# ⚠️  CẤU HÌNH TELEGRAM — Thay đổi giá trị bên dưới
# ================================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "YOUR_CHAT_ID_HERE")
# ================================================================

app = FastAPI(
    title="Account Manager API",
    description="Backend API for Account Management with Telegram notifications",
    version="1.0.0"
)

# CORS — cho phép frontend gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Request Model =====
class NotifyRequest(BaseModel):
    account_name: str
    hours: float


# ===== Health Check =====
@app.get("/health")
def health_check():
    """Check if the server and Telegram config are ready."""
    telegram_configured = (
        TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN_HERE"
        and TELEGRAM_CHAT_ID != "YOUR_CHAT_ID_HERE"
    )
    return {
        "status": "ok",
        "telegram_configured": telegram_configured
    }


# ===== Telegram Notification Endpoint =====
@app.post("/api/notify")
def send_notification(payload: NotifyRequest):
    """
    Receive account expiration signal from frontend and send Telegram message.
    """
    account_name = payload.account_name
    hours = payload.hours

    # Build message
    message = (
        f"🚨 *Cảnh báo Hệ Thống*\n\n"
        f"Tài khoản: *{account_name}*\n"
        f"Đã hoạt động đủ: *{hours} giờ*\n"
        f"Trạng thái: ⛔ Đã được tự động dừng!\n\n"
        f"_Cảnh báo: Tài khoản {account_name} đã hoạt động đủ {hours} giờ "
        f"và đã được tự động dừng!_"
    )

    # Validate config
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise HTTPException(
            status_code=500,
            detail="Telegram Bot Token chưa được cấu hình. "
                   "Hãy cập nhật TELEGRAM_BOT_TOKEN trong server.py hoặc biến môi trường."
        )

    if TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
        raise HTTPException(
            status_code=500,
            detail="Telegram Chat ID chưa được cấu hình. "
                   "Hãy cập nhật TELEGRAM_CHAT_ID trong server.py hoặc biến môi trường."
        )

    # Call Telegram Bot API
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(telegram_url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=10)

        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "message": f"Đã gửi thông báo Telegram cho tài khoản '{account_name}'",
                "telegram_response": result
            }
        else:
            error_info = response.json() if response.headers.get('content-type','').startswith('application/json') else {"error": response.text}
            raise HTTPException(
                status_code=502,
                detail=f"Telegram API trả về lỗi: {error_info}"
            )

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Telegram API timeout")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Không thể kết nối đến Telegram API")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi không mong muốn: {str(e)}")


# ===== Serve Frontend Static Files =====
# Serve index.html at root
@app.get("/")
def serve_index():
    return FileResponse("index.html")


# Serve other static files (css, js)
app.mount("/", StaticFiles(directory="."), name="static")


# ===== Run with Uvicorn =====
if __name__ == "__main__":
    import uvicorn
    print("=" * 55)
    print("  🚀 Account Manager Server")
    print("  📡 http://localhost:8000")
    print("  📖 API Docs: http://localhost:8000/docs")
    print("=" * 55)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
