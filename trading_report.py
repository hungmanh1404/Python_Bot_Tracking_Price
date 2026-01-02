"""
Paper Trading Report Generator
Formats trading results for Telegram
"""
from typing import Dict

class TradingReportGenerator:
    """Generates trading performance reports"""
    
    def generate_trading_report(self, performance: Dict) -> str:
        """Generate formatted trading report"""
        lines = []
        
        # Header
        lines.append("💰 *BÁO CÁO GIAO DỊCH THỬ NGHIỆM*")
        lines.append("_Paper Trading với Chiến lược 3-Agent_")
        lines.append("")
        lines.append("═" * 40)
        lines.append("")
        
        # Capital summary
        initial = performance['initial_capital']
        current = performance['current_value']
        pnl = performance['total_pnl']
        return_pct = performance['total_return_pct']
        
        # Determine emoji based on performance
        if pnl > 0:
            emoji = "🟢 📈"
            status = "LỜI"
        elif pnl < 0:
            emoji = "🔴 📉"
            status = "LỖ"
        else:
            emoji = "⚪"
            status = "HÒA VỐN"
        
        lines.append("*📊 TỔNG KẾT DANH MỤC*")
        lines.append(f"• Vốn ban đầu: *{initial:,.0f} VNĐ*")
        lines.append(f"• Giá trị hiện tại: *{current:,.0f} VNĐ*")
        lines.append(f"• Tiền mặt còn: *{performance['cash']:,.0f} VNĐ*")
        lines.append("")
        lines.append(f"{emoji} *{status}: {pnl:+,.0f} VNĐ ({return_pct:+.2f}%)*")
        lines.append("")
        lines.append("─" * 40)
        lines.append("")
        
        # Positions
        if performance['positions']:
            lines.append("*📁 VỊ THẾ ĐANG GIỮ*")
            lines.append("```")
            lines.append(f"{'Mã':<6} {'SL':<6} {'Giá TB':<8} {'Giá HT':<8} {'P&L %'}")
            lines.append("-" * 42)
            
            for symbol, pos in performance['positions'].items():
                shares = pos['shares']
                avg = pos['avg_price']
                current_price = pos['current_price']
                pnl_pct = pos['pnl_percentage']
                
                pnl_sign = "+" if pnl_pct >= 0 else ""
                lines.append(f"{symbol:<6} {shares:<6} {avg:<8,.0f} {current_price:<8,.0f} {pnl_sign}{pnl_pct:.2f}%")
            
            lines.append("```")
            lines.append("")
            
            # Detailed position P&L
            lines.append("*Chi tiết vị thế:*")
            for symbol, pos in performance['positions'].items():
                pnl_emoji = "🟢" if pos['pnl'] >= 0 else "🔴"
                lines.append(f"{pnl_emoji} *{symbol}*: {pos['pnl']:+,.0f} VNĐ")
            lines.append("")
        else:
            lines.append("*📁 VỊ THẾ:* Không có vị thế mở")
            lines.append("")
        
        lines.append("─" * 40)
        lines.append("")
        
        # Trading activity
        lines.append(f"*📈 HOẠT ĐỘNG GIAO DỊCH*")
        lines.append(f"• Tổng số lệnh: {performance['num_trades']}")
        
        if performance['trades']:
            lines.append("")
            lines.append("*Lịch sử giao dịch:*")
            
            # Show recent trades (up to 10)
            recent_trades = performance['trades'][-10:]
            for trade in recent_trades:
                action_emoji = "🟢 ↗" if trade['action'] == 'BUY' else "🔴 ↘"
                symbol = trade['symbol']
                shares = trade['shares']
                price = trade['price']
                
                line = f"{action_emoji} {trade['action']} {shares} {symbol} @ {price:,.0f}"
                
                if trade['action'] == 'SELL' and 'pnl' in trade:
                    pnl = trade['pnl']
                    pnl_pct = trade['pnl_percentage']
                    line += f" (P&L: {pnl:+,.0f}, {pnl_pct:+.2f}%)"
                
                lines.append(f"  {line}")
        
        lines.append("")
        lines.append("═" * 40)
        lines.append("")
        
        # Verdict
        lines.append("*🎯 KẾT LUẬN*")
        
        if return_pct > 10:
            verdict = "Chiến lược hoạt động RẤT TỐT! 🎉"
        elif return_pct > 5:
            verdict = "Chiến lược hoạt động tốt! 👍"
        elif return_pct > 0:
            verdict = "Chiến lược có lời nhẹ. Cần theo dõi thêm."
        elif return_pct > -5:
            verdict = "Chiến lược lỗ nhẹ. Cần điều chỉnh."
        else:
            verdict = "Chiến lược cần xem xét lại! ⚠️"
        
        lines.append(verdict)
        lines.append("")
        lines.append("⚠️ _Đây là mô phỏng paper trading._")
        lines.append("_Kết quả thực tế có thể khác do slippage, phí..._")
        
        return "\n".join(lines)
