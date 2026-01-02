# Deploy Lên PythonAnywhere - 100% Miễn Phí

## Tài Khoản Của Bạn
✅ Username: `manhnguyen`
✅ Console: https://www.pythonanywhere.com/user/manhnguyen/consoles/

---

## Bước 1: Clone Code Từ GitHub

1. **Mở Bash Console:**
   - Dashboard → **Consoles** → **Bash**

2. **Clone repository:**
```bash
git clone https://github.com/hungmanh1404/Python_Bot_Tracking_Price.git
cd Python_Bot_Tracking_Price
```

3. **Install dependencies:**
```bash
pip3 install --user -r requirements.txt
```

---

## Bước 2: Setup Environment Variables

1. **Tạo file .env:**
```bash
nano .env
```

2. **Thêm credentials (paste từ local .env của bạn):**
```env
TELEGRAM_BOT_TOKEN=your_actual_token_here
TELEGRAM_CHAT_ID=your_actual_chat_id_here
```

3. **Save:** `Ctrl+X` → `Y` → `Enter`

---

## Bước 3: Test Bot Chạy Được

```bash
python3 run_auto_trading.py
```

- Nếu chạy OK → Thấy "Successfully fetched real-time data from BaoMoi"
- `Ctrl+C` để stop
- Bot đang hoạt động! ✅

---

## Bước 4: Setup Scheduled Task (Chạy Mỗi Giờ)

### 4.1. Tạo Script Wrapper

PythonAnywhere cần full path, tạo script wrapper:

```bash
nano ~/run_trading_bot.sh
```

Paste vào:
```bash
#!/bin/bash
cd /home/manhnguyen/Python_Bot_Tracking_Price
python3 run_auto_trading.py
```

Save và make executable:
```bash
chmod +x ~/run_trading_bot.sh
```

### 4.2. Schedule Task

1. **Dashboard** → **Tasks**
2. Click **"Create a new scheduled task"**
3. **Fill in:**
   - **Command:** `/home/manhnguyen/run_trading_bot.sh`
   - **Hour:** `0` (runs every hour at :00)
   - **Minute:** `0`

4. Click **"Create"**

---

## ⚠️ Lưu Ý PythonAnywhere Free Tier

**Limitation:**
- Scheduled task chỉ chạy **1 lần/ngày** trên free tier
- Không phải mỗi giờ như paid plan

**Giải pháp:**
- Bot chạy 1 lần/ngày vào giờ bạn chọn
- Hoặc upgrade lên $5/month để chạy mỗi giờ

**Alternative cho free 24/7:**
- Dùng Render.com (code đã push lên GitHub rồi)
- Setup cron-job.org để ping Render

---

## Bước 5: Verify

### Check Task Logs
- Dashboard → **Tasks** → Click vào task → **Log files**
- Xem output của script

### Check Telegram
- Bot sẽ gửi notification khi chạy

---

## Update Code Sau Này

Khi có updates từ GitHub:

```bash
cd ~/Python_Bot_Tracking_Price
git pull
pip3 install --user -r requirements.txt
```

PythonAnywhere tự động dùng code mới ở lần chạy tiếp theo!

---

## Comparison: PythonAnywhere vs Render

### PythonAnywhere (hiện tại)
✅ 100% miễn phí mãi mãi
✅ Không cần credit card
❌ **Free tier: 1 task/day** (không phải mỗi giờ)
✅ Code đã sẵn sàng

### Render.com (code đã push)
✅ 100% miễn phí (750h/month)
✅ Chạy 24/7 (với cron-job.org ping)
✅ Hourly analysis
❌ Cần setup thêm cron-job.org

---

## Khuyến Nghị

**Nếu OK với 1 lần/ngày:** Dùng PythonAnywhere (đơn giản nhất)

**Nếu cần mỗi giờ/24/7:** Dùng Render (follow RENDER_DEPLOYMENT.md)

Bạn muốn option nào?
