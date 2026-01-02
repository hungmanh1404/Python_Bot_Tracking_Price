# 🚀 Hướng Dẫn Deploy Lên Render - Từng Bước

Code đã sẵn sàng trên GitHub với health check server!

---

## Bước 1: Đăng Ký Render

1. Truy cập: **https://render.com**
2. Click **"Get Started for Free"**
3. Chọn **"Sign in with GitHub"**
4. Authorize Render truy cập GitHub
5. ✅ **Không cần credit card!**

---

## Bước 2: Tạo Background Worker

1. Sau khi login, click **"New +"** (góc trên bên phải)
2. Chọn **"Background Worker"**

---

## Bước 3: Connect GitHub Repository

1. Tìm repository: **Python_Bot_Tracking_Price**
   - Nếu không thấy → Click **"Configure account"** → Grant access
2. Click **"Connect"** bên cạnh repo

---

## Bước 4: Configure Service

### 4.1. Basic Settings
- **Name:** `stock-trading-bot` (hoặc tên bạn thích)
- **Region:** `Singapore` (gần VN nhất)
- **Branch:** `main`
- **Root Directory:** để trống

### 4.2. Build & Start Commands
- **Build Command:**
  ```
  pip install -r requirements.txt
  ```
- **Start Command:**
  ```
  python3 run_auto_trading.py
  ```

### 4.3. Plan
- Chọn: **Free** (màu xám)
- Instance Type: Free

---

## Bước 5: Add Environment Variables

**QUAN TRỌNG!** Scroll xuống phần **Environment Variables**

Click **"Add Environment Variable"** và thêm **2 variables**:

### Variable 1:
- **Key:** `TELEGRAM_BOT_TOKEN`
- **Value:** `<paste_token_từ_file_.env_của_bạn>`

### Variable 2:
- **Key:** `TELEGRAM_CHAT_ID`
- **Value:** `<paste_chat_id_từ_file_.env_của_bạn>`

**Lấy values:**
```bash
# Trên máy local
cd /Users/manh.nguyen/Desktop/AngentChungChi/stock_analyzer
cat .env
```

Copy chính xác token và chat_id!

---

## Bước 6: Deploy!

1. Click **"Create Background Worker"** (button xanh ở dưới cùng)
2. Render sẽ:
   - Clone code từ GitHub
   - Install dependencies
   - Start bot
   - ⏱️ Mất ~2-3 phút

---

## Bước 7: Monitor Deployment

### 7.1. Check Logs
- Trong service dashboard → Tab **"Logs"**
- Xem build logs và runtime logs

**Nên thấy:**
```
✅ Health check server started on port 10000
🚀 AUTOMATED TRADING BOT
Mode: PAPER TRADING
Successfully fetched real-time data for FPT from BaoMoi
Successfully fetched real-time data for KBC from BaoMoi
Successfully fetched real-time data for HPG from BaoMoi
```

### 7.2. Check Telegram
- Bot gửi startup notification
- Sau đó gửi hourly reports

---

## Bước 8: Setup Anti-Sleep (Quan Trọng!)

Render free tier **sleep sau 15 phút idle**. Cần ping mỗi 10 phút.

### Option A: Cron-job.org (Khuyến nghị)

1. Truy cập: **https://cron-job.org**
2. Sign up (miễn phí)
3. Dashboard → Click **"Create cronjob"**

**Configure cronjob:**
- **Title:** `Keep Render Bot Awake`
- **URL:** `https://stock-trading-bot.onrender.com/health`
  - Thay `stock-trading-bot` bằng tên service của bạn
  - Lấy URL từ Render dashboard (phía trên)
- **Schedule:**
  - Every: `10` minutes
  - Or: `*/10 * * * *` (cron expression)
- **Enabled:** ✅ Check

4. Click **"Create"**

### Option B: UptimeRobot (Alternative)

1. https://uptimerobot.com
2. Add Monitor:
   - Monitor Type: `HTTP(s)`
   - Friendly Name: `Render Bot`
   - URL: `https://your-service.onrender.com/health`
   - Monitoring Interval: `5 minutes`

---

## Verify Everything Works

### ✅ Checklist

1. **Render Logs:** Thấy "Successfully fetched real-time data"
2. **Telegram:** Nhận startup notification
3. **Health Endpoint:** Truy cập `https://your-service.onrender.com/health`
   - Nên thấy: "OK - Stock Trading Bot is running"
4. **Cron-job.org:** Status shows "Success" sau vài phút
5. **Hourly Reports:** Telegram nhận reports mỗi giờ

---

## Troubleshooting

### Bot không start
**Check logs có error:**
- Tab Logs → Tìm error messages
- Common: Missing env vars

**Fix:**
- Environment tab → Verify TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID đúng
- Redeploy: Settings → Manual Deploy → Deploy latest commit

### Health endpoint không response
**Check:**
- Logs có "Health check server started"?
- URL đúng chưa? (có `/health` ở cuối)

**Fix:**
- Code đã có health_server.py (✅ đã push)
- Redeploy nếu cần

### Bot bị sleep
**Nguyên nhân:** Chưa setup cron-job.org

**Fix:** Follow Bước 8

### Out of hours (>750h/month)
**Render free tier:** 750 hours/month = ~31 days

**Giải pháp:**
- Bạn chỉ dùng 1 service → OK
- Hoặc upgrade plan ($7/month)

---

## Update Code Sau Này

Khi có changes:

```bash
cd /Users/manh.nguyen/Desktop/AngentChungChi/stock_analyzer
git add .
git commit -m "Update: description"
git push origin main
```

Render **tự động redeploy** trong 2-3 phút! 🚀

---

## So Sánh Options

### Render (Đang hướng dẫn)
✅ Free 24/7 (với cron-job.org)
✅ Không cần credit card
✅ Auto deploy từ GitHub
✅ Chạy mỗi 5 phút (poll interval)
⚠️ Cần setup cron-job.org

### PythonAnywhere (Bạn có account)
✅ 100% free mãi mãi
✅ Không setup gì thêm
❌ Free tier: 1 task/day (không phải mỗi giờ)
✅ Đơn giản nhất

### Railway
✅ $5 credit/month free
✅ Easiest setup
⚠️ Bot dùng ~$2-3/month
❌ Cần monitor credit

---

## Recommendation

**Dùng Render** nếu bạn muốn:
- Bot chạy 24/7
- Hourly analysis
- Free forever
- OK với setup thêm cron-job

**Dùng PythonAnywhere** nếu bạn:
- OK với 1 lần/ngày
- Muốn zero setup
- Không muốn quản lý thêm service

---

## Done! 🎉

Bot của bạn giờ chạy 24/7 trên cloud với:
- ✅ Real-time data từ BaoMoi
- ✅ Hourly reports qua Telegram
- ✅ 100% miễn phí
- ✅ Auto deploy khi push GitHub
