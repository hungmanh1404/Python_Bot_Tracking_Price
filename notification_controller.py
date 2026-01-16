"""
Notification Controller
Smart notification management to reduce Telegram spam
Only sends critical alerts immediately, batches less important messages
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from utils.logger import logger

class NotificationLevel(Enum):
    """Notification priority levels"""
    CRITICAL = 1  # Send immediately
    IMPORTANT = 2  # Include in hourly digest
    INFO = 3      # Include in daily digest only

@dataclass
class Notification:
    """Notification message with metadata"""
    level: NotificationLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    category: str = "general"
    data: Dict = field(default_factory=dict)

class NotificationController:
    """Controls notification flow to reduce spam"""
    
    def __init__(self, telegram_notifier):
        """
        Initialize notification controller
        
        Args:
            telegram_notifier: TelegramNotifier instance
        """
        self.notifier = telegram_notifier
        
        # Message queues
        self.important_queue: List[Notification] = []
        self.info_queue: List[Notification] = []
        
        # Tracking
        self.last_hourly_digest = None
        self.last_daily_digest = None
        self.sent_messages_cache = []  # For deduplication
        
        # Deduplication window
        self.dedup_window_seconds = 300  # 5 minutes
    
    def notify(self, message: str, level: NotificationLevel = NotificationLevel.INFO, 
               category: str = "general", data: Dict = None) -> bool:
        """
        Send notification based on priority level
        
        Args:
            message: Notification message
            level: Priority level
            category: Message category for grouping
            data: Additional data
            
        Returns:
            True if sent immediately
        """
        notification = Notification(
            level=level,
            message=message,
            category=category,
            data=data or {}
        )
        
        # Check for duplicates
        if self._is_duplicate(notification):
            logger.debug(f"Skipping duplicate notification: {message[:50]}")
            return False
        
        if level == NotificationLevel.CRITICAL:
            # Send immediately
            success = self.notifier.send_message(message)
            if success:
                self._add_to_cache(notification)
            return success
        
        elif level == NotificationLevel.IMPORTANT:
            # Queue for hourly digest
            self.important_queue.append(notification)
            logger.debug(f"Queued IMPORTANT notification: {message[:50]}")
            return False
        
        else:  # INFO
            # Queue for daily digest
            self.info_queue.append(notification)
            logger.debug(f"Queued INFO notification: {message[:50]}")
            return False
    
    def send_startup_message(self, config) -> bool:
        """Send bot startup notification (CRITICAL)"""
        mode = "PAPER TRADING" if config.PAPER_TRADING_MODE else "⚠️ LIVE TRADING"
        
        msg = f"""🤖 *AUTO TRADING BOT STARTED*

*Mode:* {mode}
*Capital:* {config.INITIAL_CAPITAL:,.0f} VND
*Symbols:* {', '.join(config.TRADING_SYMBOLS)}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.notify(msg, NotificationLevel.CRITICAL, "system")
    
    def send_trade_alert(self, trade: Dict) -> bool:
        """Send trade execution alert (CRITICAL)"""
        action_emoji = "🟢 BUY" if trade['action'] == 'BUY' else "🔴 SELL"
        
        msg = f"""{action_emoji} *{trade['symbol']}*

*Price:* {trade['price']:,.0f} VND
*Shares:* {trade['shares']}
*Value:* {trade['total']:,.0f} VND

*Strategy:* {trade.get('strategy', 'N/A')}
"""
        
        if trade['action'] == 'SELL' and 'pnl' in trade:
            pnl_emoji = "💚" if trade['pnl'] > 0 else "❤️"
            msg += f"{pnl_emoji} *P&L:* {trade['pnl']:+,.0f} VND ({trade['pnl_percentage']:+.2f}%)\n"
        
        return self.notify(msg, NotificationLevel.CRITICAL, "trade", trade)
    
    def send_stop_loss_alert(self, symbol: str, price: float, pnl: float) -> bool:
        """Send stop-loss trigger alert (CRITICAL)"""
        msg = f"""🛑 *STOP-LOSS TRIGGERED*

*Symbol:* {symbol}
*Price:* {price:,.0f} VND
*P&L:* {pnl:+,.0f} VND

Bảo vệ vốn thành công!
"""
        
        return self.notify(msg, NotificationLevel.CRITICAL, "stop_loss")
    
    def send_circuit_breaker_alert(self, reason: str) -> bool:
        """Send circuit breaker alert (CRITICAL)"""
        msg = f"""🚨 *CIRCUIT BREAKER ACTIVE*

{reason}

Trading đã tạm dừng. Cần review ngay!
"""
        
        return self.notify(msg, NotificationLevel.CRITICAL, "circuit_breaker")
    
    def send_pause_alert(self, reason: str, resume_time: datetime) -> bool:
        """Send auto-pause alert (CRITICAL)"""
        msg = f"""⏸️ *AUTO PAUSE ACTIVATED*

*Lý do:* {reason}
*Resume lúc:* {resume_time.strftime('%Y-%m-%d %H:%M')}

Bot sẽ tự động tiếp tục hoặc dùng `/resume` để bắt đầu lại.
"""
        
        return self.notify(msg, NotificationLevel.CRITICAL, "pause")
    
    def queue_position_update(self, symbol: str, current_price: float, 
                             pnl: float, pnl_pct: float):
        """Queue position update for hourly digest (IMPORTANT)"""
        pnl_emoji = "📈" if pnl >= 0 else "📉"
        msg = f"{pnl_emoji} {symbol}: {current_price:,.0f} VND ({pnl:+,.0f}, {pnl_pct:+.1f}%)"
        
        self.notify(msg, NotificationLevel.IMPORTANT, "position")
    
    def queue_market_update(self, symbol: str, price: float, change_pct: float):
        """Queue market price update (INFO)"""
        change_emoji = "🔼" if change_pct >= 0 else "🔽"
        msg = f"{change_emoji} {symbol}: {price:,.0f} VND ({change_pct:+.2f}%)"
        
        self.notify(msg, NotificationLevel.INFO, "market")
    
    def send_hourly_digest(self, performance: Dict) -> bool:
        """Send hourly performance digest"""
        now = datetime.now()
        
        # Check if we should send (every hour)
        if self.last_hourly_digest and (now - self.last_hourly_digest).seconds < 3600:
            return False
        
        msg = f"""📊 *BÁO CÁO THEO GIỜ*

💰 *Danh mục:* {performance['current_value']:,.0f} VND
📈 *P&L:* {performance['total_pnl']:+,.0f} VND ({performance['total_return_pct']:+.2f}%)
💵 *Tiền mặt:* {performance['cash']:,.0f} VND

*Vị thế:* {performance['num_positions']}
*Giao dịch hôm nay:* {len([t for t in performance['trades'] if t['time'].date() == now.date()])}
"""
        
        # Add important queued messages
        if self.important_queue:
            msg += f"\n📋 *CẬP NHẬT:*\n"
            # Group by category
            by_category = {}
            for notif in self.important_queue:
                if notif.category not in by_category:
                    by_category[notif.category] = []
                by_category[notif.category].append(notif.message)
            
            for category, messages in by_category.items():
                if len(messages) <= 3:
                    for m in messages:
                        msg += f"• {m}\n"
                else:
                    # Summarize if too many
                    msg += f"• {len(messages)} updates trong {category}\n"
        
        msg += f"\n⏰ {now.strftime('%H:%M')}"
        
        success = self.notifier.send_message(msg)
        if success:
            self.important_queue.clear()
            self.last_hourly_digest = now
        
        return success
    
    def send_daily_digest(self, performance: Dict, journal_summary: str) -> bool:
        """Send end-of-day full report"""
        now = datetime.now()
        
        msg = f"""📈 *BÁO CÁO CUỐI NGÀY* - {now.strftime('%Y-%m-%d')}

💰 *Kết quả:*
• Giá trị danh mục: {performance['current_value']:,.0f} VND
• P&L hôm nay: {performance['total_pnl']:+,.0f} VND ({performance['total_return_pct']:+.2f}%)
• Tiền mặt: {performance['cash']:,.0f} VND

📊 *Hoạt động:*
• Vị thế mở: {performance['num_positions']}
• Giao dịch: {len([t for t in performance['trades'] if t['time'].date() == now.date()])}

{journal_summary}

Chúc ngủ ngon! 🌙
"""
        
        success = self.notifier.send_long_message(msg)
        if success:
            self.info_queue.clear()
            self.last_daily_digest = now
        
        return success
    
    def _is_duplicate(self, notification: Notification) -> bool:
        """Check if notification is duplicate within time window"""
        now = datetime.now()
        
        # Clean old cache
        self.sent_messages_cache = [
            n for n in self.sent_messages_cache 
            if (now - n.timestamp).seconds < self.dedup_window_seconds
        ]
        
        # Check for duplicates
        for cached in self.sent_messages_cache:
            if (cached.category == notification.category and 
                cached.message == notification.message):
                return True
        
        return False
    
    def _add_to_cache(self, notification: Notification):
        """Add notification to cache for deduplication"""
        self.sent_messages_cache.append(notification)
