"""
Entry Strategies (Trụ 2)
Implements professional entry strategies with confirmation
Breakout: Price breaks 20-period high with volume confirmation
Pullback: Price pulls back to MA in uptrend with reversal confirmation
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from utils.logger import logger

class StrategyType(Enum):
    """Entry strategy types"""
    BREAKOUT = "breakout"
    PULLBACK = "pullback"
    NONE = "none"

@dataclass
class EntrySignal:
    """Entry signal result"""
    strategy: StrategyType
    is_valid: bool
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    risk_reward: float
    reasons: List[str]
    confidence: float  # 0-100

class EntryStrategies:
    """Implements professional entry strategies"""
    
    def __init__(self):
        """Initialize entry strategies"""
        # Price history for pattern detection
        self.price_history: Dict[str, List[Dict]] = {}  # {symbol: [{price, volume, timestamp}]}
        
        # Breakout thresholds
        self.breakout_lookback = 20  # Check 20-period high
        self.breakout_volume_multiplier = 1.5  # Volume must be 1.5x average
        self.breakout_max_chase_pct = 0.05  # Don't buy if >5% above breakout
        
        # Pullback thresholds
        self.pullback_ma_tolerance_pct = 0.03  # Within 3% of MA
        self.pullback_min_uptrend_pct = 0.05  # MA must be 5% above recent low
    
    def analyze_entry(self, symbol: str, data: Dict, market_regime) -> EntrySignal:
        """
        Analyze for entry opportunities
        
        Args:
            symbol: Stock symbol
            data: Current market data
            market_regime: Current market regime from filter
            
        Returns:
            EntrySignal with strategy and details
        """
        price = data.get('price', 0)
        volume = data.get('volume', 0)
        
        # Update history
        self._update_history(symbol, data)
        
        # Check both strategies
        breakout_signal = self._check_breakout_strategy(symbol, price, volume)
        pullback_signal = self._check_pullback_strategy(symbol, price, volume, data)
        
        # Choose best signal
        if breakout_signal.is_valid and pullback_signal.is_valid:
            # Both valid, choose higher confidence
            return breakout_signal if breakout_signal.confidence >= pullback_signal.confidence else pullback_signal
        elif breakout_signal.is_valid:
            return breakout_signal
        elif pullback_signal.is_valid:
            return pullback_signal
        else:
            # No valid entry
            return EntrySignal(
                strategy=StrategyType.NONE,
                is_valid=False,
                entry_price=0,
                stop_loss=0,
                take_profit_1=0,
                take_profit_2=0,
                risk_reward=0,
                reasons=["Không có setup entry rõ ràng"],
                confidence=0
            )
    
    def _check_breakout_strategy(self, symbol: str, price: float, volume: float) -> EntrySignal:
        """
        Check for breakout entry
        
        Criteria:
        1. Price breaks 20-period high
        2. Volume > 1.5x average
        3. Not chasing (price within 5% of breakout point)
        """
        reasons = []
        
        if symbol not in self.price_history or len(self.price_history[symbol]) < self.breakout_lookback:
            return EntrySignal(
                strategy=StrategyType.BREAKOUT,
                is_valid=False,
                entry_price=0, stop_loss=0, take_profit_1=0, take_profit_2=0,
                risk_reward=0,
                reasons=["Chưa đủ dữ liệu cho breakout analysis"],
                confidence=0
            )
        
        # Get recent price history
        recent_data = self.price_history[symbol][-self.breakout_lookback:]
        recent_prices = [d['price'] for d in recent_data]
        recent_volumes = [d['volume'] for d in recent_data if d['volume'] > 0]
        
        # 1. Check if price breaks 20-period high
        period_high = max(recent_prices[:-1])  # Exclude current candle
        is_breakout = price > period_high
        
        if not is_breakout:
            return EntrySignal(
                strategy=StrategyType.BREAKOUT,
                is_valid=False,
                entry_price=0, stop_loss=0, take_profit_1=0, take_profit_2=0,
                risk_reward=0,
                reasons=[f"Chưa phá đỉnh {self.breakout_lookback} phiên ({period_high:,.0f})"],
                confidence=0
            )
        
        breakout_pct = ((price / period_high) - 1) * 100
        reasons.append(f"🚀 Phá đỉnh {self.breakout_lookback} phiên: {period_high:,.0f} → {price:,.0f} (+{breakout_pct:.2f}%)")
        
        # 2. Check if chasing too much
        if breakout_pct > self.breakout_max_chase_pct * 100:
            return EntrySignal(
                strategy=StrategyType.BREAKOUT,
                is_valid=False,
                entry_price=0, stop_loss=0, take_profit_1=0, take_profit_2=0,
                risk_reward=0,
                reasons=[f"❌ Đuổi giá quá cao (+{breakout_pct:.2f}% > {self.breakout_max_chase_pct * 100}%)"],
                confidence=0
            )
        
        reasons.append(f"✅ Trong vùng entry ({breakout_pct:.2f}% từ breakout)")
        
        # 3. Check volume confirmation
        avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
        volume_ratio = volume / avg_volume if avg_volume > 0 else 0
        
        if volume_ratio < self.breakout_volume_multiplier:
            reasons.append(f"⚠️ Volume yếu ({volume_ratio:.1f}x < {self.breakout_volume_multiplier}x)")
            confidence = 40
        else:
            reasons.append(f"✅ Volume mạnh ({volume_ratio:.1f}x trung bình)")
            confidence = 75
        
        # Calculate SL/TP
        # SL: below breakout candle or recent swing low
        recent_lows = [d['low'] if 'low' in d else d['price'] for d in recent_data[-5:]]
        swing_low = min(recent_lows)
        stop_loss = min(swing_low, period_high * 0.97)  # At least 3% below breakout
        
        # TP: RR 1:2 minimum
        risk = price - stop_loss
        take_profit_1 = price + (risk * 1.5)
        take_profit_2 = price + (risk * 2.0)
        risk_reward = (take_profit_2 - price) / risk if risk > 0 else 0
        
        is_valid = confidence >= 40 and risk_reward >= 1.5
        
        return EntrySignal(
            strategy=StrategyType.BREAKOUT,
            is_valid=is_valid,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            risk_reward=risk_reward,
            reasons=reasons,
            confidence=confidence
        )
    
    def _check_pullback_strategy(self, symbol: str, price: float, volume: float, data: Dict) -> EntrySignal:
        """
        Check for pullback entry
        
        Criteria:
        1. Price pulls back to MA20/MA50 in uptrend
        2. Support level holds (no break of structure)
        3. Reversal confirmation (bullish candle)
        """
        reasons = []
        
        if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
            return EntrySignal(
                strategy=StrategyType.PULLBACK,
                is_valid=False,
                entry_price=0, stop_loss=0, take_profit_1=0, take_profit_2=0,
                risk_reward=0,
                reasons=["Chưa đủ dữ liệu cho pullback analysis"],
                confidence=0
            )
        
        # Calculate MA20
        recent_data = self.price_history[symbol][-20:]
        recent_prices = [d['price'] for d in recent_data]
        ma20 = sum(recent_prices) / len(recent_prices)
        
        # 1. Check if in uptrend (MA20 > recent low by at least 5%)
        recent_low = min(recent_prices[-10:])
        uptrend_pct = ((ma20 / recent_low) - 1) * 100
        
        if uptrend_pct < self.pullback_min_uptrend_pct * 100:
            return EntrySignal(
                strategy=StrategyType.PULLBACK,
                is_valid=False,
                entry_price=0, stop_loss=0, take_profit_1=0, take_profit_2=0,
                risk_reward=0,
                reasons=[f"Không trong uptrend (MA20 chỉ cao hơn low {uptrend_pct:.1f}%)"],
                confidence=0
            )
        
        reasons.append(f"📈 Trong uptrend (MA20: {ma20:,.0f}, cao hơn low {uptrend_pct:.1f}%)")
        
        # 2. Check if price near MA20 (within 3%)
        distance_from_ma = abs(price - ma20) / ma20 if ma20 > 0 else 1
        
        if distance_from_ma > self.pullback_ma_tolerance_pct:
            return EntrySignal(
                strategy=StrategyType.PULLBACK,
                is_valid=False,
                entry_price=0, stop_loss=0, take_profit_1=0, take_profit_2=0,
                risk_reward=0,
                reasons=[f"Giá xa MA20 ({distance_from_ma * 100:.1f}% > {self.pullback_ma_tolerance_pct * 100}%)"],
                confidence=0
            )
        
        reasons.append(f"✅ Giá gần MA20 ({price:,.0f} vs {ma20:,.0f}, {distance_from_ma * 100:.1f}%)")
        
        # 3. Check for reversal confirmation (current candle is bullish)
        # We need open/close data for this, use change instead
        change = data.get('change', 0)
        
        if change < 0:
            reasons.append("⚠️ Chưa có nến xác nhận (giá vẫn giảm)")
            confidence = 35
        else:
            reasons.append(f"✅ Nến xác nhận ({change:+.2f}%)")
            confidence = 65
        
        # 4. Check support not broken
        support_level = recent_low
        if price < support_level:
            return EntrySignal(
                strategy=StrategyType.PULLBACK,
                is_valid=False,
                entry_price=0, stop_loss=0, take_profit_1=0, take_profit_2=0,
                risk_reward=0,
                reasons=["❌ Phá support - cấu trúc bị gãy"],
                confidence=0
            )
        
        reasons.append(f"✅ Support giữ vững ({support_level:,.0f})")
        
        # Calculate SL/TP
        stop_loss = support_level * 0.98  # Below support with buffer
        risk = price - stop_loss
        take_profit_1 = price + (risk * 1.5)
        take_profit_2 = price + (risk * 2.0)
        risk_reward = (take_profit_2 - price) / risk if risk > 0 else 0
        
        is_valid = confidence >= 35 and risk_reward >= 1.5
        
        return EntrySignal(
            strategy=StrategyType.PULLBACK,
            is_valid=is_valid,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            risk_reward=risk_reward,
            reasons=reasons,
            confidence=confidence
        )
    
    def _update_history(self, symbol: str, data: Dict):
        """Update price history for pattern detection"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        price_data = {
            'price': data.get('price', 0),
            'volume': data.get('volume', 0),
            'high': data.get('high', data.get('price', 0)),
            'low': data.get('low', data.get('price', 0)),
            'change': data.get('change', 0)
        }
        
        self.price_history[symbol].append(price_data)
        
        # Keep last 60 data points
        if len(self.price_history[symbol]) > 60:
            self.price_history[symbol] = self.price_history[symbol][-60:]
