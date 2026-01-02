# Hướng Dẫn Deploy Bot Lên Railway

## Tổng Quan

Bot sẽ chạy 24/7 trên Railway.app (free tier: $5 credit/tháng).

## Bước 1: Chuẩn Bị Git Repository

### 1.1. Khởi tạo Git (nếu chưa có)
```bash
cd /Users/manh.nguyen/Desktop/AngentChungChi/stock_analyzer
git init
```

### 1.2. Commit code
```bash
git add .
git commit -m "Prepare for Railway deployment"
```

### 1.3. Tạo GitHub Repository

1. Truy cập https://github.com/new
2. Tạo repo mới: `stock-trading-bot` (private recommended)
3. **KHÔNG** chọn "Initialize with README"

### 1.4. Push code lên GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/stock-trading-bot.git
git branch -M main
git push -u origin main
```

## Bước 2: Deploy Lên Railway

### 2.1. Đăng ký Railway
1. Truy cập https://railway.app/
2. Sign up với GitHub account
3. Verify email

### 2.2. Tạo Project Mới
1. Click **"New Project"**
2. Chọn **"Deploy from GitHub repo"**
3. Authorize Railway truy cập GitHub
4. Chọn repository `stock-trading-bot`

### 2.3. Configure Deployment
Railway sẽ tự động:
- Detect Python project
- Đọc `requirements.txt`
- Đọc `Procfile` để chạy worker
- Build và deploy

### 2.4. Thêm Environment Variables

Trong Railway dashboard:

1. Click vào project → **Settings** → **Variables**
2. Thêm các biến sau:

```
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
TELEGRAM_CHAT_ID=your_actual_chat_id_here
```

**Lấy values từ file `.env` local:**
```bash
cat .env
```

## Bước 3: Verify Deployment

### 3.1. Check Logs
1. Trong Railway dashboard → **Deployments**
2. Click vào deployment mới nhất
3. Xem **Build Logs** và **Deploy Logs**

**Logs thành công sẽ hiện:**
```
🚀 AUTOMATED TRADING BOT
Mode: PAPER TRADING
Successfully fetched real-time data for FPT from BaoMoi
Successfully fetched real-time data for KBC from BaoMoi
Successfully fetched real-time data for HPG from BaoMoi
```

### 3.2. Check Telegram
- Bot sẽ gửi startup notification
- Sau đó gửi hourly report mỗi giờ

### 3.3. Monitor Resource Usage
Railway dashboard → **Metrics**
- CPU usage
- Memory usage  
- Network

## Bước 4: Update Bot (Sau Này)

Khi có code changes:

```bash
git add .
git commit -m "Update: description of changes"
git push
```

Railway sẽ **tự động deploy** version mới!

## Troubleshooting

### Bot không start
**Check:**
1. Logs có error gì không
2. Environment variables đã set đúng chưa
3. `requirements.txt` có đầy đủ dependencies

**Fix:**
```bash
# Re-deploy
git commit --allow-empty -m "Trigger redeploy"
git push
```

### Out of Credits
Railway free tier: $5/tháng

**Monitor usage:** Dashboard → Billing

**Nếu hết credit:**
- Add payment method (chỉ charge khi vượt free tier)
- Hoặc deploy lên platform khác (Render, Fly.io)

### Bot stopped unexpectedly
**Check logs:**
- Railway dashboard → Deployments → Latest → Logs
- Tìm error messages

**Common issues:**
- BaoMoi API timeout → Bot tự động fallback
- Memory limit → Optimize code hoặc upgrade plan
- Telegram API error → Check bot token

### Can't connect to GitHub
```bash
# Re-authenticate
gh auth login
```

### Railway không detect Python
Đảm bảo có các files:
- `requirements.txt` ✓
- `Procfile` ✓
- `runtime.txt` ✓

## Commands Hữu Ích

### Xem logs realtime từ terminal (optional)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# View logs
railway logs
```

### Stop bot
Railway dashboard → Project → **Settings** → **Pause Deployments**

### Restart bot  
Dashboard → **Redeploy**

## Free Tier Limits

Railway Free Tier ($5 credit/month):
- ✅ Đủ cho 1-2 bots nhỏ
- ✅ Chạy 24/7
- ✅ 512MB RAM
- ✅ Shared CPU

**Estimate:** Bot này tiêu tốn ~$2-3/tháng

## Backup Plan: Alternative Platforms

Nếu Railway không phù hợp:

### Render.com
- Free tier có sleep (không dùng được 24/7)
- Deploy tương tự Railway

### Fly.io
- Free tier tốt hơn
- Cần credit card để verify
- Phức tạp hơn chút

### PythonAnywhere
- Free tier không support long-running
- Phù hợp cho scheduled tasks hơn

---

## Done!

Bot giờ đang chạy 24/7 trên cloud! 🎉

Monitor qua:
- Railway dashboard
- Telegram notifications
