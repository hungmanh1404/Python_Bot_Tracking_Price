# 🤖 Stock Analyzer Bot

Bot tự động phân tích cổ phiếu Việt Nam và gửi báo cáo hằng ngày qua Telegram.

## ✨ Tính Năng

- 🔍 **Thu thập dữ liệu thời gian thực** từ nhiều nguồn (CafeF, VietStock)
- 🤖 **Phân tích tự động** theo phương pháp 3-Agent:
  - **Agent 1 (Hunter)**: Tìm tín hiệu tích cực
  - **Agent 2 (Skeptic)**: Phát hiện rủi ro
  - **Agent 3 (Risk Manager)**: Đưa ra quyết định cuối cùng
- 📱 **Gửi báo cáo Telegram** với format đẹp mắt
- ⏰ **Tự động hóa** chạy hằng ngày theo lịch
- 📊 **Khuyến nghị giao dịch** với Entry, Stop Loss, Take Profit

## 📋 Yêu Cầu

- Python 3.8 trở lên
- Telegram Bot Token
- Telegram Chat ID

## 🚀 Cài Đặt

### 1. Clone hoặc download project

```bash
cd stock_analyzer
```

### 2. Tạo Telegram Bot

1. Mở Telegram và tìm [@BotFather](https://t.me/botfather)
2. Gửi lệnh `/newbot` và làm theo hướng dẫn
3. Lưu lại **Bot Token** (dạng: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. Lấy **Chat ID** của bạn:
   - Tìm [@userinfobot](https://t.me/userinfobot) trên Telegram
   - Gửi bất kỳ tin nhắn nào
   - Bot sẽ trả về Chat ID của bạn

### 3. Cấu hình môi trường

```bash
# Copy file mẫu
cp .env.example .env

# Chỉnh sửa file .env và điền thông tin
nano .env
```

Nội dung file `.env`:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
STOCK_SYMBOLS=FPT,PVS,KBC,HPG
SCHEDULE_TIME=08:00
```

### 4. Cài đặt dependencies

#### Tự động (khuyến nghị):
```bash
./run.sh
```

#### Thủ công:
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# hoặc: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## 📖 Cách Sử Dụng

### Test kết nối Telegram

```bash
./run.sh --test
# hoặc: python main.py --test
```

Bạn sẽ nhận được tin nhắn test trên Telegram nếu cấu hình đúng.

### Chạy phân tích thủ công (1 lần)

```bash
./run.sh --manual
# hoặc: python main.py --manual
```

Bot sẽ chạy ngay lập tức và gửi báo cáo.

### Chạy tự động theo lịch

```bash
./run.sh
# hoặc: python main.py
```

Bot sẽ:
1. Chạy phân tích ngay khi khởi động
2. Lên lịch chạy tự động hằng ngày lúc 08:00 (hoặc thời gian bạn đặt)
3. Tiếp tục chạy cho đến khi bạn dừng (Ctrl+C)

### Chạy nền (background)

#### macOS/Linux:

```bash
nohup ./run.sh > bot.log 2>&1 &
```

Dừng bot:
```bash
ps aux | grep main.py
kill <PID>
```

#### Sử dụng screen (khuyến nghị):

```bash
# Tạo session mới
screen -S stock_bot

# Chạy bot
./run.sh

# Thoát session (bot vẫn chạy): Ctrl+A, D

# Quay lại session
screen -r stock_bot

# Dừng bot: Ctrl+C trong session
```

## 📁 Cấu Trúc Project

```
stock_analyzer/
├── main.py              # Entry point
├── config.py            # Cấu hình
├── data_scraper.py      # Thu thập dữ liệu
├── analyzer.py          # Phân tích 3-Agent
├── report_generator.py  # Tạo báo cáo
├── telegram_notifier.py # Gửi Telegram
├── scheduler.py         # Tự động hóa
├── utils/
│   └── logger.py        # Logging
├── requirements.txt     # Dependencies
├── .env                 # Config (không commit)
├── .env.example         # Config mẫu
├── run.sh              # Script chạy nhanh
└── README.md           # Tài liệu này
```

## 🎯 Mẫu Báo Cáo

```
🎯 BÁO CÁO PHÂN TÍCH CỔ PHIẾU
📅 Ngày: 31/12/2025 | ⏰ 08:00
🤖 Phân tích tự động theo phương pháp 3-Agent

═══════════════════════════════════════

📈 FPT
Quyết định: 🟢 MUA NGAY
Độ tin cậy: 78/100 🔥

🐂 Điểm tích cực:
  • Giá tăng 2.5% - Momentum tích cực
  • RSI 45 - Vùng hợp lý
  • Thanh khoản tốt

🐻 Rủi ro:
  • Biến động thị trường chung
  • ...

📊 Thông tin giao dịch:
  • Entry: 95,000 - 98,000
  • Stop Loss: 92,000
  • Targets: TP1: 105,000, TP2: 115,000
  • R:R Ratio: 1:3.5

💡 Tín hiệu mua mạnh với 4 điểm tích cực

...
```

## ⚙️ Tùy Chỉnh

### Thay đổi danh sách cổ phiếu

Chỉnh sửa `STOCK_SYMBOLS` trong file `.env`:
```
STOCK_SYMBOLS=VNM,VIC,VHM,MSN,TCB
```

### Thay đổi giờ chạy

Chỉnh sửa `SCHEDULE_TIME` trong file `.env`:
```
SCHEDULE_TIME=07:30  # Chạy lúc 7:30 sáng
```

### Điều chỉnh ngưỡng phân tích

Chỉnh sửa trong `config.py`:
```python
CONFIDENCE_THRESHOLD_BUY = 75  # Ngưỡng để khuyến nghị MUA
MIN_RISK_REWARD_RATIO = 2.0    # R:R tối thiểu
```

## 🐛 Troubleshooting

### Lỗi: "TELEGRAM_BOT_TOKEN not set"
- Kiểm tra file `.env` có tồn tại và chứa đúng token

### Không nhận được tin nhắn Telegram
- Chạy `./run.sh --test` để kiểm tra
- Đảm bảo Bot Token và Chat ID đúng
- Kiểm tra bot đã được start (`/start` trong chat với bot)

### Lỗi import module
- Đảm bảo đã activate virtual environment
- Chạy lại: `pip install -r requirements.txt`

### Dữ liệu không chính xác
- Bot sử dụng web scraping, có thể bị lỗi nếu website thay đổi cấu trúc
- Cần cập nhật selector trong `data_scraper.py`

## 📝 Logs

Bot ghi log vào file `stock_analyzer.log`. Xem log:

```bash
tail -f stock_analyzer.log
```

## 🔒 Bảo Mật

- **KHÔNG** commit file `.env` lên git
- File `.env` đã được thêm vào `.gitignore`
- Giữ Bot Token bí mật

## 🚧 Roadmap

- [ ] Thêm nhiều nguồn dữ liệu (API chính thức)
- [ ] Phân tích kỹ thuật nâng cao (Fibonacci, Bollinger Bands)
- [ ] Tích hợp AI/ML cho dự đoán
- [ ] Web dashboard để xem lịch sử
- [ ] Alert giá theo điều kiện
- [ ] Backtesting framework

## 📄 License

MIT License - Tự do sử dụng và chỉnh sửa

## 🙏 Credits

Developed by Alpha Strategic Investment Council

---

**⚠️ Disclaimer:** Đây là công cụ hỗ trợ phân tích, không phải lời khuyên đầu tư. Luôn DYOR (Do Your Own Research) và quản lý rủi ro cẩn thận.
