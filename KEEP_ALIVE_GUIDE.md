# Keep-Alive Guide for Render.com

## Problem
Render.com free tier servers sleep after 15 minutes of inactivity. Cần ping health endpoint định kỳ để giữ bot luôn chạy.

---

## Solution 1: Chạy Pinger Script (Recommended cho Local/VPS)

### Bước 1: Test thử
```bash
cd /Users/manh.nguyen/Desktop/AngentChungChi/stock_analyzer
python3 keep_alive_pinger.py
```

Script sẽ ping `https://python-bot-tracking-price.onrender.com/health` mỗi 5 phút.

### Bước 2: Chạy nền (background)

**macOS/Linux:**
```bash
# Chạy nền với nohup
nohup python3 keep_alive_pinger.py > pinger.log 2>&1 &

# Hoặc dùng screen
screen -S pinger
python3 keep_alive_pinger.py
# Ctrl+A, D để detach
```

**Stop pinger:**
```bash
# Tìm process
ps aux | grep keep_alive_pinger

# Kill process
kill <PID>
```

---

## Solution 2: External Cron Service (BEST - FREE & Reliable)

### Option A: UptimeRobot (Recommended)

**FREE**、 mỗi 5 phút、 unlimited monitors

1. Đăng ký: https://uptimerobot.com/
2. Click **"+ Add New Monitor"**
3. Cấu hình:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Bot Keep Alive
   - **URL**: `https://python-bot-tracking-price.onrender.com/health`
   - **Monitoring Interval**: 5 minutes
4. Click **"Create Monitor"**

✅ Done! UptimeRobot sẽ tự động ping mỗi 5 phút.

---

### Option B: Cron-job.org

**FREE**, mỗi 1-60 phút

1. Đăng ký: https://cron-job.org/
2. Click **"Create cronjob"**
3. Cấu hình:
   - **Title**: Keep Bot Alive
   - **URL**: `https://python-bot-tracking-price.onrender.com/health`
   - **Schedule**: Every 5 minutes
4. Save

---

### Option C: Freshping (by Freshworks)

**FREE**, mỗi 1 phút

1. Đăng ký: https://www.freshworks.com/website-monitoring/
2. Add new check
3. URL: `https://python-bot-tracking-price.onrender.com/health`
4. Interval: 5 minutes

---

## Solution 3: GitHub Actions (Advanced)

Tạo file `.github/workflows/keep-alive.yml`:

```yaml
name: Keep Bot Alive

on:
  schedule:
    # Chạy mỗi 5 phút
    - cron: '*/5 * * * *'
  workflow_dispatch:  # Cho phép chạy manual

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Health Endpoint
        run: |
          curl -f https://python-bot-tracking-price.onrender.com/health || exit 0
          echo "Health check completed"
```

Push lên GitHub repo → Actions sẽ tự chạy mỗi 5 phút.

---

## Solution 4: Render Cron Job (Paid Plan Only)

Nếu upgrade lên Render paid plan, có thể dùng Render Cron Jobs:

```yaml
# render.yaml
services:
  - type: web
    name: trading-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python run_auto_trading.py
    
  - type: cron
    name: keep-alive
    env: python
    schedule: "*/5 * * * *"  # Every 5 minutes
    buildCommand: pip install requests
    startCommand: curl https://python-bot-tracking-price.onrender.com/health
```

---

## Recommendation

**TỐT NHẤT: Dùng UptimeRobot** ✅

**Lý do:**
- ✅ 100% free
- ✅ Không cần máy chạy 24/7
- ✅ Có dashboard theo dõi uptime
- ✅ Email alert nếu bot down
- ✅ Easy setup (2 phút)

---

## Verify It's Working

### 1. Check Render Logs
```
Render Dashboard → Your Service → Logs
```

Sẽ thấy:
```
GET /health 200 OK
Healthy! Bot running... 
```

### 2. Check Health Endpoint
```bash
curl https://python-bot-tracking-price.onrender.com/health
```

Response:
```json
{
  "status": "healthy",
  "uptime": "5h 23m",
  ...
}
```

### 3. UptimeRobot Dashboard
Sẽ hiện **"Up"** với uptime % > 99%

---

## Troubleshooting

### Bot vẫn bị sleep?

**Kiểm tra:**
1. Health endpoint có response 200 OK không?
   ```bash
   curl -I https://python-bot-tracking-price.onrender.com/health
   ```

2. UptimeRobot có ping đúng URL không?

3. Render logs có requests đến `/health` không?

### Pinger script không chạy?

```bash
# Check Python version
python3 --version  # Cần >= 3.7

# Install requests nếu thiếu
pip3 install requests

# Run với verbose logging
python3 keep_alive_pinger.py
```

---

## Cost Comparison

| Solution | Cost | Reliability | Setup Time |
|----------|------|-------------|------------|
| UptimeRobot | FREE | ⭐⭐⭐⭐⭐ | 2 min |
| Local Pinger | FREE* | ⭐⭐ | 5 min |
| GitHub Actions | FREE | ⭐⭐⭐⭐ | 10 min |
| Cron-job.org | FREE | ⭐⭐⭐⭐ | 3 min |

*Yêu cầu máy chạy 24/7

---

## Next Steps

1. ✅ Đăng ký UptimeRobot
2. ✅ Add monitor cho health endpoint
3. ✅ Đợi 30 phút
4. ✅ Kiểm tra Render logs thấy requests đều đặn mỗi 5 phút

🎉 Bot sẽ không bao giờ sleep nữa!
