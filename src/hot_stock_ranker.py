"""
Hot Stock Ranker — Combines fusion, trend, volume, and sector data
to rank symbols by overall opportunity score.

Score = Fusion×0.35 + Trend_Agreement×0.25 + Volume_Surge×0.20 + Sector_Tailwind×0.20
"""

from typing import List, Dict, Optional
from sector_map import get_sector_etfs, get_sector_name
from volume_analysis import volume_surge_score


def compute_trend_agreement(levels: dict) -> float:
    """
    Score how well multiple timeframes agree on direction.
    
    1d and 30m same direction → +1.0 (strong agreement)
    1d up, 30m down → 0.0 (conflict, neutral)
    Divergence present without centers → +0.5 (early warning)
    
    Args:
        levels: dict like {"30m": {...}, "1d": {...}} from scan JSON
    """
    if not levels:
        return 0.0
    
    level_directions = {}
    for lv, ld in levels.items():
        level_directions[lv] = ld.get("trend", "neutral")
    
    # Need at least 2 levels to check agreement
    sorted_levels = sorted(level_directions.keys())
    if len(sorted_levels) < 2:
        return 0.5  # Single level = neutral
    
    # Check primary pair (highest + second highest timeframe)
    high_tf = sorted_levels[-1]  # e.g. "1d"
    mid_tf = sorted_levels[-2]   # e.g. "30m"
    
    high_dir = level_directions[high_tf]
    mid_dir = level_directions[mid_tf]
    
    # Both up
    if high_dir == "up" and mid_dir == "up":
        return 1.0
    
    # Both down
    if high_dir == "down" and mid_dir == "down":
        return -1.0
    
    # One up, one down = conflict
    if high_dir != mid_dir and high_dir != "neutral" and mid_dir != "neutral":
        return 0.0
    
    # Divergence as partial agreement
    high_div_bullish = levels[high_tf].get("div_bullish", 0)
    high_div_bearish = levels[high_tf].get("div_bearish", 0)
    
    if high_div_bullish > 1.0 and mid_dir == "up":
        return 0.7  # Bullish divergence + short-term up
    if high_div_bullish > 1.0:
        return 0.5  # Bullish divergence alone
    
    if high_div_bearish > 1.0 and mid_dir == "down":
        return -0.7
    if high_div_bearish > 1.0:
        return -0.5
    
    return 0.3  # Weak or no signal


def compute_sector_tailwind(stock_symbol: str, sector_data: dict) -> float:
    """
    Check if the stock's sector is providing tailwind.
    
    Args:
        stock_symbol: e.g. "SMR"
        sector_data: dict of sector scan results, keyed by ETF symbol
                     Each value has "trend" and "change_pct"
    
    Returns:
        -1.0 to +1.0 score
    """
    sector_etfs = get_sector_etfs(stock_symbol)
    if not sector_etfs or not sector_data:
        return 0.0
    
    # Primary sector (first entry)
    primary = sector_etfs[0]
    sec_data = sector_data.get(primary)
    if not sec_data:
        return 0.0
    
    sector_trend = sec_data.get("trend", "neutral")
    sector_change = sec_data.get("change_pct", 0)
    
    if sector_trend == "up":
        if sector_change > 2.0:
            return 1.0   # Strong sector uptrend
        elif sector_change > 1.0:
            return 0.7
        else:
            return 0.5
    elif sector_trend == "down":
        if sector_change < -2.0:
            return -1.0  # Strong sector downtrend
        elif sector_change < -1.0:
            return -0.7
        else:
            return -0.5
    
    return 0.0


def rank_symbols(
    stock_results: List[dict],
    sector_data: dict,
    weights: Optional[dict] = None
) -> List[dict]:
    """
    Rank all scanned symbols by combined hot stock score.
    
    Args:
        stock_results: list of symbol scan results (from chanlun_bsp_scan.py JSON)
        sector_data: dict of sector scan results (from chanlun_sector_scan.py JSON)
        weights: optional override for scoring weights
    
    Returns:
        List of dicts sorted by total_score descending:
        [
            {
                "symbol": "TECK",
                "rank": 1,
                "fusion_score": 5.0,
                "trend_agreement": 1.0,
                "volume_score": 0.7,
                "sector_score": 0.5,
                "total_score": 0.72,
                "verdict": "HOT",
                "fusion_overall": "BUY",
            },
            ...
        ]
    """
    if weights is None:
        weights = {
            "fusion": 0.35,
            "trend": 0.25,
            "volume": 0.20,
            "sector": 0.20,
        }
    
    ranked = []
    
    for sr in stock_results:
        symbol = sr.get("symbol", "?")
        fusion = sr.get("fusion") or {}
        
        # Fusion score (normalize -6..+6 to -1..+1)
        raw_fusion = fusion.get("total_strength", 0)
        fusion_score = max(-1.0, min(raw_fusion / 6.0, 1.0))
        
        # Trend agreement
        levels = fusion.get("levels", {})
        trend_score = compute_trend_agreement(levels)
        
        # Volume score (from per-symbol volume data)
        vol_data = sr.get("volume", {})
        vol_ratio = vol_data.get("ratio", 1.0)
        volume_score = volume_surge_score(vol_ratio)
        
        # Sector tailwind
        sector_score = compute_sector_tailwind(symbol, sector_data)
        
        # Combined score (-1..+1)
        total = (
            fusion_score * weights["fusion"]
            + trend_score * weights["trend"]
            + volume_score * weights["volume"]
            + sector_score * weights["sector"]
        )
        
        # Clamp to -1..+1
        total = max(-1.0, min(total, 1.0))
        
        # Verdict label
        if total >= 0.6:
            verdict = "HOT"
        elif total >= 0.3:
            verdict = "WARM"
        elif total <= -0.6:
            verdict = "COLD"
        elif total <= -0.3:
            verdict = "COOL"
        else:
            verdict = "NEUTRAL"
        
        ranked.append({
            "symbol": symbol,
            "total_score": round(total, 3),
            "verdict": verdict,
            "fusion_overall": fusion.get("overall", "HOLD"),
            "fusion_strength": round(raw_fusion, 1),
            "fusion_score": round(fusion_score, 2),
            "trend_score": round(trend_score, 2),
            "volume_score": round(volume_score, 2),
            "sector_score": round(sector_score, 2),
            "vol_ratio": round(vol_data.get("ratio", 1.0), 2),
        })
    
    # Sort by total_score descending
    ranked.sort(key=lambda x: x["total_score"], reverse=True)
    
    # Assign ranks
    for i, r in enumerate(ranked):
        r["rank"] = i + 1
    
    return ranked


def get_top_picks(ranked: List[dict], n: int = 3) -> List[dict]:
    """Return top N symbols by rank (only HOT and WARM)."""
    return [r for r in ranked if r["verdict"] in ("HOT", "WARM")][:n]


def get_bottom_picks(ranked: List[dict], n: int = 3) -> List[dict]:
    """Return bottom N symbols by rank (only COLD and COOL)."""
    bottoms = [r for r in ranked if r["verdict"] in ("COLD", "COOL")]
    bottoms.reverse()
    return bottoms[:n]
