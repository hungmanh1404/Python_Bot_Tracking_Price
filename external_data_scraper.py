"""
External Data Scraper Module
Collects data from external sources: commodities, futures, fundamentals, and news
"""
import requests
import feedparser
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from utils.logger import logger
import os
import json
import re


class BrentOilMonitor:
    """Monitor Brent crude oil prices"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('COMMODITIES_API_KEY', '')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def get_current_price(self) -> Optional[Dict]:
        """
        Get current Brent crude oil price
        
        Returns:
            Dict with price, source, and timestamp or None if failed
        """
        # Try API first if available
        if self.api_key:
            try:
                result = self._fetch_from_api()
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Commodities API failed: {e}")
        
        # Fallback to web scraping
        try:
            result = self._scrape_from_investing()
            if result:
                return result
        except Exception as e:
            logger.error(f"Failed to get Brent oil price: {e}")
        
        return None
    
    def _fetch_from_api(self) -> Optional[Dict]:
        """Fetch from Commodities-API"""
        try:
            url = "https://commodities-api.com/api/latest"
            params = {
                'access_key': self.api_key,
                'base': 'USD',
                'symbols': 'BRENT'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('rates', {}).get('BRENT'):
                    # API returns inverse rate (USD per barrel)
                    brent_rate = 1 / data['rates']['BRENT']
                    
                    return {
                        'price': round(brent_rate, 2),
                        'currency': 'USD',
                        'source': 'Commodities-API',
                        'timestamp': datetime.now().isoformat(),
                        'is_real': True
                    }
        except Exception as e:
            logger.debug(f"Commodities API error: {e}")
        
        return None
    
    def _scrape_from_investing(self) -> Optional[Dict]:
        """Scrape Brent price from Investing.com"""
        try:
            url = "https://www.investing.com/commodities/brent-oil"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to find price element (structure may vary)
                price_elem = soup.find('span', {'data-test': 'instrument-price-last'})
                if not price_elem:
                    price_elem = soup.find('span', class_=re.compile(r'text-\d+xl'))
                
                if price_elem:
                    price_text = price_elem.get_text().strip().replace(',', '')
                    price = float(price_text)
                    
                    return {
                        'price': round(price, 2),
                        'currency': 'USD',
                        'source': 'Investing.com (scraped)',
                        'timestamp': datetime.now().isoformat(),
                        'is_real': True
                    }
        except Exception as e:
            logger.debug(f"Investing.com scraping error: {e}")
        
        return None


class ShanghaiSteelMonitor:
    """Monitor Shanghai Futures HRC (Hot Rolled Coil) steel prices"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def get_current_price(self) -> Optional[Dict]:
        """
        Get current HRC steel price from Shanghai Futures
        
        Returns:
            Dict with price, source, and timestamp or None if failed
        """
        # Try scraping from public sources
        try:
            result = self._scrape_from_smm()
            if result:
                return result
        except Exception as e:
            logger.warning(f"SMM scraping failed: {e}")
        
        try:
            result = self._scrape_from_mysteel()
            if result:
                return result
        except Exception as e:
            logger.warning(f"Mysteel scraping failed: {e}")
        
        logger.error("Failed to get Shanghai HRC steel price from all sources")
        return None
    
    def _scrape_from_smm(self) -> Optional[Dict]:
        """Scrape from Shanghai Metals Market"""
        try:
            # This is a placeholder - actual URL needs verification
            url = "https://www.metal.com/price/China/HRC"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to find HRC price (structure may vary)
                # This is a generic approach - may need adjustment
                price_elem = soup.find('span', class_=re.compile(r'price'))
                if price_elem:
                    price_text = price_elem.get_text().strip().replace(',', '')
                    price = float(price_text)
                    
                    return {
                        'price': round(price, 2),
                        'currency': 'CNY',
                        'unit': 'ton',
                        'source': 'Shanghai Metals Market (scraped)',
                        'timestamp': datetime.now().isoformat(),
                        'is_real': True
                    }
        except Exception as e:
            logger.debug(f"SMM scraping error: {e}")
        
        return None
    
    def _scrape_from_mysteel(self) -> Optional[Dict]:
        """Scrape from Mysteel.com (alternative source)"""
        try:
            # Placeholder for alternative source
            # May require more research to find accessible public data
            logger.debug("Mysteel scraping not yet implemented")
            return None
        except Exception as e:
            logger.debug(f"Mysteel scraping error: {e}")
        
        return None


class VNStockFundamentalScraper:
    """Scrape Vietnamese stock fundamental data (P/E, revenue growth)"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def get_fundamentals(self, symbol: str) -> Optional[Dict]:
        """
        Get fundamental data for a Vietnamese stock
        
        Args:
            symbol: Stock symbol (e.g., 'FPT')
            
        Returns:
            Dict with P/E, revenue growth, etc. or None if failed
        """
        # Try CafeF first
        try:
            result = self._scrape_from_cafef(symbol)
            if result:
                return result
        except Exception as e:
            logger.warning(f"CafeF scraping failed for {symbol}: {e}")
        
        # Try VNDirect as fallback
        try:
            result = self._scrape_from_vndirect(symbol)
            if result:
                return result
        except Exception as e:
            logger.warning(f"VNDirect scraping failed for {symbol}: {e}")
        
        logger.error(f"Failed to get fundamentals for {symbol}")
        return None
    
    def _scrape_from_cafef(self, symbol: str) -> Optional[Dict]:
        """Scrape from CafeF"""
        try:
            url = f"https://s.cafef.vn/hose/{symbol}-ctck.chn"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                pe_ratio = None
                revenue_growth = None
                
                # Try to find P/E ratio
                # Look for table rows with P/E data
                rows = soup.find_all('tr')
                for row in rows:
                    text = row.get_text()
                    if 'P/E' in text:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            try:
                                pe_text = cells[1].get_text().strip().replace(',', '')
                                pe_ratio = float(pe_text)
                            except:
                                pass
                
                # Note: Revenue growth is harder to scrape - may need financial reports
                # For now, we'll mark it as unavailable
                
                if pe_ratio:
                    return {
                        'symbol': symbol,
                        'pe_ratio': pe_ratio,
                        'revenue_growth': None,  # Not available from basic scraping
                        'source': 'CafeF (scraped)',
                        'timestamp': datetime.now().isoformat(),
                        'is_real': True
                    }
        except Exception as e:
            logger.debug(f"CafeF scraping error for {symbol}: {e}")
        
        return None
    
    def _scrape_from_vndirect(self, symbol: str) -> Optional[Dict]:
        """Scrape from VNDirect"""
        try:
            url = f"https://dchart.vndirect.com.vn/StockInPlay/{symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to extract P/E from JSON data or HTML elements
                # This is a placeholder - actual implementation depends on VNDirect's structure
                logger.debug(f"VNDirect scraping for {symbol} needs structure analysis")
                
        except Exception as e:
            logger.debug(f"VNDirect scraping error for {symbol}: {e}")
        
        return None


class VNNewsScanner:
    """Scan Vietnamese business news for specific keywords"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def scan_for_keywords(self, symbol: str, keywords: List[str], days: int = 7) -> Optional[Dict]:
        """
        Scan news for specific keywords related to a stock
        
        Args:
            symbol: Stock symbol (e.g., 'KBC')
            keywords: List of keywords to search for
            days: Number of days to look back
            
        Returns:
            Dict with found articles or None
        """
        found_articles = []
        
        # Scan CafeF RSS
        try:
            cafef_articles = self._scan_cafef_rss(symbol, keywords, days)
            found_articles.extend(cafef_articles)
        except Exception as e:
            logger.warning(f"CafeF RSS scan failed: {e}")
        
        # Scan VnExpress RSS
        try:
            vnexpress_articles = self._scan_vnexpress_rss(symbol, keywords, days)
            found_articles.extend(vnexpress_articles)
        except Exception as e:
            logger.warning(f"VnExpress RSS scan failed: {e}")
        
        if found_articles:
            return {
                'symbol': symbol,
                'keywords': keywords,
                'articles_found': len(found_articles),
                'articles': found_articles[:5],  # Top 5 most relevant
                'source': 'RSS Feeds (CafeF, VnExpress)',
                'timestamp': datetime.now().isoformat(),
                'is_real': True
            }
        
        return {
            'symbol': symbol,
            'keywords': keywords,
            'articles_found': 0,
            'articles': [],
            'source': 'RSS Feeds (CafeF, VnExpress)',
            'timestamp': datetime.now().isoformat(),
            'is_real': True
        }
    
    def _scan_cafef_rss(self, symbol: str, keywords: List[str], days: int) -> List[Dict]:
        """Scan CafeF RSS feed"""
        found = []
        try:
            # CafeF business RSS feed
            feed_url = "https://cafef.vn/timeline.rss"
            feed = feedparser.parse(feed_url)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for entry in feed.entries:
                # Check if article is recent
                published = entry.get('published_parsed')
                if published:
                    pub_date = datetime(*published[:6])
                    if pub_date < cutoff_date:
                        continue
                
                # Check for keywords in title or summary
                title = entry.get('title', '').lower()
                summary = entry.get('summary', '').lower()
                symbol_lower = symbol.lower()
                
                # Check if symbol or keywords are mentioned
                matched_keywords = []
                if symbol_lower in title or symbol_lower in summary:
                    for keyword in keywords:
                        if keyword.lower() in title or keyword.lower() in summary:
                            matched_keywords.append(keyword)
                
                if matched_keywords:
                    found.append({
                        'title': entry.get('title'),
                        'link': entry.get('link'),
                        'published': entry.get('published'),
                        'matched_keywords': matched_keywords,
                        'source': 'CafeF'
                    })
        
        except Exception as e:
            logger.debug(f"CafeF RSS error: {e}")
        
        return found
    
    def _scan_vnexpress_rss(self, symbol: str, keywords: List[str], days: int) -> List[Dict]:
        """Scan VnExpress business RSS feed"""
        found = []
        try:
            # VnExpress business RSS feed
            feed_url = "https://vnexpress.net/rss/kinh-doanh.rss"
            feed = feedparser.parse(feed_url)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for entry in feed.entries:
                # Check if article is recent
                published = entry.get('published_parsed')
                if published:
                    pub_date = datetime(*published[:6])
                    if pub_date < cutoff_date:
                        continue
                
                # Check for keywords in title or description
                title = entry.get('title', '').lower()
                description = entry.get('description', '').lower()
                symbol_lower = symbol.lower()
                
                # Check if symbol or keywords are mentioned  
                matched_keywords = []
                if symbol_lower in title or symbol_lower in description:
                    for keyword in keywords:
                        if keyword.lower() in title or keyword.lower() in description:
                            matched_keywords.append(keyword)
                
                if matched_keywords:
                    found.append({
                        'title': entry.get('title'),
                        'link': entry.get('link'),
                        'published': entry.get('published'),
                        'matched_keywords': matched_keywords,
                        'source': 'VnExpress'
                    })
        
        except Exception as e:
            logger.debug(f"VnExpress RSS error: {e}")
        
        return found


# Test functions for manual verification
if __name__ == "__main__":
    print("=== Testing External Data Scrapers ===\n")
    
    # Test Brent Oil Monitor
    print("1. Testing Brent Oil Monitor...")
    oil_monitor = BrentOilMonitor()
    oil_data = oil_monitor.get_current_price()
    if oil_data:
        print(f"   ✓ Brent Oil: ${oil_data['price']} ({oil_data['source']})")
    else:
        print("   ✗ Brent Oil: Data unavailable")
    
    # Test Shanghai Steel Monitor
    print("\n2. Testing Shanghai Steel Monitor...")
    steel_monitor = ShanghaiSteelMonitor()
    steel_data = steel_monitor.get_current_price()
    if steel_data:
        print(f"   ✓ HRC Steel: {steel_data['price']} {steel_data['currency']}/{steel_data['unit']} ({steel_data['source']})")
    else:
        print("   ✗ HRC Steel: Data unavailable")
    
    # Test VN Stock Fundamentals
    print("\n3. Testing VN Stock Fundamental Scraper...")
    fundamental_scraper = VNStockFundamentalScraper()
    fpt_data = fundamental_scraper.get_fundamentals('FPT')
    if fpt_data:
        print(f"   ✓ FPT P/E: {fpt_data.get('pe_ratio', 'N/A')} ({fpt_data['source']})")
    else:
        print("   ✗ FPT Fundamentals: Data unavailable")
    
    # Test News Scanner
    print("\n4. Testing VN News Scanner...")
    news_scanner = VNNewsScanner()
    kbc_news = news_scanner.scan_for_keywords('KBC', ['Foxconn', 'LG Innotek', 'biên bản ghi nhớ'], days=7)
    if kbc_news and kbc_news['articles_found'] > 0:
        print(f"   ✓ Found {kbc_news['articles_found']} articles about KBC")
        for article in kbc_news['articles'][:3]:
            print(f"     - {article['title']}")
    else:
        print("   ✗ No recent news found for KBC with specified keywords")
    
    print("\n=== Test Complete ===")
