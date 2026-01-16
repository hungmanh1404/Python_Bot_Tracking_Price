"""
Market Regime Filter (Trụ 1)
Detects market conditions to only trade when favorable
Only allows trading in clear trending markets with good liquidity
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from utils.logger import logger

class MarketRegime(Enum):
    """Market regime states"""
    BULLISH_TRENDING = "bullish_trending"  # Allow buying
    BEARISH_TRENDING = "bearish_trending"  # Only sell
    SIDEWAYS = "sideways"                  # No trading
    VOLATILE_SHOCK = "volatile_shock"      # Pause all trading

@dataclass
class RegimeAnalysis:
    """Market regime analysis result"""
    regime: MarketRegime
    confidence: float  # 0-100
    reasons: List[str]
    can_buy: bool
    can_sell: bool

class MarketRegimeFilter:
    """Filters trading based on market regime"""
    
    def __init__(self):
        """Initialize market regime filter"""
        # Historical data cache for MA calculation
        self.price_history: Dict[str, List[float]] = {}
        self.volume_history: Dict[str, List[float]] = {}
        
        # Thresholds
        self.ma_periods = {'MA20': 20, 'MA50': 50}
        self.volume_threshold_multiplier = 1.0  # Volume should be >= average
        self.sideways_range_pct = 0.05  # 5% range = sideways
        self.volatility_shock_pct = 0.10  # 10% move in single update = shock
    
    def analyze_regime(self, symbol: str, data: Dict) -> RegimeAnalysis:
        """
        Analyze market regime for a symbol
        
        Args:
            symbol: Stock symbol
            data: Current market data with price, volume, etc.
            
        Returns:
            RegimeAnalysis with regime determination
        """
        price = data.get('price', 0)
        volume = data.get('volume', 0)
        change = data.get('change', 0)
        
        # Update history
        self._update_history(symbol, price, volume)
        
        reasons = []
        regime_score = 0  # Positive = bullish, Negative = bearish
        
        # 1. Check for volatility shock (highest priority)
        if abs(change) >= self.volatility_shock_pct * 100:
            return RegimeAnalysis(
                regime=MarketRegime.VOLATILE_SHOCK,
                confidence=90,
                reasons=[f"Biến động cực mạnh {change:+.2f}% - Tạm dừng giao dịch"],
                can_buy=False,
                can_sell=False
            )
        
        # 2. Calculate moving averages
        ma20 = self._calculate_ma(symbol, 20)
        ma50 = self._calculate_ma(symbol, 50)
        
        if ma20 is None or ma50 is None:
            # Not enough data for full analysis
            return RegimeAnalysis(
                regime=MarketRegime.SIDEWAYS,
                confidence=50,
                reasons=["Chưa đủ dữ liệu lịch sử để phân tích MA"],
                can_buy=False,
                can_sell=True
            )
        
        # 3. Trend Analysis: Price vs MA
        if price > ma20 and price > ma50:
            reasons.append(f"✅ Giá > MA20 ({ma20:.0f}) và MA50 ({ma50:.0f})")
            regime_score += 2
        elif price > ma20:
            reasons.append(f"Giá > MA20 ({ma20:.0f}) nhưng < MA50 ({ma50:.0f})")
            regime_score += 1
        else:
            reasons.append(f"❌ Giá < MA20 ({ma20:.0f}) - Xu hướng yếu")
            regime_score -= 2
        
        # 4. MA Slope (is MA20 trending up?)
        ma20_slope = self._calculate_ma_slope(symbol, 20)
        if ma20_slope and ma20_slope > 0.01:  # 1% upward slope
            reasons.append("📈 MA20 đang dốc lên - Xu hướng tăng")
            regime_score += 2
        elif ma20_slope and ma20_slope < -0.01:
            reasons.append("📉 MA20 đang dốc xuống - Xu hướng giảm")
            regime_score -= 2
        else:
            reasons.append("➡️ MA20 nằm ngang - Thị trường sideway")
            regime_score -= 1
        
        # 5. Golden/Death Cross
        if ma20 > ma50:
            cross_pct = ((ma20 / ma50) - 1) * 100
            if cross_pct > 2:
                reasons.append(f"🌟 Golden Cross mạnh - MA20 cao hơn MA50 {cross_pct:.1f}%")
                regime_score += 1
            else:
                reasons.append("MA20 > MA50 (bullish)")
                regime_score += 0.5
        else:
            reasons.append("⚠️ MA20 < MA50 (bearish)")
            regime_score -= 1
        
        # 6. Volume Analysis
        avg_volume = self._calculate_avg_volume(symbol, 20)
        if avg_volume and volume > 0:
            volume_ratio = volume / avg_volume
            if volume_ratio >= 1.0:
                reasons.append(f"✅ Volume tốt ({volume_ratio:.1f}x trung bình)")
                regime_score += 1
            else:
                reasons.append(f"⚠️ Volume thấp ({volume_ratio:.1f}x trung bình)")
                regime_score -= 1
        
        # 7. Detect Sideways (price trapped in narrow range)
        price_range_pct = self._calculate_price_range_pct(symbol, 20)
        if price_range_pct and price_range_pct < self.sideways_range_pct * 100:
            reasons.append(f"📊 Thị trường sideway hẹp (biên độ {price_range_pct:.1f}%)")
            regime_score -= 3  # Strong penalty for sideways
        
        # 8. Determine Final Regime
        confidence = min(abs(regime_score) * 15, 100)  # Scale to 0-100
        
        if regime_score >= 3:
            regime = MarketRegime.BULLISH_TRENDING
            can_buy = True
            can_sell = True
        elif regime_score <= -3:
            regime = MarketRegime.BEARISH_TRENDING
            can_buy = False
            can_sell = True
        else:
            regime = MarketRegime.SIDEWAYS
            can_buy = False
            can_sell = True
        
        logger.info(f"📊 {symbol} Market Regime: {regime.value} (Score: {regime_score}, Confidence: {confidence}%)")
        
        return RegimeAnalysis(
            regime=regime,
            confidence=confidence,
            reasons=reasons,
            can_buy=can_buy,
            can_sell=can_sell
        )
    
    def _update_history(self, symbol: str, price: float, volume: float):
        """Update price and volume history"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        if symbol not in self.volume_history:
            self.volume_history[symbol] = []
        
        self.price_history[symbol].append(price)
        self.volume_history[symbol].append(volume)
        
        # Keep last 60 data points (for MA50 + buffer)
        max_length = 60
        if len(self.price_history[symbol]) > max_length:
            self.price_history[symbol] = self.price_history[symbol][-max_length:]
        if len(self.volume_history[symbol]) > max_length:
            self.volume_history[symbol] = self.volume_history[symbol][-max_length:]
    
    def _calculate_ma(self, symbol: str, period: int) -> Optional[float]:
        """Calculate moving average"""
        if symbol not in self.price_history:
            return None
        
        prices = self.price_history[symbol]
        if len(prices) < period:
            return None
        
        return sum(prices[-period:]) / period
    
    def _calculate_ma_slope(self, symbol: str, period: int) -> Optional[float]:
        """Calculate MA slope (percentage change over last 5 periods)"""
        if symbol not in self.price_history:
            return None
        
        prices = self.price_history[symbol]
        if len(prices) < period + 5:
            return None
        
        ma_current = sum(prices[-period:]) / period
        ma_5_ago = sum(prices[-period-5:-5]) / period
        
        if ma_5_ago == 0:
            return None
        
        slope = ((ma_current / ma_5_ago) - 1)
        return slope
    
    def _calculate_avg_volume(self, symbol: str, period: int) -> Optional[float]:
        """Calculate average volume"""
        if symbol not in self.volume_history:
            return None
        
        volumes = self.volume_history[symbol]
        if len(volumes) < period:
            return None
        
        # Filter out zero volumes
        valid_volumes = [v for v in volumes[-period:] if v > 0]
        if not valid_volumes:
            return None
        
        return sum(valid_volumes) / len(valid_volumes)
    
    def _calculate_price_range_pct(self, symbol: str, period: int) -> Optional[float]:
        """Calculate price range as percentage of average price"""
        if symbol not in self.price_history:
            return None
        
        prices = self.price_history[symbol]
        if len(prices) < period:
            return None
        
        recent_prices = prices[-period:]
        price_high = max(recent_prices)
        price_low = min(recent_prices)
        price_avg = sum(recent_prices) / len(recent_prices)
        
        if price_avg == 0:
            return None
        
        range_pct = ((price_high - price_low) / price_avg) * 100
        return range_pct
    
    def get_regime_summary(self, symbol: str) -> str:
        """Get human-readable summary of current regime"""
        if symbol not in self.price_history:
            return "Chưa có dữ liệu"
        
        price = self.price_history[symbol][-1] if self.price_history[symbol] else 0
        ma20 = self._calculate_ma(symbol, 20)
        ma50 = self._calculate_ma(symbol, 50)
        
        summary = f"Giá: {price:,.0f}"
        if ma20:
            summary += f" | MA20: {ma20:,.0f}"
        if ma50:
            summary += f" | MA50: {ma50:,.0f}"
        
        return summary
