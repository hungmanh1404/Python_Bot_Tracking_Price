# Quick Start - Sector Analyst

## Chạy ngay (3 bước)

### 1. Cài dependencies
```bash
cd stock_analyzer
source venv/bin/activate
pip install feedparser
```

### 2. Test thử
```bash
python run_sector_analyst.py --test
```

Bạn sẽ thấy báo cáo hiển thị ngay trên màn hình.

### 3. Chạy thật (gửi Telegram)

#### Chạy một lần:
```bash
python run_sector_analyst.py --once
```

#### Chạy tự động mỗi ngày 8:30 AM:
```bash
python run_sector_analyst.py
```

---

## Lưu ý quan trọng ⚠️

### Về dữ liệu

Hệ thống hiện tại sẽ báo **"Dữ liệu không khả dụng"** cho hầu hết các chỉ tiêu vì:
- ❌ Chưa có API key cho Commodities-API (giá dầu)
- ❌ P/E ratio cần scraping phức tạp
- ❌ Shanghai steel futures khó truy cập

Chỉ có **KBC news scanning** hoạt động ổn định (✅ RSS feeds).

### Để cải thiện dữ liệu

1. **Đăng ký Commodities-API** (free): https://commodities-api.com/
2. Thêm vào `.env`:
   ```
   COMMODITIES_API_KEY=your_key_here
   ```
3. Chạy lại test

---

## Điều chỉnh ngưỡng

Chỉnh sửa `auto_config.py`:

```python
# Thay đổi ngưỡng cảnh báo FPT
FPT_PE_THRESHOLD = 18.0  # Mặc định 18x

# Thay đổi ngưỡng Brent oil  
PVS_BRENT_THRESHOLD = 85.0  # Mặc định $85

# Thêm/bớt từ khóa KBC
KBC_KEYWORDS = [
    'KBC ký biên bản ghi nhớ',
    'Foxconn',
    'LG Innotek',
    'Samsung',  # Có thể thêm mới
]
```

---

## Deploy lên cloud

### Railway.app hoặc Render.com

1. Push code lên GitHub
2. Connect repository
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python run_sector_analyst.py`
5. Add environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `COMMODITIES_API_KEY` (optional)

---

## Troubleshooting

### "Dữ liệu không khả dụng"
- ✅ Đây là **hành vi đúng** nếu chưa có API keys
- Hệ thống **không fake data**, báo thật

### Không nhận Telegram
```bash
python -c "from telegram_notifier import TelegramNotifier; TelegramNotifier().test_connection()"
```

---

## Xem thêm

- **User Guide đầy đủ**: `SECTOR_ANALYST_GUIDE.md`
- **Implementation walkthrough**: Brain artifacts
- **Log file**: `stock_analyzer.log`
