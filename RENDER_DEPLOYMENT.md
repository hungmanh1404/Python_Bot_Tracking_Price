# Deploy to Render.com - 100% Free

## ⚠️ Render Free Tier Limitation

**QUAN TRỌNG:**
- Render free tier **sleep sau 15 phút không có request**
- Bot sẽ bị dừng khi idle
- **Giải pháp:** Dùng external service ping bot mỗi 10 phút (miễn phí)

---

## Bước 1: Đăng Ký Render

1. Truy cập: https://render.com
2. Sign up với GitHub account
3. **Không cần credit card**

---

## Bước 2: Deploy Bot

### 2.1. Tạo New Service
1. Dashboard → **New** → **Background Worker**
2. Connect GitHub repo: `Python_Bot_Tracking_Price`

### 2.2. Configure Service
- **Name:** `stock-trading-bot`
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python3 run_auto_trading.py`
- **Plan:** **Free**

### 2.3. Add Environment Variables
Click **Environment** → Add:
```
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 2.4. Deploy
Click **Create Background Worker** → Render tự động build và deploy!

---

## Bước 3: Giữ Bot Không Sleep (Anti-Sleep)

Render free tier sleep sau 15 phút. Để bot chạy 24/7:

### Option 1: Cron-job.org (Khuyến nghị)
1. Truy cập: https://cron-job.org (free)
2. Tạo tài khoản
3. Create Cronjob:
   - **URL:** `https://your-bot-name.onrender.com/health`
   - **Interval:** Every 10 minutes
   - **Enabled:** Yes

**Lưu ý:** Cần thêm health endpoint vào bot (tôi sẽ tạo)

### Option 2: UptimeRobot (Alternative)
1. https://uptimerobot.com (free)
2. Add Monitor:
   - Type: HTTP(s)
   - URL: `https://your-bot-name.onrender.com/health`
   - Interval: 5 minutes

---

## Files Cần Thêm

### 1. Health Check Endpoint

Tạo file `health_server.py` để Render/Cron-job có thể ping:

```python
# Simple HTTP server for health checks
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def start_health_server():
    server = HTTPServer(('0.0.0.0', 10000), HealthHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
```

### 2. Update `run_auto_trading.py`

Thêm health server:
```python
from health_server import start_health_server

# Start health check server
health_server = start_health_server()
print("Health check server started on port 10000")

# Run bot as usual...
```

---

## Verification

### Check Deployment
1. Render Dashboard → Logs
2. Xem startup logs
3. Verify "Successfully fetched real-time data from BaoMoi"

### Check Telegram
- Bot gửi startup notification
- Hourly reports

### Check Health Endpoint
```bash
curl https://your-bot-name.onrender.com/health
# Should return: OK
```

---

## Cost

✅ **100% Miễn phí:**
- Render.com: Free tier
- Cron-job.org: Free
- **Không tốn 1 đồng!**

---

## Pros & Cons

### ✅ Pros
- Hoàn toàn miễn phí
- Không cần credit card
- Easy setup
- Auto deploy từ GitHub
- Good logs

### ⚠️ Cons
- Cần anti-sleep workaround
- Có thể bị delay khi wake up từ sleep
- 750 hours/month (đủ cho 24/7)

---

## Next Steps

1. Tôi sẽ tạo `health_server.py`
2. Update `run_auto_trading.py`
3. Push lên GitHub
4. Deploy trên Render
5. Setup cron-job.org anti-sleep
6. Done! Bot chạy 24/7 miễn phí
