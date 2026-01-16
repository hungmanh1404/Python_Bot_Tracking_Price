"""
3-Agent Analysis Framework
Implements Hunter (Bullish), Skeptic (Bearish), and Risk Manager agents
Integrated with Market Regime Filter (Trụ 1)
"""
from typing import Dict, List, Tuple
from utils.logger import logger
from market_regime_filter import MarketRegimeFilter, MarketRegime

class Agent3Analyzer:
    """Implements the 3-agent analysis framework with Regime Filtering"""
    
    def __init__(self):
        self.market_filter = MarketRegimeFilter()
        self.min_confidence_buy = 75
    
    def analyze(self, symbol: str, data: Dict) -> Dict:
        """
        Perform complete 3-agent analysis
        """
        logger.info(f"Starting analysis for {symbol}")
        
        # 0. Trụ 1: Market Regime Filter
        regime_analysis = self.market_filter.analyze_regime(symbol, data)
        
        # If market is in shock or sideways, strictly limit trading
        if regime_analysis.regime == MarketRegime.VOLATILE_SHOCK:
            return self._create_no_trade_result(symbol, regime_analysis, "Thị trường biến động sốc - ĐỨNG NGOÀI")
            
        if regime_analysis.regime == MarketRegime.SIDEWAYS:
            # Only allow if specific breakout logic overrides, but generally wait
            # For now, we strict filter
            return self._create_no_trade_result(symbol, regime_analysis, "Thị trường Sideway - Chờ xu hướng")
        
        # Agent 1: Hunter (Bullish Case)
        bullish_points = self._agent_hunter(symbol, data, regime_analysis)
        
        # Agent 2: Skeptic (Bearish Case)
        bearish_points = self._agent_skeptic(symbol, data, regime_analysis)
        
        # Agent 3: Risk Manager (Final Decision)
        decision = self._agent_risk_manager(symbol, data, bullish_points, bearish_points, regime_analysis)
        
        result = {
            'symbol': symbol,
            'regime': regime_analysis.regime.value,
            'regime_confidence': regime_analysis.confidence,
            'bullish_case': bullish_points,
            'bearish_case': bearish_points,
            'decision': decision['action'],
            'confidence': decision['confidence'],
            'reasoning': decision['reasoning']
        }
        
        logger.info(f"{symbol} analysis complete: {decision['action']} (Confidence: {decision['confidence']}%)")
        return result
    
    def _create_no_trade_result(self, symbol: str, regime_analysis, reason: str) -> Dict:
        """Helper to create no-trade result"""
        return {
            'symbol': symbol,
            'regime': regime_analysis.regime.value,
            'regime_confidence': regime_analysis.confidence,
            'bullish_case': [],
            'bearish_case': regime_analysis.reasons,
            'decision': "🔴 ĐỨNG NGOÀI",
            'confidence': 0,
            'reasoning': reason
        }
    
    def _agent_hunter(self, symbol: str, data: Dict, regime_analysis) -> List[str]:
        """Agent 1: Find bullish signals"""
        bullish_signals = []
        
        # Add regime signals
        if regime_analysis.regime == MarketRegime.BULLISH_TRENDING:
            bullish_signals.extend([r for r in regime_analysis.reasons if "✅" in r or "📈" in r])
        
        # Check price trend
        change = data.get('change') or 0
        if change > 2:
            bullish_signals.append(f"💪 Giá tăng mạnh {change:.2f}% - Momentum tích cực")
        elif change > 0.5:
            bullish_signals.append(f"Giá tăng {change:.2f}%")
        
        # Check volume
        volume = data.get('volume') or 0
        if volume > 1000000:
             bullish_signals.append("Thanh khoản tốt")

        return bullish_signals if bullish_signals else ["Không phát hiện tín hiệu mua rõ ràng"]
    
    def _agent_skeptic(self, symbol: str, data: Dict, regime_analysis) -> List[str]:
        """Agent 2: Find bearish signals"""
        bearish_signals = []
        
        # Add regime warning signals
        if regime_analysis.regime == MarketRegime.BEARISH_TRENDING:
             bearish_signals.extend(regime_analysis.reasons)
             
        # Check price trend
        change = data.get('change') or 0
        if change < -2:
            bearish_signals.append(f"⚠️ Giá giảm mạnh {abs(change):.2f}%")
        
        return bearish_signals if bearish_signals else ["Không phát hiện rủi ro lớn"]
    
    def _agent_risk_manager(self, symbol: str, data: Dict, 
                           bullish: List[str], bearish: List[str],
                           regime_analysis) -> Dict:
        """Agent 3: Make final decision"""
        
        confidence = self._calculate_confidence(data, bullish, bearish)
        
        # Decision Logic based on Trụ 1 (Regime) & Trụ 2 (Entry - delegated to strategy check later)
        # Here we just give signal INTENT
        
        if regime_analysis.can_buy and confidence >= 40: # Lowered threshold as planned
             action = "🟢 MUA (SIGNAL)" # Requires strategy confirmation next
             reasoning = f"Market thuận lợi, {len(bullish)} tín hiệu tích cực"
        elif regime_analysis.can_sell and confidence < 30:
             action = "🔴 BÁN/CẮT"
             reasoning = "Market xấu hoặc tín hiệu yếu"
        else:
             action = "⚪ THEO DÕI"
             reasoning = "Chưa đủ điều kiện vào lệnh"

        return {
            'action': action,
            'confidence': confidence,
            'reasoning': reasoning
        }
    
    def _calculate_confidence(self, data: Dict, bullish: List[str], bearish: List[str]) -> int:
        """Calculate confidence score"""
        # Revised scoring logic
        score = 50 # Start neutral
        
        # Add points for bullish signals
        for s in bullish:
            if "💪" in s or "✅" in s: score += 10
            else: score += 5
            
        # Subtract points for bearish signals
        for s in bearish:
            if "⚠️" in s or "❌" in s: score -= 15 # Risk aversion
            else: score -= 5
            
        # Volume boost
        volume = data.get('volume', 0)
        if volume > 2000000: score += 5
        
        return max(0, min(100, score))
