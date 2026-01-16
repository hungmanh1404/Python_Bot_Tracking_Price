"""
Trade Journal (Trụ 4)
Comprehensive trade tracking for discipline and learning
Records every trade with full context, analysis, and results
"""
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from utils.logger import logger

@dataclass
class JournalEntry:
    """Single trade journal entry"""
    # Pre-trade planning
    timestamp: str
    symbol: str
    action: str  # BUY or SELL
    strategy: str  # breakout, pullback, etc.
    market_regime: str
    entry_reason: str
    
    # Trade execution
    entry_price: float
    shares: int
    total_value: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    risk_reward: float
    risk_amount: float  # Money at risk
    
    # Post-trade results (filled on exit)
    exit_timestamp: Optional[str] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None
    
    # Lessons learned
    notes: str = ""
    mistakes: List[str] = None
    
    def __post_init__(self):
        if self.mistakes is None:
            self.mistakes = []

class TradeJournal:
    """Manages trade journal and performance analytics"""
    
    def __init__(self, journal_file: str = "data/trade_journal.json"):
        """
        Initialize trade journal
        
        Args:
            journal_file: Path to journal file
        """
        self.journal_file = journal_file
        self.entries: List[JournalEntry] = []
        
        # Ensure data directory exists
        Path(journal_file).parent.mkdir(exist_ok=True)
        
        # Load existing journal
        self._load_journal()
        
        # Pause tracking
        self.consecutive_losses = 0
        self.pause_until: Optional[datetime] = None
        self.pause_reason = ""
    
    def log_entry(self, trade_data: Dict, strategy: str, market_regime: str, 
                  stop_loss: float, take_profit_1: float, take_profit_2: float,
                  risk_reward: float, risk_amount: float) -> str:
        """
        Log a new trade entry
        
        Args:
            trade_data: Trade execution data
            strategy: Entry strategy used
            market_regime: Market regime at entry
            stop_loss: Stop loss price
            take_profit_1: First TP level
            take_profit_2: Second TP level
            risk_reward: RR ratio
            risk_amount: Amount at risk
            
        Returns:
            Entry ID
        """
        entry = JournalEntry(
            timestamp=datetime.now().isoformat(),
            symbol=trade_data['symbol'],
            action=trade_data['action'],
            strategy=strategy,
            market_regime=market_regime,
            entry_reason=trade_data.get('reason', ''),
            entry_price=trade_data['price'],
            shares=trade_data['shares'],
            total_value=trade_data['total'],
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            risk_reward=risk_reward,
            risk_amount=risk_amount
        )
        
        self.entries.append(entry)
        self._save_journal()
        
        logger.info(f"📝 Journal entry created: {entry.symbol} {entry.action} via {entry.strategy}")
        
        return entry.timestamp
    
    def log_exit(self, symbol: str, exit_data: Dict, notes: str = ""):
        """
        Log trade exit for most recent entry of symbol
        
        Args:
            symbol: Stock symbol
            exit_data: Exit trade data
            notes: Optional notes/lessons learned
        """
        # Find most recent open entry for this symbol
        for entry in reversed(self.entries):
            if entry.symbol == symbol and entry.exit_timestamp is None:
                entry.exit_timestamp = datetime.now().isoformat()
                entry.exit_price = exit_data['price']
                entry.exit_reason = exit_data.get('reason', '')
                entry.pnl = exit_data.get('pnl', 0)
                entry.pnl_percentage = exit_data.get('pnl_percentage', 0)
                entry.notes = notes
                
                # Track consecutive losses
                if entry.pnl < 0:
                    self.consecutive_losses += 1
                    logger.warning(f"📉 Consecutive losses: {self.consecutive_losses}")
                else:
                    self.consecutive_losses = 0  # Reset on win
                
                # Check for auto-pause
                if self.consecutive_losses >= 3:
                    self._trigger_auto_pause()
                
                self._save_journal()
                logger.info(f"📝 Journal exit logged: {symbol} P&L: {entry.pnl:+,.0f} VND")
                break
    
    def _trigger_auto_pause(self):
        """Trigger 48-hour auto pause after 3 consecutive losses"""
        self.pause_until = datetime.now() + timedelta(hours=48)
        self.pause_reason = f"3 lệnh thua liên tiếp - Cần nghỉ để review"
        
        logger.error(f"⏸️ AUTO PAUSE activated until {self.pause_until}")
        
        # Save pause state
        self._save_journal()
    
    def is_paused(self) -> bool:
        """Check if trading is currently paused"""
        if self.pause_until is None:
            return False
        
        if datetime.now() < self.pause_until:
            return True
        else:
            # Pause period ended
            logger.info("✅ Pause period ended, resuming trading")
            self.pause_until = None
            self.pause_reason = ""
            return False
    
    def manual_resume(self):
        """Manually resume trading (clear pause)"""
        self.pause_until = None
        self.pause_reason = ""
        self.consecutive_losses = 0
        self._save_journal()
        logger.info("✅ Trading resumed manually")
    
    def get_performance_summary(self) -> Dict:
        """Get performance analytics from journal"""
        if not self.entries:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_rr': 0,
                'total_pnl': 0,
                'best_strategy': 'N/A'
            }
        
        # Filter completed trades
        completed = [e for e in self.entries if e.exit_timestamp is not None]
        
        if not completed:
            return {
                'total_trades': len(self.entries),
                'open_positions': len([e for e in self.entries if e.exit_timestamp is None]),
                'win_rate': 0,
                'avg_rr': 0,
                'total_pnl': 0,
                'best_strategy': 'N/A'
            }
        
        # Calculate metrics
        wins = [e for e in completed if e.pnl > 0]
        losses = [e for e in completed if e.pnl < 0]
        
        win_rate = (len(wins) / len(completed)) * 100 if completed else 0
        avg_rr = sum(e.risk_reward for e in completed) / len(completed) if completed else 0
        total_pnl = sum(e.pnl for e in completed)
        
        # Best strategy
        strategy_pnl = {}
        for e in completed:
            if e.strategy not in strategy_pnl:
                strategy_pnl[e.strategy] = {'pnl': 0, 'count': 0}
            strategy_pnl[e.strategy]['pnl'] += e.pnl
            strategy_pnl[e.strategy]['count'] += 1
        
        best_strategy = max(strategy_pnl.items(), key=lambda x: x[1]['pnl'])[0] if strategy_pnl else 'N/A'
        
        return {
            'total_trades': len(completed),
            'open_positions': len([e for e in self.entries if e.exit_timestamp is None]),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': win_rate,
            'avg_rr': avg_rr,
            'total_pnl': total_pnl,
            'best_strategy': best_strategy,
            'consecutive_losses': self.consecutive_losses,
            'is_paused': self.is_paused(),
            'pause_until': self.pause_until.isoformat() if self.pause_until else None
        }
    
    def get_recent_trades(self, limit: int = 5) -> List[JournalEntry]:
        """Get recent trades"""
        return self.entries[-limit:] if self.entries else []
    
    def export_report(self) -> str:
        """Export journal as formatted report"""
        summary = self.get_performance_summary()
        
        report = f"""📊 *TRADE JOURNAL SUMMARY*

*Tổng quan:*
• Tổng giao dịch: {summary['total_trades']}
• Thắng: {summary.get('wins', 0)} | Thua: {summary.get('losses', 0)}
• Win rate: {summary['win_rate']:.1f}%
• Avg RR: {summary['avg_rr']:.2f}
• Tổng P&L: {summary['total_pnl']:+,.0f} VND

*Strategy tốt nhất:* {summary['best_strategy']}

"""
        
        # Recent trades
        recent = self.get_recent_trades(5)
        if recent:
            report += "*5 Giao dịch gần nhất:*\n"
            for e in recent:
                status = "✅" if e.pnl and e.pnl > 0 else "❌" if e.pnl else "🔄"
                pnl_str = f" ({e.pnl:+,.0f})" if e.pnl else " (Open)"
                report += f"{status} {e.symbol} {e.action} - {e.strategy}{pnl_str}\n"
        
        # Pause status
        if summary['is_paused']:
            report += f"\n⏸️ *PAUSED* đến {summary['pause_until']}\n"
            report += f"Lý do: {self.pause_reason}\n"
        
        return report
    
    def _save_journal(self):
        """Save journal to file"""
        try:
            data = {
                'entries': [asdict(e) for e in self.entries],
                'consecutive_losses': self.consecutive_losses,
                'pause_until': self.pause_until.isoformat() if self.pause_until else None,
                'pause_reason': self.pause_reason
            }
            
            with open(self.journal_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Journal saved to {self.journal_file}")
        except Exception as e:
            logger.error(f"Error saving journal: {e}")
    
    def _load_journal(self):
        """Load journal from file"""
        try:
            if Path(self.journal_file).exists():
                with open(self.journal_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load entries
                self.entries = [JournalEntry(**e) for e in data.get('entries', [])]
                
                # Load pause state
                self.consecutive_losses = data.get('consecutive_losses', 0)
                pause_until_str = data.get('pause_until')
                if pause_until_str:
                    self.pause_until = datetime.fromisoformat(pause_until_str)
                self.pause_reason = data.get('pause_reason', '')
                
                logger.info(f"Loaded {len(self.entries)} journal entries")
        except Exception as e:
            logger.error(f"Error loading journal: {e}")
            self.entries = []
