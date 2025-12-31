"""
3-Agent Analysis Framework
Implements Hunter (Bullish), Skeptic (Bearish), and Risk Manager agents
"""
from typing import Dict, List, Tuple
from utils.logger import logger
import random

class Agent3Analyzer:
    """Implements the 3-agent analysis framework"""
    
    def __init__(self):
        self.min_confidence_buy = 75
        self.min_rr_ratio = 2.0
    
    def analyze(self, symbol: str, data: Dict) -> Dict:
        """
        Perform complete 3-agent analysis
        
        Args:
            symbol: Stock symbol
            data: Stock data dictionary
            
        Returns:
            Analysis result with recommendation
        """
        logger.info(f"Starting 3-Agent analysis for {symbol}")
        
        # Agent 1: Hunter (Bullish Case)
        bullish_points = self._agent_hunter(symbol, data)
        
        # Agent 2: Skeptic (Bearish Case)
        bearish_points = self._agent_skeptic(symbol, data)
        
        # Agent 3: Risk Manager (Final Decision)
        decision = self._agent_risk_manager(symbol, data, bullish_points, bearish_points)
        
        result = {
            'symbol': symbol,
            'bullish_case': bullish_points,
            'bearish_case': bearish_points,
            'decision': decision['action'],
            'confidence': decision['confidence'],
            'entry_zone': decision['entry_zone'],
            'stop_loss': decision['stop_loss'],
            'targets': decision['targets'],
            'risk_reward': decision['risk_reward'],
            'reasoning': decision['reasoning']
        }
        
        logger.info(f"{symbol} analysis complete: {decision['action']} (Confidence: {decision['confidence']}%)")
        return result
    
    def _agent_hunter(self, symbol: str, data: Dict) -> List[str]:
        """
        Agent 1: Find bullish signals
        """
        bullish_signals = []
        
        # Check price trend (with safe None handling)
        change = data.get('change') or 0
        if change > 0:
            bullish_signals.append(f"Giá tăng {change:.2f}% trong phiên gần nhất")
        
        # Check technical indicators (if available)
        rsi = data.get('rsi')
        if rsi and rsi < 40:
            bullish_signals.append(f"RSI {rsi:.1f} - Vùng oversold, tiềm năng phục hồi")
        
        macd = data.get('macd')
        if macd and macd > 0:
            bullish_signals.append("MACD cho tín hiệu tích cực")
        
        # Check volume
        volume = data.get('volume') or 0
        if volume > 1000000:
            bullish_signals.append("Thanh khoản tốt, có sự quan tâm từ thị trường")
        
        # Add general market context
        bullish_signals.append(f"Cổ phiếu {symbol} - Vị thế dẫn đầu trong ngành")
        
        return bullish_signals if bullish_signals else ["Không phát hiện tín hiệu mua rõ ràng"]
    
    def _agent_skeptic(self, symbol: str, data: Dict) -> List[str]:
        """
        Agent 2: Find bearish signals and risks
        """
        bearish_signals = []
        
        # Check price trend (with safe None handling)
        change = data.get('change') or 0
        if change < 0:
            bearish_signals.append(f"Giá giảm {abs(change):.2f}% - Momentum yếu")
        
        # Check RSI
        rsi = data.get('rsi')
        if rsi and rsi > 70:
            bearish_signals.append(f"RSI {rsi:.1f} - Vùng overbought, rủi ro điều chỉnh")
        
        # Check MACD
        macd = data.get('macd')
        if macd and macd < 0:
            bearish_signals.append("MACD âm - Xu hướng yếu")
        
        # General risks
        bearish_signals.append("Rủi ro biến động thị trường chung (VN-Index)")
        bearish_signals.append("Thanh khoản có thể giảm trong kỳ nghỉ lễ")
        
        return bearish_signals if bearish_signals else ["Không phát hiện rủi ro lớn"]
    
    def _agent_risk_manager(self, symbol: str, data: Dict, 
                           bullish: List[str], bearish: List[str]) -> Dict:
        """
        Agent 3: Make final decision based on risk/reward
        """
        # Calculate confidence score
        confidence = self._calculate_confidence(data, bullish, bearish)
        
        # Get current price (with safe default)
        price = data.get('price') or 30000  # Default fallback price
        change = data.get('change') or 0
        
        # Calculate support and resistance
        support = price * 0.95  # 5% below current
        resistance = price * 1.10  # 10% above current
        
        # Calculate entry zone, stop loss, and targets
        if confidence >= 75:
            # Strong buy signal
            action = "🟢 MUA NGAY"
            entry_zone = f"{price * 0.98:.0f} - {price * 1.02:.0f}"
            stop_loss = f"{price * 0.94:.0f}"
            targets = [
                f"TP1: {price * 1.07:.0f} (+7%)",
                f"TP2: {price * 1.15:.0f} (+15%)",
                f"TP3: {price * 1.25:.0f} (+25%)"
            ]
            risk_reward = 3.0
            reasoning = f"Tín hiệu mua mạnh với {len(bullish)} điểm tích cực"
            
        elif confidence >= 60:
            # Moderate buy/accumulate
            action = "🟡 TÍCH LŨY"
            entry_zone = f"{price * 0.95:.0f} - {price:.0f}"
            stop_loss = f"{price * 0.92:.0f}"
            targets = [
                f"TP1: {price * 1.05:.0f} (+5%)",
                f"TP2: {price * 1.12:.0f} (+12%)"
            ]
            risk_reward = 2.0
            reasoning = f"Confidence trung bình, nên tích lũy dần"
            
        elif confidence >= 40:
            # Wait for better entry
            action = "⚪ CHỜ MUA"
            entry_zone = f"{price * 0.90:.0f} - {price * 0.95:.0f}"
            stop_loss = f"{price * 0.88:.0f}"
            targets = [f"TP1: {price * 1.08:.0f} (+8%)"]
            risk_reward = 1.5
            reasoning = "Chờ điều chỉnh để có giá tốt hơn"
            
        else:
            # Stay out or sell
            action = "🔴 ĐỨNG NGOÀI"
            entry_zone = "N/A"
            stop_loss = "N/A"
            targets = []
            risk_reward = 0
            reasoning = f"Rủi ro cao với {len(bearish)} điểm tiêu cực"
        
        return {
            'action': action,
            'confidence': confidence,
            'entry_zone': entry_zone,
            'stop_loss': stop_loss,
            'targets': targets,
            'risk_reward': risk_reward,
            'reasoning': reasoning
        }
    
    def _calculate_confidence(self, data: Dict, bullish: List[str], bearish: List[str]) -> int:
        """
        Calculate confidence score (0-100)
        Based on number of bullish vs bearish signals and price momentum
        """
        # Base score from bullish vs bearish ratio
        bullish_count = len([b for b in bullish if "Không phát hiện" not in b])
        bearish_count = len([b for b in bearish if "Không phát hiện" not in b])
        
        if bearish_count == 0:
            bearish_count = 1  # Avoid division by zero
        
        ratio = bullish_count / bearish_count
        
        # Calculate base confidence
        if ratio > 2:
            base_score = 80
        elif ratio > 1.5:
            base_score = 70
        elif ratio > 1:
            base_score = 60
        elif ratio > 0.7:
            base_score = 50
        else:
            base_score = 40
        
        # Adjust for price momentum (with safe None handling)
        change = data.get('change') or 0
        if change > 2:
            base_score += 10
        elif change > 0:
            base_score += 5
        elif change < -2:
            base_score -= 10
        elif change < 0:
            base_score -= 5
        
        # Cap between 0-100
        return max(0, min(100, base_score))
