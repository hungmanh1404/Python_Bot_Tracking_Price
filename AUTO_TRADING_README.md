# 🤖 Automated Trading Bot - Hướng Dẫn Sử Dụng

## Tổng Quan

Bot giao dịch tự động chạy liên tục, theo dõi thị trường real-time và tự động thực hiện mua/bán dựa trên chiến lược 3-Agent.

## ⚙️ Cấu Hình

### Chế Độ Trading

Mở file `auto_config.py` và điều chỉnh:

```python
PAPER_TRADING_MODE = True  # True = Paper trading, False = Real trading
INITIAL_CAPITAL = 10_000_000  # VND
```

### Tham Số Trading

```python
POLL_INTERVAL = 300  # Kiểm tra giá mỗi 5 phút

# Position sizing
MAX_POSITION_SIZE = 0.25  # Tối đa 25% vào 1 mã

# Risk management
STOP_LOSS_PCT = 0.08  # Auto-sell khi lỗ 8%
TAKE_PROFIT_PCT = 0.15  # Auto-sell 50% khi lời 15%
MAX_DAILY_LOSS_PCT = 0.05  # Dừng trading nếu lỗ 5%/ngày
MAX_DRAWDOWN_PCT = 0.15  # Dừng hoàn toàn nếu lỗ 15%
```

## 🚀 Chạy Bot

### 1. Test Mode (Paper Trading)

```bash
cd stock_analyzer
source venv/bin/activate
python run_auto_trading.py
```

### 2. Chạy Nền (Background)

```bash
screen -S trading_bot
python run_auto_trading.py
# Ctrl+A, D để detach
# screen -r trading_bot để quay lại
```

## 📱 Thông Báo Telegram

Bot sẽ gửi các loại thông báo sau:

1. **Startup**: Khi bot bắt đầu chạy
2. **Trade Alerts**: Mỗi khi mua/bán
3. **Hourly Reports**: Cập nhật mỗi giờ
4. **Stop-Loss/Take-Profit**: Khi được trigger
5. **Circuit Breaker**: Khi bot dừng do rủi ro

## 🛡️ Safety Mechanisms

### Auto Stop-Loss
- Mỗi vị thế có stop-loss tự động ở -8%
- Trailing stop: Stop-loss tăng theo giá

### Daily Loss Limit
- Bot tự dừng nếu lỗ > 5% trong ngày
- Reset vào đầu phiên sáng hôm sau

### Circuit Breaker
Bot dừng hoàn toàn khi:
- Total drawdown > 15%
- 3 lệnh lỗ liên tiếp
- Daily loss > 5%

### Position Limits
- Max 4 vị thế cùng lúc
- Max 25% vốn/mã
- Min 5% vốn/mã

## ⚠️ LƯU Ý QUAN TRỌNG

> **CẢNH BÁO**
> 
> - Đây là auto-trading bot, sẽ tự động mua/bán
> - LUÔN test với PAPER MODE trước
> - Có rủi ro mất vốn
> - Không nên để bot chạy unsupervised
> - Chỉ trade với tiền có thể chấp nhận mất

## 🔧 Troubleshooting

### Bot không giao dịch
- Kiểm tra confidence threshold (min 60%)
- Xem log để biết lý do reject
- Kiểm tra circuit breaker status

### Bot dừng đột ngột
- Xem log file `stock_analyzer.log`
- Kiểm tra Telegram messages
- Có thể do circuit breaker hoặc lỗi API

### Giá không cập nhật
- Kiểm tra internet connection
- Verify web scraping vẫn hoạt động
- Xem xét dùng API thay vì scraping

## 📊 Monitoring

Theo dõi bot qua:
1. **Terminal logs**: Real-time output
2. **Telegram**: Hourly updates
3. **Log file**: `stock_analyzer.log`

## 🛑 Dừng Bot

1. **Graceful stop**: Ctrl+C trong terminal
2. **Force stop**: `pkill -f run_auto_trading`
3. Bot sẽ gửi final report khi dừng

---

**Lưu ý:** Đây là phiên bản beta. Luôn monitor closely và sẵn sàng can thiệp thủ công nếu cần!
