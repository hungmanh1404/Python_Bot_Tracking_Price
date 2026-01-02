"""
Data Scraper Module
Collects real-time stock data from BaoMoi API
"""
import requests
import random
from typing import Dict, Optional
from utils.logger import logger
import time

class StockDataScraper:
    """Scrapes stock data from BaoMoi real-time API"""
    
    # BaoMoi API configuration
    BAOMOI_API_BASE = "https://w-api.baomoi.com/api/v1/slave/widget/stock/entry/get/info"
    BAOMOI_API_KEY = "kI44ARvPwaqL7v0KuDSM0rGORtdY1nnw"
    
    # Stock exchange mapping (1 = HOSE, 2 = HNX, 3 = UPCOM)
    # Only stocks available on BaoMoi API
    EXCHANGE_MAP = {
        'FPT': '1',  # HOSE - Real-time data available
        'HPG': '1',  # HOSE - Real-time data available
        'KBC': '1',  # HOSE - Real-time data available
    }
    
    def __init__(self, data_mode='real'):
        self.data_mode = data_mode
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        
        # Fallback prices for demo mode
        self.fallback_prices = {
            'FPT': 121100,
            'KBC': 34400,
            'HPG': 28400,
        }
        
        # Track prices for simulation in demo mode
        self.mock_prices = self.fallback_prices.copy()
        for symbol in self.mock_prices:
            variation = random.uniform(-0.02, 0.02)
            self.mock_prices[symbol] = self.mock_prices[symbol] * (1 + variation)
    
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """
        Get comprehensive stock data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'FPT', 'KBC', 'HPG')
            
        Returns:
            Dictionary containing stock data or None if failed
        """
        try:
            logger.info(f"Fetching data for {symbol}...")
            
            if self.data_mode == 'demo':
                # Use simulated data in demo mode
                return self._get_mock_data(symbol)
            
            # Try to fetch real-time data from BaoMoi
            data = self._fetch_from_baomoi(symbol)
            if data:
                logger.info(f"Successfully fetched real-time data for {symbol} from BaoMoi")
                return data
            
            # Fallback to mock data if API fails
            logger.warning(f"BaoMoi API failed for {symbol}, using fallback data")
            return self._get_mock_data(symbol)
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return self._get_mock_data(symbol)
    
    def _fetch_from_baomoi(self, symbol: str) -> Optional[Dict]:
        """Fetch real-time data from BaoMoi API"""
        try:
            if symbol not in self.EXCHANGE_MAP:
                logger.warning(f"Symbol {symbol} not in exchange map")
                return None
            
            # Prepare API request
            exchange = self.EXCHANGE_MAP[symbol]
            stock_id = f"{exchange}|{symbol}"
            ctime = int(time.time())
            
            # Use known valid signature
            sig = "6061945aa5a022ca504501ec88a286f3d6bfeb6aac7a30a4596f7391f5ecdd19"
            
            params = {
                'id': stock_id,
                'dayAgo': '1',
                'ctime': str(ctime),
                'version': '0.7.57',
                'sig': sig,
                'apiKey': self.BAOMOI_API_KEY
            }
            
            response = self.session.get(
                self.BAOMOI_API_BASE,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('err') == 0 and result.get('data'):
                    stock_data = result['data']
                    
                    # Extract key information
                    price = float(stock_data.get('price', 0))
                    change_pct = float(stock_data.get('change', 0))
                    volume = int(stock_data.get('volume', 0))
                    
                    # Calculate additional metrics if available
                    price_high = float(stock_data.get('priceHigh', price))
                    price_low = float(stock_data.get('priceLow', price))
                    
                    data = {
                        'symbol': symbol,
                        'source': 'baomoi',
                        'price': price,
                        'change': change_pct,
                        'volume': volume,
                        'high': price_high,
                        'low': price_low,
                        'last_update': stock_data.get('lastUpdateTime', ''),
                        'rsi': None,  # Not provided by API
                        'macd': None,  # Not provided by API
                    }
                    
                    logger.debug(f"BaoMoi data for {symbol}: {price:,.0f} VND ({change_pct:+.2f}%)")
                    return data
                else:
                    logger.warning(f"BaoMoi API returned error for {symbol}: {result.get('msg')}")
                    return None
            else:
                logger.warning(f"BaoMoi API HTTP {response.status_code} for {symbol}")
                return None
                
        except Exception as e:
            logger.debug(f"BaoMoi fetch failed for {symbol}: {e}")
            return None
    
    def _get_mock_data(self, symbol: str) -> Optional[Dict]:
        """Generate simulated stock data for demo/fallback"""
        try:
            if symbol not in self.mock_prices:
                logger.warning(f"No fallback data available for {symbol}")
                return None
            
            # Simulate small price movement (±0.5%)
            change_pct = random.uniform(-0.5, 0.5)
            old_price = self.mock_prices[symbol]
            new_price = old_price * (1 + change_pct / 100)
            
            # Update stored price
            self.mock_prices[symbol] = new_price
            
            # Generate realistic volume
            base_volume = random.randint(100000, 500000)
            
            data = {
                'symbol': symbol,
                'source': 'simulated',
                'price': round(new_price, -2),
                'change': round(change_pct, 2),
                'volume': base_volume,
                'rsi': random.uniform(30, 70),
                'macd': random.uniform(-1, 1),
            }
            
            logger.debug(f"Simulated data for {symbol}: {data['price']:,.0f} VND ({change_pct:+.2f}%)")
            return data
            
        except Exception as e:
            logger.error(f"Error generating fallback data for {symbol}: {e}")
            return None
    
    def get_web_search_data(self, symbol: str) -> Dict:
        """
        Simulate web search for stock analysis
        Returns basic sentiment data
        """
        try:
            return {
                'symbol': symbol,
                'news_sentiment': 'neutral',
                'analyst_consensus': 'hold',
                'recent_news_count': 0
            }
        except Exception as e:
            logger.error(f"Web search failed for {symbol}: {e}")
            return {'symbol': symbol, 'news_sentiment': 'unknown'}
