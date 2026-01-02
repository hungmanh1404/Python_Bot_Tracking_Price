# 🚀 Railway Deployment - Quick Start

Code đã được push lên GitHub thành công!

**Repository:** https://github.com/hungmanh1404/Python_Bot_Tracking_Price

---

## Bước Tiếp Theo: Deploy Trên Railway

### 1. Truy Cập Railway
👉 https://railway.app

- Click **"Login with GitHub"**
- Authorize Railway

### 2. Tạo Project Mới
- Click **"New Project"**
- Chọn **"Deploy from GitHub repo"**
- Tìm và chọn: **Python_Bot_Tracking_Price**
- Click **"Deploy Now"**

Railway sẽ tự động:
✅ Detect Python project  
✅ Install dependencies từ `requirements.txt`  
✅ Đọc `Procfile` để chạy bot  
✅ Build và deploy

### 3. Configure Environment Variables

Trong Railway dashboard:

1. Click vào project vừa tạo
2. Vào tab **"Variables"**
3. Click **"+ New Variable"**
4. Thêm 2 variables:

```
TELEGRAM_BOT_TOKEN=<token_của_bạn>
TELEGRAM_CHAT_ID=<chat_id_của_bạn>
```

**Lấy values từ file `.env` local:**
```bash
cd /Users/manh.nguyen/Desktop/AngentChungChi/stock_analyzer
cat .env
```

Copy đúng values vào Railway.

### 4. Redeploy (Sau Khi Add Env Vars)

- Click tab **"Deployments"**
- Click **"Redeploy"** để bot chạy với env vars mới

### 5. Verify Bot Đang Chạy

**Check Logs:**
- Tab **"Deployments"** → Click deployment mới nhất
- Xem logs, nên thấy:
  ```
  🚀 AUTOMATED TRADING BOT
  Mode: PAPER TRADING
  Successfully fetched real-time data for FPT from BaoMoi
  Successfully fetched real-time data for KBC from BaoMoi
  Successfully fetched real-time data for HPG from BaoMoi
  ```

**Check Telegram:**
- Bot sẽ gửi startup notification
- Mỗi giờ gửi hourly report

---

## Monitoring

### Xem Logs Realtime
Railway Dashboard → **Deployments** → Latest → **View Logs**

### Check Resource Usage  
Railway Dashboard → **Metrics**
- CPU: Should be <10%
- Memory: ~200-300MB
- Network: Minimal

### Cost Tracking
Dashboard → **Usage**
- Free tier: $5/month
- Your bot: ~$2-3/month ✅

---

## Update Code Sau Này

Khi có code changes:

```bash
cd /Users/manh.nguyen/Desktop/AngentChungChi/stock_analyzer

# Make changes
git add .
git commit -m "Update: description"
git push
```

Railway **tự động** redeploy trong ~2 phút! 🚀

---

## Troubleshooting

### Bot Không Start
- Check logs có error
- Verify env vars đã set đúng
- Ensure requirements.txt complete

### Telegram Không Nhận Notification
- Check `TELEGRAM_BOT_TOKEN` correct
- Check `TELEGRAM_CHAT_ID` correct
- Test bot token: https://api.telegram.org/bot<YOUR_TOKEN>/getMe

### Out of Memory
- Railway free tier: 512MB RAM
- Bot này dùng ~200-300MB
- Nếu vượt: optimize code hoặc upgrade plan

---

## Summary

✅ Code trên GitHub: https://github.com/hungmanh1404/Python_Bot_Tracking_Price  
✅ Ready to deploy trên Railway  
✅ Bot sẽ chạy 24/7 với real-time data từ BaoMoi  
✅ Free tier: $5/month (bot dùng ~$2-3)

**Next:** Follow steps above để deploy! 🎉
