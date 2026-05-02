"""
Divergence Detection Module (背驰检测)
缠论第 15, 24, 25, 27 课

Three methods:
1. Point method: MACD histogram comparison at two fractal points (original)
2. Area method: MACD柱 area comparison between two same-direction segments
3. DIF method: DIF 黄白线 comparison (价格新低/新高 vs DIF 不新低/新高)

Additional checks:
- 黄白线回拉0轴 check (DIF/DEA crossing zero during center formation)
- 区间套 (interval nesting) for multi-level reversal pinpointing
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import math
from .kline import KlineSeries
from .fractal import Fractal
from .segment import Segment
from .center import Center
from .indicators import MACDResult


@dataclass
class DivergenceResult:
    """背驰检测结果"""
    has_divergence: bool
    score: float  # 0.0 to 5.0, higher = stronger divergence
    method: str  # 'point', 'area', 'dif', 'combined'
    details: dict  # Method-specific details


@dataclass
class ZeroPullbackResult:
    """黄白线回拉0轴检测结果"""
    has_pullback: bool
    pullback_level: float  # How close DIF got to 0 (0.0 = right at 0, higher = further)
    dif_min: float  # Minimum DIF value during pullback
    dif_max: float  # Maximum DIF value during pullback


class DivergenceDetector:
    """
    背驰检测器 - 多方法融合
    Divergence Detector - Multi-method fusion
    
    缠论核心（第 15 课）：
    没有趋势，没有背驰 — No trend, no divergence
    
    检测方法（第 24/25 课）：
    1. 面积法（Area Method）: 比较两段同向走势的 MACD 柱面积
    2. 力度法（Force Method）: 面积 / 时间
    3. 黄白线法（DIF Method）: 比较 DIF 线的高低
    
    标准 2 中枢趋势 MACD 形态（第 24 课）：
    1. 第一中枢：DIF 黄白线从 0 轴下方升起
    2. 突破段：最强的一段
    3. 第二中枢：DIF 黄白线回拉至 0 轴附近
    4. 最后突破：检查 DIF 是否不能新高/新低，或柱面积缩小
    """

    def __init__(self, area_weight: float = 0.5, dif_weight: float = 0.3, point_weight: float = 0.2):
        """
        Args:
            area_weight: Area method weight in combined score
            dif_weight: DIF method weight in combined score
            point_weight: Point method weight in combined score
        """
        self.area_weight = area_weight
        self.dif_weight = dif_weight
        self.point_weight = point_weight

    def detect_bullish_divergence(
        self,
        series: KlineSeries,
        macd_data: List[MACDResult],
        segments: List[Segment],
        bottom_fractals: List[Fractal],
        centers: List[Center]
    ) -> DivergenceResult:
        """
        检测底背驰 (Bullish Divergence)
        
        条件：
        1. 价格新低 (at bottom fractal)
        2. MACD 柱面积不新低 (Area method)
        3. DIF 黄白线不新低 (DIF method)
        4. 黄白线曾回拉 0 轴（中枢形成时）
        
        Returns:
            DivergenceResult with combined score
        """
        if len(bottom_fractals) < 2 or not macd_data:
            return DivergenceResult(
                has_divergence=False, score=0.0, method='combined',
                details={'reason': 'insufficient data'}
            )

        last_low = bottom_fractals[-1]
        prev_low = bottom_fractals[-2]

        # 条件 1: 价格新低
        if last_low.price >= prev_low.price:
            return DivergenceResult(
                has_divergence=False, score=0.0, method='combined',
                details={'reason': 'price not making new low'}
            )

        last_idx = last_low.kline_index
        prev_idx = prev_low.kline_index

        if last_idx >= len(macd_data) or prev_idx >= len(macd_data):
            return DivergenceResult(
                has_divergence=False, score=0.0, method='combined',
                details={'reason': 'index out of range'}
            )

        # === Method 1: Point method (MACD histogram comparison) ===
        point_score = self._point_method_bullish(macd_data, last_idx, prev_idx)

        # === Method 2: Area method (MACD柱面积比较) ===
        area_score = self._area_method_bullish(macd_data, series, segments, last_idx, prev_idx, last_low, prev_low)

        # === Method 3: DIF method (黄白线比较) ===
        dif_score = self._dif_method_bullish(macd_data, last_idx, prev_idx)

        # === Combined score ===
        combined_score = (
            self.area_weight * area_score +
            self.dif_weight * dif_score +
            self.point_weight * point_score
        )

        has_divergence = combined_score > 0.3

        return DivergenceResult(
            has_divergence=has_divergence,
            score=min(combined_score, 5.0),
            method='combined',
            details={
                'point_score': point_score,
                'area_score': area_score,
                'dif_score': dif_score,
                'combined_score': combined_score,
                'last_price': last_low.price,
                'prev_price': prev_low.price
            }
        )

    def detect_bearish_divergence(
        self,
        series: KlineSeries,
        macd_data: List[MACDResult],
        segments: List[Segment],
        top_fractals: List[Fractal],
        centers: List[Center]
    ) -> DivergenceResult:
        """
        检测顶背驰 (Bearish Divergence)
        
        Symmetric to bullish divergence.
        """
        if len(top_fractals) < 2 or not macd_data:
            return DivergenceResult(
                has_divergence=False, score=0.0, method='combined',
                details={'reason': 'insufficient data'}
            )

        last_high = top_fractals[-1]
        prev_high = top_fractals[-2]

        # 条件 1: 价格新高
        if last_high.price <= prev_high.price:
            return DivergenceResult(
                has_divergence=False, score=0.0, method='combined',
                details={'reason': 'price not making new high'}
            )

        last_idx = last_high.kline_index
        prev_idx = prev_high.kline_index

        if last_idx >= len(macd_data) or prev_idx >= len(macd_data):
            return DivergenceResult(
                has_divergence=False, score=0.0, method='combined',
                details={'reason': 'index out of range'}
            )

        # === Method 1: Point method ===
        point_score = self._point_method_bearish(macd_data, last_idx, prev_idx)

        # === Method 2: Area method ===
        area_score = self._area_method_bearish(macd_data, series, segments, last_idx, prev_idx, last_high, prev_high)

        # === Method 3: DIF method ===
        dif_score = self._dif_method_bearish(macd_data, last_idx, prev_idx)

        # === Combined score ===
        combined_score = (
            self.area_weight * area_score +
            self.dif_weight * dif_score +
            self.point_weight * point_score
        )

        has_divergence = combined_score > 0.3

        return DivergenceResult(
            has_divergence=has_divergence,
            score=min(combined_score, 5.0),
            method='combined',
            details={
                'point_score': point_score,
                'area_score': area_score,
                'dif_score': dif_score,
                'combined_score': combined_score,
                'last_price': last_high.price,
                'prev_price': prev_high.price
            }
        )

    # ========== Point Method (MACD histogram at fractals) ==========

    def _point_method_bullish(self, macd_data: List[MACDResult], last_idx: int, prev_idx: int) -> float:
        """
        Point method for bullish divergence.
        Compare MACD histogram at the last two bottom fractals.
        
        Bullish: Price new low, but MACD histogram higher than previous.
        """
        last_hist = macd_data[last_idx].histogram
        prev_hist = macd_data[prev_idx].histogram

        if last_hist <= prev_hist:
            return 0.0

        # Score proportional to relative difference
        score = (last_hist - prev_hist) / max(abs(prev_hist), 0.001)
        return min(score, 5.0)

    def _point_method_bearish(self, macd_data: List[MACDResult], last_idx: int, prev_idx: int) -> float:
        """
        Point method for bearish divergence.
        Compare MACD histogram at the last two top fractals.
        
        Bearish: Price new high, but MACD histogram lower than previous.
        """
        last_hist = macd_data[last_idx].histogram
        prev_hist = macd_data[prev_idx].histogram

        if last_hist >= prev_hist:
            return 0.0

        score = (prev_hist - last_hist) / max(abs(prev_hist), 0.001)
        return min(score, 5.0)

    # ========== Area Method (MACD柱面积比较) ==========

    def _area_method_bullish(
        self,
        macd_data: List[MACDResult],
        series: KlineSeries,
        segments: List[Segment],
        last_idx: int,
        prev_idx: int,
        last_fractal: Fractal,
        prev_fractal: Fractal
    ) -> float:
        """
        Area method for bullish divergence.
        
        Compare MACD histogram AREA between the two most recent
        same-direction (down) segments.
        
        Key intuition (第 25 课):
        Second downward push has LESS momentum (smaller absolute area)
        even though price went LOWER.
        """
        # Find the two most recent down segments
        down_segments = [s for s in segments if s.direction == 'down']
        if len(down_segments) < 2:
            # Fall back to fractal-based area estimation
            return self._area_between_points(macd_data, last_idx, prev_idx, bullish=True)

        # Use the last two down segments
        seg2 = down_segments[-1]  # Most recent down segment
        seg1 = down_segments[-2]  # Previous down segment

        # Calculate area under MACD histogram for each segment
        area1 = self._calc_macd_area(macd_data, seg1.start_idx, seg1.end_idx)
        area2 = self._calc_macd_area(macd_data, seg2.start_idx, seg2.end_idx)

        # Bullish divergence: abs(area2) < abs(area1) (less downward momentum in 2nd push)
        area1_abs = abs(area1)
        area2_abs = abs(area2)
        if area2_abs >= area1_abs:
            return 0.0

        # Score: how much smaller is area2_abs relative to area1_abs
        if area1_abs < 0.001:
            return 0.0

        reduction = (area1_abs - area2_abs) / area1_abs
        return min(reduction * 3.0, 5.0)

    def _area_method_bearish(
        self,
        macd_data: List[MACDResult],
        series: KlineSeries,
        segments: List[Segment],
        last_idx: int,
        prev_idx: int,
        last_fractal: Fractal,
        prev_fractal: Fractal
    ) -> float:
        """
        Area method for bearish divergence.
        
        Compare MACD histogram AREA between the two most recent
        same-direction (up) segments.
        
        Bearish divergence: Second upward push has LESS area
        even though price went HIGHER.
        """
        up_segments = [s for s in segments if s.direction == 'up']
        if len(up_segments) < 2:
            return self._area_between_points(macd_data, last_idx, prev_idx, bullish=False)

        seg2 = up_segments[-1]
        seg1 = up_segments[-2]

        area1 = self._calc_macd_area(macd_data, seg1.start_idx, seg1.end_idx)
        area2 = self._calc_macd_area(macd_data, seg2.start_idx, seg2.end_idx)

        # Bearish divergence: abs(area2) < abs(area1) (less upward momentum in 2nd push)
        area1_abs = abs(area1)
        area2_abs = abs(area2)
        if area2_abs >= area1_abs:
            return 0.0

        if abs(area1) < 0.001:
            return 0.0

        reduction = (area1 - area2) / abs(area1)
        return min(reduction * 3.0, 5.0)

    def _area_between_points(self, macd_data: List[MACDResult], idx1: int, idx2: int, bullish: bool) -> float:
        """
        Fallback: estimate area between two index points.
        Used when segments are unavailable.
        """
        start, end = min(idx1, idx2), max(idx1, idx2)
        if end - start < 2:
            return 0.0

        # Split into two halves
        mid = (start + end) // 2
        area_first = sum(
            macd_data[i].histogram for i in range(start, mid)
            if i < len(macd_data)
        )
        area_second = sum(
            macd_data[i].histogram for i in range(mid, end)
            if i < len(macd_data)
        )

        # For bullish: second half should be less negative
        # For bearish: second half should be less positive
        if bullish:
            if area_second <= area_first:
                return 0.0
        else:
            if area_second >= area_first:
                return 0.0

        score = abs(area_second - area_first) / max(abs(area_first), 0.001)
        return min(score, 3.0)

    def _calc_macd_area(self, macd_data: List[MACDResult], start_idx: int, end_idx: int) -> float:
        """
        Calculate total MACD histogram area over a segment.
        
        Uses absolute values for the area - we care about MAGNITUDE
        of momentum in either direction.
        """
        total = 0.0
        for i in range(max(0, start_idx), min(end_idx + 1, len(macd_data))):
            total += macd_data[i].histogram
        return total

    # ========== DIF Method (黄白线比较) ==========

    def _dif_method_bullish(self, macd_data: List[MACDResult], last_idx: int, prev_idx: int) -> float:
        """
        DIF 黄白线 method for bullish divergence.
        
        Bullish: Price makes new low, but DIF does NOT make new low.
        
        Standard pattern (第 24 课):
        - First low: DIF deeply negative
        - Pullback: DIF rises toward 0 (第一中枢形成)
        - Second low: DIF not as negative as first low
        """
        last_dif = macd_data[last_idx].dif
        prev_dif = macd_data[prev_idx].dif

        # Bullish: last DIF > prev DIF (less negative)
        if last_dif <= prev_dif:
            return 0.0

        score = (last_dif - prev_dif) / max(abs(prev_dif), 0.001)
        return min(score, 5.0)

    def _dif_method_bearish(self, macd_data: List[MACDResult], last_idx: int, prev_idx: int) -> float:
        """
        DIF 黄白线 method for bearish divergence.
        
        Bearish: Price makes new high, but DIF does NOT make new high.
        """
        last_dif = macd_data[last_idx].dif
        prev_dif = macd_data[prev_idx].dif

        # Bearish: last DIF < prev DIF (less positive)
        if last_dif >= prev_dif:
            return 0.0

        score = (prev_dif - last_dif) / max(abs(prev_dif), 0.001)
        return min(score, 5.0)

    # ========== 黄白线回拉0轴 Check ==========

    def check_zero_pullback(
        self,
        macd_data: List[MACDResult],
        centers: List[Center]
    ) -> ZeroPullbackResult:
        """
        检查 DIF 黄白线是否回拉 0 轴
        
        Standard 2-center MACD pattern (第 24 课):
        1. First center: DIF rises from below 0
        2. Breakout: strongest segment
        3. Second center: DIF pulls back near 0
        4. Final breakout: check divergence
        
        Returns:
            ZeroPullbackResult indicating if pullback occurred
        """
        if len(centers) < 1 or not macd_data:
            return ZeroPullbackResult(
                has_pullback=False, pullback_level=float('inf'),
                dif_min=0, dif_max=0
            )

        # Check DIF values around the most recent center
        last_center = centers[-1]
        start = max(0, last_center.start_idx)
        end = min(len(macd_data), last_center.end_idx + 5)  # A bit of buffer

        if start >= end:
            return ZeroPullbackResult(
                has_pullback=False, pullback_level=float('inf'),
                dif_min=0, dif_max=0
            )

        dif_values = [macd_data[i].dif for i in range(start, end)]
        if not dif_values:
            return ZeroPullbackResult(
                has_pullback=False, pullback_level=float('inf'),
                dif_min=0, dif_max=0
            )

        dif_min = min(dif_values)
        dif_max = max(dif_values)

        # How close did DIF get to 0?
        # Find the minimum absolute DIF value (closest to 0)
        min_abs_dif = min(abs(d) for d in dif_values)

        # Get price range for normalization
        price_range = abs(macd_data[-1].dif - macd_data[0].dif) if len(macd_data) > 1 else 1.0
        if price_range < 0.001:
            price_range = 1.0

        # Normalized pullback level (0.0 = right at 0, lower = better)
        pullback_level = min_abs_dif / max(price_range, 0.001)

        # Pullback is significant if DIF crossed or touched near 0
        has_pullback = min_abs_dif < price_range * 0.3

        return ZeroPullbackResult(
            has_pullback=has_pullback,
            pullback_level=pullback_level,
            dif_min=dif_min,
            dif_max=dif_max
        )

    def check_segment_fractal_divergence(
        self,
        series: KlineSeries,
        macd_data: List[MACDResult],
        segments: List[Segment]
    ) -> Optional[DivergenceResult]:
        """
        线段级别背驰检测（第 27 课 - 区间套）
        
        Looks at the last two same-direction segments and checks
        if the MACD area of the second is smaller.
        
        This is a broader check than point-based divergence -
        it captures the overall momentum shift between segments.
        """
        if len(macd_data) < 5 or len(segments) < 2:
            return None

        # Only consider segments with clear price movement
        up_segs = [s for s in segments if s.direction == 'up']
        down_segs = [s for s in segments if s.direction == 'down']

        scores = []

        # Check up segments (bearish divergence possible)
        if len(up_segs) >= 2:
            s1, s2 = up_segs[-2], up_segs[-1]
            # Check if price went higher but area smaller
            if s2.end_price > s1.end_price:
                area1 = self._calc_macd_area(macd_data, s1.start_idx, s1.end_idx)
                area2 = self._calc_macd_area(macd_data, s2.start_idx, s2.end_idx)
                if area2 < area1 and abs(area1) > 0.001:
                    score = (area1 - area2) / abs(area1)
                    scores.append(-score)  # Negative = bearish

        # Check down segments (bullish divergence possible)
        if len(down_segs) >= 2:
            s1, s2 = down_segs[-2], down_segs[-1]
            if s2.end_price < s1.end_price:
                area1 = self._calc_macd_area(macd_data, s1.start_idx, s1.end_idx)
                area2 = self._calc_macd_area(macd_data, s2.start_idx, s2.end_idx)
                if area2 > area1 and abs(area1) > 0.001:
                    score = abs(area2 - area1) / abs(area1)
                    scores.append(score)  # Positive = bullish

        if not scores:
            return None

        avg_score = sum(abs(s) for s in scores) / len(scores)
        direction = 'bullish' if sum(scores) > 0 else 'bearish'

        return DivergenceResult(
            has_divergence=avg_score > 0.2,
            score=min(avg_score * 2.0, 5.0),
            method='segment_area',
            details={
                'direction': direction,
                'segment_scores': scores,
                'avg_score': avg_score
            }
        )


# ===== Convenience function =====

def detect_divergence(
    series: KlineSeries,
    macd_data: List[MACDResult],
    segments: List[Segment],
    fractals: List[Fractal],
    centers: List[Center]
) -> dict:
    """
    Convenience function: run all divergence checks and return summary.
    
    Returns:
        {
            'bullish': DivergenceResult or None,
            'bearish': DivergenceResult or None,
            'segment_divergence': DivergenceResult or None,
            'zero_pullback': ZeroPullbackResult or None
        }
    """
    detector = DivergenceDetector()

    top_fractals = [f for f in fractals if f.is_top]
    bottom_fractals = [f for f in fractals if not f.is_top]

    bullish = detector.detect_bullish_divergence(
        series, macd_data, segments, bottom_fractals, centers
    ) if len(bottom_fractals) >= 2 else None

    bearish = detector.detect_bearish_divergence(
        series, macd_data, segments, top_fractals, centers
    ) if len(top_fractals) >= 2 else None

    segment_div = detector.check_segment_fractal_divergence(
        series, macd_data, segments
    )

    zero_pb = detector.check_zero_pullback(macd_data, centers)

    return {
        'bullish': bullish,
        'bearish': bearish,
        'segment_divergence': segment_div,
        'zero_pullback': zero_pb
    }
