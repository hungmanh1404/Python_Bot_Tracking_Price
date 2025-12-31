"""
Report Generator Module
Formats analysis results for Telegram messages
"""
from typing import List, Dict
from datetime import datetime

class ReportGenerator:
    """Generates formatted reports for Telegram"""
    
    def __init__(self):
        self.max_message_length = 4000  # Telegram limit is 4096
    
    def generate_daily_report(self, analyses: List[Dict], market_context: str = "") -> str:
        """
        Generate daily report for all stocks
        
        Args:
            analyses: List of analysis results
            market_context: General market context
            
        Returns:
            Formatted report string
        """
        report_parts = []
        
        # Header
        header = self._generate_header()
        report_parts.append(header)
        
        # Market context (if provided)
        if market_context:
            report_parts.append(f"📊 *THỊ TRƯỜNG:* {market_context}\n")
        
        report_parts.append("═" * 40 + "\n")
        
        # Individual stock analyses
        for analysis in analyses:
            stock_report = self._generate_stock_report(analysis)
            report_parts.append(stock_report)
            report_parts.append("─" * 40 + "\n")
        
        # Summary table
        summary = self._generate_summary_table(analyses)
        report_parts.append(summary)
        
        # Footer
        footer = self._generate_footer()
        report_parts.append(footer)
        
        full_report = "\n".join(report_parts)
        
        # Check if report exceeds Telegram limit
        if len(full_report) > self.max_message_length:
            return self._truncate_report(full_report)
        
        return full_report
    
    def _generate_header(self) -> str:
        """Generate report header"""
        now = datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%H:%M")
        
        return f"""🎯 *BÁO CÁO PHÂN TÍCH CỔ PHIẾU*
📅 Ngày: {date_str} | ⏰ {time_str}
🤖 _Phân tích tự động theo phương pháp 3-Agent_

"""
    
    def _generate_stock_report(self, analysis: Dict) -> str:
        """Generate report for a single stock"""
        symbol = analysis['symbol']
        decision = analysis['decision']
        confidence = analysis['confidence']
        
        # Main info
        lines = [
            f"*📈 {symbol}*",
            f"*Quyết định:* {decision}",
            f"*Độ tin cậy:* {confidence}/100 {'🔥' if confidence >= 75 else '⚠️' if confidence >= 60 else '❄️'}",
            ""
        ]
        
        # Bullish points
        if analysis['bullish_case']:
            lines.append("*🐂 Điểm tích cực:*")
            for point in analysis['bullish_case'][:3]:  # Top 3
                lines.append(f"  • {point}")
            lines.append("")
        
        # Bearish points
        if analysis['bearish_case']:
            lines.append("*🐻 Rủi ro:*")
            for point in analysis['bearish_case'][:3]:  # Top 3
                lines.append(f"  • {point}")
            lines.append("")
        
        # Trading info (if applicable)
        if analysis['entry_zone'] != "N/A":
            lines.append("*📊 Thông tin giao dịch:*")
            lines.append(f"  • *Entry:* {analysis['entry_zone']}")
            lines.append(f"  • *Stop Loss:* {analysis['stop_loss']}")
            if analysis['targets']:
                lines.append(f"  • *Targets:* {', '.join(analysis['targets'][:2])}")
            lines.append(f"  • *R:R Ratio:* 1:{analysis['risk_reward']:.1f}")
            lines.append("")
        
        # Reasoning
        lines.append(f"💡 _{analysis['reasoning']}_")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_summary_table(self, analyses: List[Dict]) -> str:
        """Generate summary comparison table"""
        lines = [
            "📋 *TỔNG KẾT*",
            "```"
        ]
        
        # Header
        lines.append(f"{'Mã':<6} {'Action':<12} {'Conf':<5} {'R:R':<5}")
        lines.append("-" * 32)
        
        # Rows
        for analysis in analyses:
            symbol = analysis['symbol']
            action_emoji = self._get_action_emoji(analysis['decision'])
            conf = f"{analysis['confidence']}"
            rr = f"1:{analysis['risk_reward']:.1f}" if analysis['risk_reward'] > 0 else "N/A"
            
            lines.append(f"{symbol:<6} {action_emoji:<12} {conf:<5} {rr:<5}")
        
        lines.append("```")
        lines.append("")
        
        # Recommendations
        buy_stocks = [a['symbol'] for a in analyses if '🟢' in a['decision']]
        watch_stocks = [a['symbol'] for a in analyses if '🟡' in a['decision']]
        
        if buy_stocks:
            lines.append(f"✅ *Khuyến nghị MUA:* {', '.join(buy_stocks)}")
        if watch_stocks:
            lines.append(f"👀 *Theo dõi:* {', '.join(watch_stocks)}")
        
        return "\n".join(lines)
    
    def _generate_footer(self) -> str:
        """Generate report footer"""
        return """\n
⚠️ *Lưu ý:* Đây là phân tích tham khảo. 
Luôn DYOR và quản lý rủi ro cẩn thận.

_Powered by Stock Analyzer Bot v1.0_ 🤖"""
    
    def _get_action_emoji(self, decision: str) -> str:
        """Extract emoji from decision"""
        if '🟢' in decision:
            return '🟢 MUA'
        elif '🟡' in decision:
            return '🟡 CHỜ'
        elif '⚪' in decision:
            return '⚪ CHỜ'
        else:
            return '🔴 OUT'
    
    def _truncate_report(self, report: str) -> str:
        """Truncate report if too long"""
        return report[:self.max_message_length - 100] + "\n\n... (Báo cáo đã được rút gọn)"
