"""
Volume Analysis — Volume ratio and surge detection
Used to confirm trend strength (缠论 does not use volume, but volume confirms breakouts).
"""

from typing import List


def compute_volume_ratio(volumes: List[float], window: int = 20) -> float:
    """
    Calculate current volume vs trailing average.
    
    Returns volume_ratio where:
    - 1.0 = average volume
    - >1.5 = significant surge
    - >2.0 = extreme surge
    - <0.5 = extremely low volume (potential false breakout)
    """
    if not volumes or len(volumes) < 2:
        return 1.0
    
    current_vol = volumes[-1]
    lookback = min(window, len(volumes) - 1)
    avg_vol = sum(volumes[-lookback - 1:-1]) / lookback
    
    if avg_vol <= 0:
        return 1.0
    
    return current_vol / avg_vol


def volume_surge_score(vol_ratio: float) -> float:
    """
    Convert volume ratio to a 0.0-1.0 score.
    
    - 0.0x-0.7x: 0.0 (too quiet, false breakout risk)
    - 0.7x-1.0x: 0.3 (normal volume, neutral)
    - 1.0x-1.5x: 0.5-0.8 (moderate surge, confirms move)
    - 1.5x-2.0x: 0.8-1.0 (strong surge, high confidence)
    - >2.0x: 1.0 (extreme, but could be exhaustion)
    """
    if vol_ratio < 0.7:
        return 0.0
    elif vol_ratio < 1.0:
        return 0.3  # Normal volume, no surge
    elif vol_ratio < 1.5:
        return 0.5 + (vol_ratio - 1.0) * 0.6  # 0.5 → 0.8
    elif vol_ratio < 2.0:
        return 0.8 + (vol_ratio - 1.5) * 0.4  # 0.8 → 1.0
    else:
        return 1.0


def compute_volume_divergence(prices: List[float], volumes: List[float], window: int = 10) -> float:
    """
    Check for volume-price divergence.
    
    If price is rising but volume is declining → potential weakness (bearish divergence).
    If price is falling but volume is declining → potential capitulation (bullish divergence).
    
    Returns:
    - Positive = volume confirms price (healthy)
    - Negative = volume diverges from price (warning)
    """
    if len(prices) < window * 2 or len(volumes) < window * 2:
        return 0.0
    
    # Compare first half vs second half
    mid = -window
    first_half_vol = sum(volumes[-window * 2:-window]) / window
    second_half_vol = sum(volumes[-window:]) / window
    vol_change = (second_half_vol - first_half_vol) / max(first_half_vol, 1)
    
    first_half_price = sum(prices[-window * 2:-window]) / window
    second_half_price = sum(prices[-window:]) / window
    price_change = (second_half_price - first_half_price) / max(first_half_price, 0.01)
    
    # Volume should confirm price direction
    # Both up = positive, both down = positive, diverging = negative
    if price_change > 0 and vol_change > 0:
        return min(vol_change, 1.0)  # Volume confirms uptrend ✓
    elif price_change < 0 and vol_change < 0:
        return min(abs(vol_change), 1.0)  # Volume confirms downtrend ✓
    elif price_change > 0 and vol_change < 0:
        return -min(abs(vol_change), 1.0)  # Price up, vol down → warning
    else:
        return -min(abs(vol_change), 1.0)  # Price down, vol up → panic selling


def extract_volume_from_klines(klines) -> List[float]:
    """Extract volume values from a KlineSeries or list of klines."""
    return [k.volume for k in klines]


def extract_prices_from_klines(klines) -> List[float]:
    """Extract close prices from a KlineSeries or list of klines."""
    return [k.close for k in klines]
