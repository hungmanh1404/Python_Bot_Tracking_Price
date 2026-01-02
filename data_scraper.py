"""
Data Scraper Module
Collects real-time stock data from web sources
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from utils.logger import logger
import time
import random
from datetime import datetime

class StockDataScraper:
    """Scrapes stock data from various sources"""
    
    # Base prices for mock data (in VND)
    MOCK_BASE_PRICES = {
        'FPT': 120000,
        'PVS': 25000,
        'KBC': 35000,
        'HPG': 28000,
    }
    
    def __init__(self, data_mode='demo'):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.data_mode = data_mode
        self.mock_prices = self.MOCK_BASE_PRICES.copy()  # Track mock prices for continuity
        
        # Initialize with small random variation
        for symbol in self.mock_prices:
            variation = random.uniform(-0.02, 0.02)  # ±2%
            self.mock_prices[symbol] = self.mock_prices[symbol] * (1 + variation)
    
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """
        Get comprehensive stock data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'FPT', 'PVS')
            
        Returns:
            Dictionary containing stock data or None if failed
        """
        try:
            logger.info(f"Fetching data for {symbol}...")
            
            # Use mock data if in demo mode
            if self.data_mode == 'demo':
                data = self._get_mock_data(symbol)
                if data:
                    logger.info(f"Successfully fetched mock data for {symbol}")
                    return data
            
            # Try multiple sources with fallback for real data
            data = self._fetch_from_cafef(symbol)
            if not data:
                data = self._fetch_from_vietstock(symbol)
            
            if data:
                logger.info(f"Successfully fetched data for {symbol}")
                return data
            else:
                logger.warning(f"Could not fetch data for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def _get_mock_data(self, symbol: str) -> Optional[Dict]:
        """Generate realistic mock stock data for testing"""
        try:
            if symbol not in self.MOCK_BASE_PRICES:
                logger.warning(f"No mock data available for {symbol}")
                return None
            
            # Simulate small price movement (±0.5%)
            change_pct = random.uniform(-0.5, 0.5)
            old_price = self.mock_prices[symbol]
            new_price = old_price * (1 + change_pct / 100)
            
            # Update stored price for next call
            self.mock_prices[symbol] = new_price
            
            # Generate realistic volume
            base_volume = random.randint(100000, 500000)
            
            data = {
                'symbol': symbol,
                'source': 'mock',
                'price': round(new_price, -2),  # Round to nearest 100 VND
                'change': round(change_pct, 2),
                'volume': base_volume,
                'rsi': random.uniform(30, 70),  # Mock RSI
                'macd': random.uniform(-1, 1),  # Mock MACD
            }
            
            logger.debug(f"Mock data for {symbol}: {data['price']:,.0f} VND ({change_pct:+.2f}%)")
            return data
            
        except Exception as e:
            logger.error(f"Error generating mock data for {symbol}: {e}")
            return None
    
    def _fetch_from_cafef(self, symbol: str) -> Optional[Dict]:
        """Fetch data from CafeF"""
        try:
            url = f"https://s.cafef.vn/hose/{symbol}-ctcp.chn"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse price (this is simplified, real implementation would need actual selectors)
                data = {
                    'symbol': symbol,
                    'source': 'cafef',
                    'price': self._parse_price(soup),
                    'change': self._parse_change(soup),
                    'volume': self._parse_volume(soup),
                    'rsi': None,  # Would need chart data API
                    'macd': None,  # Would need chart data API
                }
                return data
        except Exception as e:
            logger.debug(f"CafeF fetch failed for {symbol}: {e}")
            return None
    
    def _fetch_from_vietstock(self, symbol: str) -> Optional[Dict]:
        """Fetch data from VietStock"""
        try:
            url = f"https://finance.vietstock.vn/{symbol}/overview.htm"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                data = {
                    'symbol': symbol,
                    'source': 'vietstock',
                    'price': self._parse_price(soup),
                    'change': self._parse_change(soup),
                    'volume': self._parse_volume(soup),
                    'rsi': None,
                    'macd': None,
                }
                return data
        except Exception as e:
            logger.debug(f"VietStock fetch failed for {symbol}: {e}")
            return None
    
    def _parse_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Parse current price from HTML"""
        try:
            # This is a placeholder - actual parsing depends on website structure
            # You would need to inspect the website and use appropriate selectors
            price_elem = soup.select_one('.price, .gia-hien-tai, [id*="price"]')
            if price_elem:
                price_text = price_elem.text.strip().replace(',', '').replace('VND', '')
                return float(price_text)
        except:
            pass
        return None
    
    def _parse_change(self, soup: BeautifulSoup) -> Optional[float]:
        """Parse price change percentage"""
        try:
            change_elem = soup.select_one('.change, .thay-doi, [class*="percent"]')
            if change_elem:
                change_text = change_elem.text.strip().replace('%', '').replace('+', '')
                return float(change_text)
        except:
            pass
        return None
    
    def _parse_volume(self, soup: BeautifulSoup) -> Optional[int]:
        """Parse trading volume"""
        try:
            volume_elem = soup.select_one('.volume, .khoi-luong, [id*="volume"]')
            if volume_elem:
                volume_text = volume_elem.text.strip().replace(',', '')
                return int(volume_text)
        except:
            pass
        return None
    
    def get_web_search_data(self, symbol: str) -> Dict:
        """
        Simulate web search for stock analysis
        This is a simplified version - in production, you'd use Google Custom Search API
        or scrape news sites
        """
        try:
            # Search for recent news and analysis
            query = f"{symbol} stock Vietnam analysis RSI MACD {time.strftime('%B %Y')}"
            
            # For demo purposes, return mock sentiment
            # In production, this would analyze actual search results
            return {
                'symbol': symbol,
                'news_sentiment': 'neutral',
                'analyst_consensus': 'hold',
                'recent_news_count': 0
            }
        except Exception as e:
            logger.error(f"Web search failed for {symbol}: {e}")
            return {'symbol': symbol, 'news_sentiment': 'unknown'}
