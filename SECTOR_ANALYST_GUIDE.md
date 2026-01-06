# Sector Analyst System - User Guide

## Tổng quan

Hệ thống **Sector Analyst** tự động giám sát và phân tích 4 cổ phiếu trong danh mục đầu tư của bạn: **FPT**, **PVS**, **KBC**, và **HPG**. Mỗi mã được theo dõi với các chỉ tiêu và tín hiệu riêng biệt.

## Chức năng chính

### 📊 FPT - Công nghệ
- **Chỉ tiêu**: P/E ratio và Tăng trưởng doanh thu quý
- **Tín hiệu**:
  - 🟢 **VÙNG MUA RẺ**: P/E < 18x (cổ phiếu đang undervalued)
  - 🔴 **CẢNH BÁO NGUY HIỂM**: Tăng trưởng doanh thu quý < 15%
- **Nguồn dữ liệu**: CafeF, VNDirect (scraping)

### ⛽ PVS - Dịch vụ dầu khí
- **Chỉ tiêu**: Giá dầu Brent crude oil
- **Tín hiệu**:
  - 🟢 **TÍN HIỆU MUA**: Brent > $85/thùng và giữ vững trong 7 ngày
- **Nguồn dữ liệu**: Commodities-API (fallback: Investing.com scraping)

### 🔧 KBC - Xây dựng & Cơ khí
- **Chỉ tiêu**: Quét tin tức về hợp tác chiến lược
- **Từ khóa**: "KBC ký biên bản ghi nhớ", "Foxconn", "LG Innotek", "Samsung"
- **Tín hiệu**:
  - 🔔 **TIN TỨC QUAN TRỌNG**: Phát hiện tin về hợp tác mới
- **Nguồn dữ liệu**: RSS feeds từ CafeF và VnExpress

### 🏗️ HPG - Thép
- **Chỉ tiêu**: Giá thép HRC trên sàn Thượng Hải
- **Tín hiệu**:
  - 🟢 **TÍN HIỆU MUA**: Giá HRC tăng liên tục 2 tuần
- **Nguồn dữ liệu**: Shanghai Futures Exchange (fallback: SMM scraping)

## Cài đặt

### 1. Cài đặt dependencies
```bash
cd stock_analyzer
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Cấu hình API keys (tùy chọn)

Tạo/chỉnh sửa file `.env`:
```bash
# Bắt buộc - Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Tùy chọn - Để cải thiện chất lượng dữ liệu
COMMODITIES_API_KEY=your_commodities_api_key_here
```

**Lưu ý**: 
- Nếu không có `COMMODITIES_API_KEY`, hệ thống sẽ tự động dùng web scraping
- Web scraping có thể không ổn định bằng API chính thức

### 3. Điều chỉnh ngưỡng cảnh báo (tùy chọn)

Chỉnh sửa `auto_config.py`:
```python
# FPT thresholds
FPT_PE_THRESHOLD = 18.0  # Thay đổi ngưỡng P/E
FPT_REVENUE_GROWTH_THRESHOLD = 15.0  # Thay đổi ngưỡng tăng trưởng

# PVS thresholds
PVS_BRENT_THRESHOLD = 85.0  # Ngưỡng giá dầu
PVS_BRENT_DAYS_STABLE = 7  # Số ngày kiểm tra

# HPG thresholds
HPG_HRC_WEEKS_INCREASE = 2  # Số tuần tăng liên tiếp
```

## Sử dụng

### Chạy test mode (dry run)
Kiểm tra xem hệ thống hoạt động đúng không:
```bash
python run_sector_analyst.py --test
```

Kết quả sẽ hiển thị ngay trên màn hình, **không gửi** Telegram.

### Chạy một lần
Tạo báo cáo và gửi qua Telegram ngay lập tức:
```bash
python run_sector_analyst.py --once
```

### Chạy theo lịch (khuyến nghị)
Tự động chạy mỗi ngày lúc 8:30 sáng:
```bash
python run_sector_analyst.py
```

Hệ thống sẽ:
1. Chạy **ngay lập tức** một lần khi khởi động
2. Sau đó chạy **mỗi ngày lúc 8:30 AM** (giờ Việt Nam)
3. Gửi báo cáo qua Telegram trước giờ giao dịch

### Dừng hệ thống
Nhấn `Ctrl+C` để dừng scheduler.

## Ví dụ báo cáo

```
📊 BÁO CÁO PHÂN TÍCH NGÀNH
⏰ 02/01/2026 08:30
========================================

🏢 FPT - Công nghệ
----------------------------------------
🟢 VÙNG MUA RẺ: P/E = 17.2x (< 18.0x)
  • Tăng trưởng doanh thu: 18.5% (tốt)
  Nguồn: CafeF (scraped)

⛽ PVS - Dịch vụ dầu khí
----------------------------------------
🟢 TÍN HIỆU MUA PVS: Brent > $85 và giữ vững 7 ngày
  • Giá hiện tại: $87.50 (> $85)
  • Brent trung bình 7 ngày: $86.80
  Nguồn: Commodities-API

🔧 KBC - Xây dựng & Cơ khí
----------------------------------------
🔔 TIN TỨC QUAN TRỌNG: Tìm thấy 2 bài viết về KBC
  • KBC ký hợp đồng hợp tác với Foxconn... (CafeF)
  📰 Tin tức nổi bật:
    - KBC triển khai dự án mới với đối tác Foxconn
      https://cafef.vn/...
  Nguồn: RSS Feeds (CafeF, VnExpress)

🏗️ HPG - Thép
----------------------------------------
🟢 TÍN HIỆU MUA HPG: Giá thép HRC tăng 2 tuần liên tiếp
  • Tuần 1: 4200.00 CNY/tấn
  • Tuần 2: 4250.00 CNY/tấn
  • Tuần 3: 4300.00 CNY/tấn
  • Giá hiện tại: 4300.00 CNY/tấn
  Nguồn: Shanghai Metals Market (scraped)

========================================
✅ TÍN HIỆU TÍCH CỰC: FPT, PVS, KBC, HPG
📬 Tổng số cảnh báo: 4

💡 Lưu ý: Đây là phân tích tự động, vui lòng xác minh trước khi đầu tư.
```

## Lưu trữ dữ liệu

Hệ thống lưu lịch sử giá để phát hiện xu hướng tại:
```
stock_analyzer/data/sector_history.json
```

File này chứa:
- Giá dầu Brent 30 ngày gần nhất
- Giá thép HRC 12 tuần gần nhất
- P/E và revenue growth của FPT theo quý

## Lưu ý quan trọng ⚠️

### Về dữ liệu thực
1. **Hệ thống KHÔNG BAO GIỜ fake data**
2. Nếu không lấy được dữ liệu → báo rõ "Dữ liệu không khả dụng"
3. Mỗi chỉ tiêu có ghi rõ nguồn dữ liệu (API hay scraping)

### Độ tin cậy dữ liệu
- **News scanning (KBC)**: Cao ✅ (RSS feeds ổn định)
- **Brent oil**: Trung bình ⚠️ (cần API key để ổn định)
- **FPT fundamentals**: Thấp ❌ (scraping phức tạp, cần cập nhật thường xuyên)
- **Shanghai steel**: Thấp ❌ (khó truy cập dữ liệu công khai)

### Khuyến nghị
1. **Luôn xác minh dữ liệu** bằng nguồn chính thức trước khi đầu tư
2. Đăng ký **Commodities-API** (free tier) để cải thiện độ tin cậy giá dầu
3. Theo dõi log file để phát hiện lỗi data scraping
4. Cân nhắc dùng API trả phí cho production

## Troubleshooting

### Không nhận được báo cáo Telegram
1. Kiểm tra Telegram credentials trong `.env`
2. Test connection:
   ```bash
   python -c "from telegram_notifier import TelegramNotifier; TelegramNotifier().test_connection()"
   ```

### Tất cả dữ liệu đều "không khả dụng"
- Đây là **hành vi đúng** nếu:
  - Chưa có API keys
  - Website thay đổi cấu trúc HTML
  - Mạng bị chặn truy cập
- Kiểm tra log để biết chi tiết

### Một số mã có data, một số không
- Đây là bình thường - các nguồn dữ liệu khác nhau có độ tin cậy khác nhau
- Ưu tiên theo dõi các mã có data ổn định (như news scanning)

## Deploy lên cloud

### Railway / Render
```bash
# Đảm bảo đã push code lên GitHub
git add .
git commit -m "Add sector analyst system"
git push

# Trong Render/Railway dashboard:
# 1. Build Command: pip install -r requirements.txt
# 2. Start Command: python run_sector_analyst.py
# 3. Add environment variables từ .env
```

### Cron job (alternative)
Nếu deploy lên VPS, dùng cron để chạy hàng ngày:
```bash
crontab -e
```

Thêm dòng:
```
30 8 * * * cd /path/to/stock_analyzer && source venv/bin/activate && python run_sector_analyst.py --once
```

## Hỗ trợ

- **Log file**: `stock_analyzer/stock_analyzer.log`
- **History file**: `stock_analyzer/data/sector_history.json`
- **Config**: `stock_analyzer/auto_config.py`

Nếu cần hỗ trợ, cung cấp:
1. Output của `--test` mode
2. Nội dung file log
3. Phiên bản Python: `python --version`
