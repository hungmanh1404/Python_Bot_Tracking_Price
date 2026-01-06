"""
Sector Analyst Module
Monitors specific stocks with custom rules and generates daily reports
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os
from utils.logger import logger
from external_data_scraper import (
    BrentOilMonitor,
    ShanghaiSteelMonitor,
    VNStockFundamentalScraper,
    VNNewsScanner
)


class SectorAnalyst:
    """
    Sector Analyst - Monitors portfolio stocks with specific triggers
    """
    
    def __init__(self, config=None):
        """
        Initialize Sector Analyst
        
        Args:
            config: Configuration object (defaults to AutoTradingConfig)
        """
        if config is None:
            from auto_config import AutoTradingConfig
            config = AutoTradingConfig
        
        self.config = config
        
        # Initialize data monitors
        self.oil_monitor = BrentOilMonitor()
        self.steel_monitor = ShanghaiSteelMonitor()
        self.fundamental_scraper = VNStockFundamentalScraper()
        self.news_scanner = VNNewsScanner()
        
        # History file for tracking trends
        self.history_file = os.path.join(
            os.path.dirname(__file__),
            'data',
            'sector_history.json'
        )
        self._ensure_history_file()
    
    def _ensure_history_file(self):
        """Ensure history file and directory exist"""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump({
                    'brent_oil': {},
                    'hrc_steel': {},
                    'fpt_fundamentals': {},
                    'kbc_news': []
                }, f, indent=2)
    
    def _load_history(self) -> Dict:
        """Load historical data"""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return {'brent_oil': {}, 'hrc_steel': {}, 'fpt_fundamentals': {}, 'kbc_news': []}
    
    def _save_history(self, history: Dict):
        """Save historical data"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def monitor_fpt(self) -> Dict:
        """
        Monitor FPT stock
        - Alert if P/E < 18x (undervalued zone)
        - Alert if quarterly revenue growth < 15% (danger signal)
        
        Returns:
            Dict with monitoring results and alerts
        """
        logger.info("Monitoring FPT...")
        
        result = {
            'symbol': 'FPT',
            'pe_ratio': None,
            'revenue_growth': None,
            'alerts': [],
            'signals': [],
            'data_available': False
        }
        
        # Get fundamental data
        fpt_data = self.fundamental_scraper.get_fundamentals('FPT')
        
        if fpt_data:
            result['data_available'] = True
            result['pe_ratio'] = fpt_data.get('pe_ratio')
            result['revenue_growth'] = fpt_data.get('revenue_growth')
            result['data_source'] = fpt_data.get('source')
            
            # Check P/E ratio
            if result['pe_ratio']:
                pe_threshold = getattr(self.config, 'FPT_PE_THRESHOLD', 18.0)
                if result['pe_ratio'] < pe_threshold:
                    result['alerts'].append({
                        'type': 'BUY_ZONE',
                        'message': f"🟢 VÙNG MUA RẺ: P/E = {result['pe_ratio']:.1f}x (< {pe_threshold}x)",
                        'severity': 'positive'
                    })
                else:
                    result['signals'].append(f"P/E = {result['pe_ratio']:.1f}x (bình thường)")
            else:
                result['signals'].append("P/E: Dữ liệu không khả dụng")
            
            # Check revenue growth (if available)
            if result['revenue_growth'] is not None:
                growth_threshold = getattr(self.config, 'FPT_REVENUE_GROWTH_THRESHOLD', 15.0)
                if result['revenue_growth'] < growth_threshold:
                    result['alerts'].append({
                        'type': 'DANGER',
                        'message': f"🔴 CẢNH BÁO: Tăng trưởng doanh thu = {result['revenue_growth']:.1f}% (< {growth_threshold}%)",
                        'severity': 'negative'
                    })
                else:
                    result['signals'].append(f"Tăng trưởng doanh thu: {result['revenue_growth']:.1f}% (tốt)")
            else:
                result['signals'].append("Tăng trưởng doanh thu: Dữ liệu không khả dụng")
        else:
            result['alerts'].append({
                'type': 'DATA_UNAVAILABLE',
                'message': "⚠️ Không lấy được dữ liệu fundamental cho FPT",
                'severity': 'warning'
            })
        
        return result
    
    def monitor_pvs(self) -> Dict:
        """
        Monitor PVS stock based on Brent oil prices
        - Signal BUY if Brent > $85 and stable for 1 week
        
        Returns:
            Dict with monitoring results and signals
        """
        logger.info("Monitoring PVS (via Brent oil)...")
        
        result = {
            'symbol': 'PVS',
            'brent_price': None,
            'brent_trend': None,
            'alerts': [],
            'signals': [],
            'data_available': False
        }
        
        # Get current Brent price
        oil_data = self.oil_monitor.get_current_price()
        
        if oil_data:
            result['data_available'] = True
            result['brent_price'] = oil_data['price']
            result['data_source'] = oil_data['source']
            
            # Save to history
            history = self._load_history()
            today = datetime.now().strftime('%Y-%m-%d')
            history['brent_oil'][today] = oil_data['price']
            
            # Keep only last 30 days
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            history['brent_oil'] = {
                k: v for k, v in history['brent_oil'].items()
                if k >= cutoff_date
            }
            self._save_history(history)
            
            # Check for stable high price (> $85 for 7 days)
            threshold = getattr(self.config, 'PVS_BRENT_THRESHOLD', 85.0)
            days_stable = getattr(self.config, 'PVS_BRENT_DAYS_STABLE', 7)
            
            # Get last 7 days of prices
            recent_prices = list(history['brent_oil'].values())[-days_stable:]
            
            if len(recent_prices) >= days_stable:
                all_above_threshold = all(price > threshold for price in recent_prices)
                
                if all_above_threshold:
                    result['alerts'].append({
                        'type': 'BUY_SIGNAL',
                        'message': f"🟢 TÍN HIỆU MUA PVS: Brent > ${threshold} và giữ vững {days_stable} ngày",
                        'severity': 'positive'
                    })
                    result['brent_trend'] = 'stable_high'
                else:
                    avg_price = sum(recent_prices) / len(recent_prices)
                    result['signals'].append(f"Brent trung bình 7 ngày: ${avg_price:.2f}")
                    result['brent_trend'] = 'normal'
            else:
                result['signals'].append(f"Cần thêm {days_stable - len(recent_prices)} ngày dữ liệu để xác định xu hướng")
                result['brent_trend'] = 'insufficient_data'
            
            # Current price status
            if result['brent_price'] > threshold:
                result['signals'].append(f"Giá hiện tại: ${result['brent_price']} (> ${threshold})")
            else:
                result['signals'].append(f"Giá hiện tại: ${result['brent_price']} (< ${threshold})")
        else:
            result['alerts'].append({
                'type': 'DATA_UNAVAILABLE',
                'message': "⚠️ Không lấy được giá dầu Brent",
                'severity': 'warning'
            })
        
        return result
    
    def monitor_kbc(self) -> Dict:
        """
        Monitor KBC stock via news scanning
        - Scan for keywords: 'KBC ký biên bản ghi nhớ', 'Foxconn', 'LG Innotek'
        - Alert immediately if found
        
        Returns:
            Dict with monitoring results and news alerts
        """
        logger.info("Monitoring KBC (via news scanning)...")
        
        result = {
            'symbol': 'KBC',
            'news_found': 0,
            'articles': [],
            'alerts': [],
            'signals': [],
            'data_available': False
        }
        
        # Get keywords from config
        keywords = getattr(self.config, 'KBC_KEYWORDS', [
            'KBC ký biên bản ghi nhớ',
            'Foxconn',
            'LG Innotek'
        ])
        
        # Scan news
        news_data = self.news_scanner.scan_for_keywords('KBC', keywords, days=7)
        
        if news_data:
            result['data_available'] = True
            result['news_found'] = news_data['articles_found']
            result['articles'] = news_data['articles']
            result['data_source'] = news_data['source']
            
            if result['news_found'] > 0:
                result['alerts'].append({
                    'type': 'NEWS_ALERT',
                    'message': f"🔔 TIN TỨC QUAN TRỌNG: Tìm thấy {result['news_found']} bài viết về KBC",
                    'severity': 'positive'
                })
                
                # List top articles
                for i, article in enumerate(result['articles'][:3], 1):
                    result['signals'].append(
                        f"{i}. {article['title']} ({article['source']})"
                    )
            else:
                result['signals'].append("Không có tin tức đặc biệt trong 7 ngày qua")
        else:
            result['alerts'].append({
                'type': 'DATA_UNAVAILABLE',
                'message': "⚠️ Không quét được tin tức cho KBC",
                'severity': 'warning'
            })
        
        return result
    
    def monitor_hpg(self) -> Dict:
        """
        Monitor HPG stock via Shanghai steel HRC prices
        - Signal BUY if HRC increases for 2 consecutive weeks
        
        Returns:
            Dict with monitoring results and signals
        """
        logger.info("Monitoring HPG (via Shanghai HRC)...")
        
        result = {
            'symbol': 'HPG',
            'hrc_price': None,
            'hrc_trend': None,
            'alerts': [],
            'signals': [],
            'data_available': False
        }
        
        # Get current HRC price
        steel_data = self.steel_monitor.get_current_price()
        
        if steel_data:
            result['data_available'] = True
            result['hrc_price'] = steel_data['price']
            result['data_source'] = steel_data['source']
            
            # Save to history (weekly basis)
            history = self._load_history()
            
            # Get current week number
            current_week = datetime.now().strftime('%Y-W%U')
            history['hrc_steel'][current_week] = steel_data['price']
            
            # Keep only last 12 weeks
            all_weeks = sorted(history['hrc_steel'].keys())
            if len(all_weeks) > 12:
                history['hrc_steel'] = {
                    k: history['hrc_steel'][k] for k in all_weeks[-12:]
                }
            self._save_history(history)
            
            # Check for consecutive increases
            weeks_threshold = getattr(self.config, 'HPG_HRC_WEEKS_INCREASE', 2)
            recent_weeks = sorted(history['hrc_steel'].keys())[-weeks_threshold-1:]
            
            if len(recent_weeks) >= weeks_threshold + 1:
                recent_prices = [history['hrc_steel'][w] for w in recent_weeks]
                
                # Check if prices are increasing
                is_increasing = all(
                    recent_prices[i] < recent_prices[i+1]
                    for i in range(len(recent_prices) - 1)
                )
                
                if is_increasing:
                    result['alerts'].append({
                        'type': 'BUY_SIGNAL',
                        'message': f"🟢 TÍN HIỆU MUA HPG: Giá thép HRC tăng {weeks_threshold} tuần liên tiếp",
                        'severity': 'positive'
                    })
                    result['hrc_trend'] = 'increasing'
                    
                    # Show price progression
                    for i, (week, price) in enumerate(zip(recent_weeks, recent_prices)):
                        result['signals'].append(f"Tuần {i+1}: {price:.2f} CNY/tấn")
                else:
                    result['signals'].append("Giá thép chưa có xu hướng tăng liên tục")
                    result['hrc_trend'] = 'mixed'
            else:
                result['signals'].append(f"Cần thêm {weeks_threshold + 1 - len(recent_weeks)} tuần dữ liệu")
                result['hrc_trend'] = 'insufficient_data'
            
            result['signals'].append(f"Giá hiện tại: {result['hrc_price']:.2f} CNY/tấn")
        else:
            result['alerts'].append({
                'type': 'DATA_UNAVAILABLE',
                'message': "⚠️ Không lấy được giá thép HRC từ Thượng Hải",
                'severity': 'warning'
            })
        
        return result
    
    def generate_daily_report(self, dry_run: bool = False) -> str:
        """
        Generate comprehensive daily sector analysis report
        
        Args:
            dry_run: If True, only print report without sending
            
        Returns:
            Formatted report string
        """
        logger.info("Generating daily sector analysis report...")
        
        # Monitor all stocks
        fpt_result = self.monitor_fpt()
        pvs_result = self.monitor_pvs()
        kbc_result = self.monitor_kbc()
        hpg_result = self.monitor_hpg()
        
        # Build report
        report_lines = [
            "📊 BÁO CÁO PHÂN TÍCH NGÀNH",
            f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "=" * 40,
            ""
        ]
        
        # FPT Section
        report_lines.append("🏢 FPT - Công nghệ")
        report_lines.append("-" * 40)
        if fpt_result['data_available']:
            for alert in fpt_result['alerts']:
                report_lines.append(alert['message'])
            for signal in fpt_result['signals']:
                report_lines.append(f"  • {signal}")
            report_lines.append(f"  Nguồn: {fpt_result.get('data_source', 'N/A')}")
        else:
            report_lines.append("  ⚠️ Dữ liệu không khả dụng")
        report_lines.append("")
        
        # PVS Section
        report_lines.append("⛽ PVS - Dịch vụ dầu khí")
        report_lines.append("-" * 40)
        if pvs_result['data_available']:
            for alert in pvs_result['alerts']:
                report_lines.append(alert['message'])
            for signal in pvs_result['signals']:
                report_lines.append(f"  • {signal}")
            report_lines.append(f"  Nguồn: {pvs_result.get('data_source', 'N/A')}")
        else:
            report_lines.append("  ⚠️ Dữ liệu không khả dụng")
        report_lines.append("")
        
        # KBC Section
        report_lines.append("🔧 KBC - Xây dựng & Cơ khí")
        report_lines.append("-" * 40)
        if kbc_result['data_available']:
            for alert in kbc_result['alerts']:
                report_lines.append(alert['message'])
            for signal in kbc_result['signals']:
                report_lines.append(f"  • {signal}")
            if kbc_result['articles']:
                report_lines.append("  📰 Tin tức nổi bật:")
                for article in kbc_result['articles'][:3]:
                    report_lines.append(f"    - {article['title']}")
                    report_lines.append(f"      {article['link']}")
            report_lines.append(f"  Nguồn: {kbc_result.get('data_source', 'N/A')}")
        else:
            report_lines.append("  ⚠️ Dữ liệu không khả dụng")
        report_lines.append("")
        
        # HPG Section
        report_lines.append("🏗️ HPG - Thép")
        report_lines.append("-" * 40)
        if hpg_result['data_available']:
            for alert in hpg_result['alerts']:
                report_lines.append(alert['message'])
            for signal in hpg_result['signals']:
                report_lines.append(f"  • {signal}")
            report_lines.append(f"  Nguồn: {hpg_result.get('data_source', 'N/A')}")
        else:
            report_lines.append("  ⚠️ Dữ liệu không khả dụng")
        report_lines.append("")
        
        # Summary
        report_lines.append("=" * 40)
        total_alerts = (
            len(fpt_result['alerts']) +
            len(pvs_result['alerts']) +
            len(kbc_result['alerts']) +
            len(hpg_result['alerts'])
        )
        
        # Count buy signals
        buy_signals = []
        for result in [fpt_result, pvs_result, kbc_result, hpg_result]:
            for alert in result['alerts']:
                if alert['type'] in ['BUY_ZONE', 'BUY_SIGNAL']:
                    buy_signals.append(result['symbol'])
        
        if buy_signals:
            report_lines.append(f"✅ TÍN HIỆU TÍCH CỰC: {', '.join(buy_signals)}")
        else:
            report_lines.append("⚪ Không có tín hiệu đặc biệt")
        
        report_lines.append(f"📬 Tổng số cảnh báo: {total_alerts}")
        report_lines.append("")
        report_lines.append("💡 Lưu ý: Đây là phân tích tự động, vui lòng xác minh trước khi đầu tư.")
        
        report = "\n".join(report_lines)
        
        if dry_run:
            print("\n" + report + "\n")
        
        return report


# Test function
if __name__ == "__main__":
    print("=== Testing Sector Analyst ===\n")
    
    analyst = SectorAnalyst()
    report = analyst.generate_daily_report(dry_run=True)
    
    print("\n=== Test Complete ===")
