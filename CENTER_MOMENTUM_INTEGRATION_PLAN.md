# 中枢动量模块整合方案 - 缠论 v6.0

**版本**: v6.0-beta  
**创建日期**: 2026-04-17  
**状态**: 🟡 待审批

---

## 📋 目录

1. [缠论理论基础](#缠论理论基础)
2. [当前系统架构分析](#当前系统架构分析)
3. [中枢动量模块定位](#中枢动量模块定位)
4. [整合方案设计](#整合方案设计)
5. [可信度提升策略](#可信度提升策略)
6. [技术实现方案](#技术实现方案)
7. [开发计划与验收](#开发计划与验收)

---

## 缠论理论基础

### 中枢与买卖点的关系

根据缠论原文 (第 17-21 课、第 63-67 课):

```
第一类买卖点 (buy1/sell1):
  - 趋势背驰点
  - 通常出现在第三个中枢之后
  - 是趋势反转的临界点

第二类买卖点 (buy2/sell2):
  - 第一类买卖点后的回调/反弹
  - 不破前低/前高
  - 是趋势确认的入场点

第三类买卖点 (buy3/sell3):
  - 中枢突破后的回抽确认
  - 是趋势加速的信号
```

### 中枢序号的战略意义

| 中枢序号 | 趋势阶段 | 买卖点概率 | 操作策略 |
|---------|---------|-----------|---------|
| 第 1 中枢 | 趋势初现 | buy2/sell2 | 轻仓试单 |
| 第 2 中枢 | 趋势确认 | buy2/sell2 | 加仓 |
| 第 3 中枢 | 趋势背驰区 | buy1/sell1 | 警惕反转 |
| 第 3 中枢后 | 背驰高风崄 | buy1/sell1 | 准备离场 |

### 动量变化的理论依据

缠论第 67 课 - 趋势背驰:

```
趋势背驰的判断:
1. 价格创新高/新低
2. MACD/力度不创新高/新低
3. 中枢区间缩小 (动量增强信号)
4. 离开段力度 < 进入段力度 (背驰确认)

中枢动量分析的核心:
- 中枢区间变化 → 趋势强弱
- 中枢位置移动 → 趋势方向
- 进入/离开段对比 → 背驰判断
```

---

## 当前系统架构分析

### v5.3 核心模块

```
┌─────────────────────────────────────────────────────────┐
│                    v5.3 核心架构                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  数据层 → 缠论结构 → 买卖点检测 → 信号推送              │
│    ↓          ↓           ↓           ↓                 │
│  K 线数据   分型/笔/线段  buy1/2/3   Telegram            │
│                                                         │
│  核心文件:                                               │
│  - python-layer/trading_system/                         │
│      - fractal.py (分型检测)                            │
│      - pen.py (笔计算)                                  │
│      - segment.py (线段计算)                            │
│      - center.py (中枢检测)                             │
│      - monitor.py (监控引擎)                            │
│                                                         │
│  - scripts/                                              │
│      - buy_sell_points.py (买卖点检测)                  │
│      - monitor_all.py (主监控)                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### v6.0 新增模块

```
┌─────────────────────────────────────────────────────────┐
│                    v6.0 新增架构                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Phase 1: 趋势起势检测 (trend_start_detector.py)        │
│  Phase 2: 趋势衰减监测 (trend_decay_monitor.py)         │
│  Phase 3: 趋势反转预警 (trend_reversal_warning.py)      │
│  Phase 4: 综合置信度引擎 (comprehensive_confidence_...) │
│                                                         │
│  新增维度:                                               │
│  - 成交量确认 (volume_confirmation.py)                  │
│  - MACD 高级分析 (macd_advanced_analysis.py)            │
│  - 综合可信度计算 (confidence_calculator.py)            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 当前可信度计算逻辑

```python
# confidence_calculator.py 权重配置
WEIGHTS = {
    'chanlun_base': 0.35,       # 缠论价格结构 (基础)
    'volume': 0.15,             # 成交量确认
    'macd': 0.20,               # MACD 多维度
    'multi_level': 0.15,        # 多级别确认
    'external': 0.15,           # 外部因子
}

# 计算逻辑
final_confidence = (
    chanlun_base * 0.35 +
    volume_score * 0.15 +
    macd_score * 0.20 +
    multi_level * 0.15 +
    external * 0.15
)
```

**问题**: 当前 `chanlun_base` 仅考虑买卖点类型，未考虑:
- 中枢序号 (第几个中枢)
- 中枢动量状态 (增强/衰减)
- 趋势延续性评估

---

## 中枢动量模块定位

### 模块定位

中枢动量模块不是独立模块，而是**缠论基础维度的增强**:

```
原 chanlun_base (35% 权重):
  - 买卖点类型 (buy1/buy2/sell1/sell2)
  - 级别 (5m/30m/1d/1w)
  - 基础置信度 (根据买卖点类型设定)

增强后 chanlun_base (35% 权重):
  - 买卖点类型 (原有)
  - 中枢序号 (新增 +10-15% 调整)
  - 动量状态 (新增 +5-10% 调整)
  - 趋势延续性 (新增 +5-10% 调整)
```

### 与其他模块的关系

```
┌─────────────────────────────────────────────────────────┐
│              缠论 v6.0 可信度架构                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                    综合置信度 100%                      │
│                         ↓                               │
│    ┌──────────┬──────────┬──────────┬──────────┐       │
│    │          │          │          │          │       │
│  缠论基础   成交量    MACD     多级别    外部因子   │
│  (35%)     (15%)     (20%)     (15%)     (15%)   │
│    ↓                                          │       │
│  ┌───────┐                                    │       │
│  │中枢动量│ ← 本模块定位                        │       │
│  │增强层 │                                    │       │
│  └───────┘                                    │       │
│    ↓                                          │       │
│  - 买卖点类型 (原有)                           │       │
│  - 中枢序号 (新增)                             │       │
│  - 动量状态 (新增)                             │       │
│  - 延续概率 (新增)                             │       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 整合方案设计

### 方案 A: 中枢动量作为 chanlun_base 子模块 (推荐)

**核心思路**: 中枢动量分析作为缠论基础维度的增强层

```python
# 伪代码示例
class EnhancedChanLunConfidence:
    """增强的缠论基础置信度计算"""
    
    def __init__(self):
        self.center_momentum_analyzer = CenterMomentumAnalyzer()
        
    def calculate(self, signal, centers, segments, price):
        # 1. 基础置信度 (根据买卖点类型)
        base = self._get_base_confidence(signal.type)  # 0.5-0.7
        
        # 2. 中枢序号调整
        center_bonus = self._get_center_position_bonus(centers, price)  # -0.15 to +0.15
        
        # 3. 动量状态调整
        momentum_bonus = self._get_momentum_bonus(centers, segments)  # -0.10 to +0.10
        
        # 4. 趋势延续性调整
        continuation_bonus = self._get_continuation_bonus(centers)  # -0.10 to +0.10
        
        # 综合计算
        enhanced_confidence = base + center_bonus + momentum_bonus + continuation_bonus
        return max(0.0, min(1.0, enhanced_confidence))
```

**权重调整**:

| 维度 | 原权重 | 新权重 | 变化说明 |
|------|-------|-------|---------|
| chanlun_base | 35% | 35% | 内部增强，权重不变 |
| volume | 15% | 15% | 不变 |
| macd | 20% | 20% | 不变 |
| multi_level | 15% | 15% | 不变 |
| external | 15% | 15% | 不变 |

**chanlun_base 内部权重**:

| 因子 | 权重 | 说明 |
|------|------|------|
| 买卖点类型 | 50% | buy2/sell2 > buy1/sell1 |
| 中枢序号 | 20% | 第 1/2 中枢 > 第 3 中枢 |
| 动量状态 | 15% | 增强 > 稳定 > 衰减 |
| 延续概率 | 15% | 高延续 > 低延续 |

---

### 方案 B: 中枢动量作为独立维度

**核心思路**: 中枢动量作为第 6 个独立维度

```python
WEIGHTS = {
    'chanlun_base': 0.30,       # 降低 5%
    'volume': 0.15,
    'macd': 0.20,
    'multi_level': 0.15,
    'external': 0.10,           # 降低 5%
    'center_momentum': 0.10,    # 新增 10%
}
```

**优点**: 模块独立，便于单独回测和优化

**缺点**: 中枢动量与缠论基础高度相关，独立计算可能重复

---

### 方案 C: 中枢动量作为后置过滤器

**核心思路**: 先计算综合置信度，再用中枢动量进行过滤

```python
# 1. 计算原有综合置信度
base_confidence = calculator.calculate(...)

# 2. 中枢动量过滤
center_analysis = analyzer.analyze(centers, segments, price)

if center_analysis.center_position == AFTER_THIRD:
    # 第三中枢后，降低置信度
    final_confidence = base_confidence * 0.7
elif center_analysis.momentum_status == DECREASING:
    # 动量衰减，降低置信度
    final_confidence = base_confidence * 0.85
else:
    final_confidence = base_confidence
```

**优点**: 实现简单，不影响现有逻辑

**缺点**: 过滤规则较粗糙，无法充分利用中枢信息

---

### 推荐方案: 方案 A (中枢动量作为 chanlun_base 增强层)

**理由**:

1. **理论一致性**: 中枢是缠论核心概念，应归入缠论基础维度
2. **避免重复**: 中枢动量与买卖点高度相关，独立计算会重复
3. **精细调整**: 可以在 chanlun_base 内部进行多维度调整
4. **向后兼容**: 不改变现有权重配置，便于回测对比

---

## 可信度提升策略

### 策略 1: 中枢序号可信度调整

```python
def get_center_position_bonus(centers, price):
    """
    根据中枢序号调整可信度
    
    缠论理论:
    - 第 1 中枢后: 趋势初现，可信度 +10%
    - 第 2 中枢后: 趋势确认，可信度 +15%
    - 第 3 中枢: 背驰风险，可信度 -15%
    - 第 3 中枢后: 高背驰风险，可信度 -25%
    """
    if not centers:
        return 0.0
    
    # 确定当前位置
    position = determine_center_position(centers, price)
    
    bonus_map = {
        CenterPosition.BEFORE_FIRST: 0.0,      # 无中枢，不调整
        CenterPosition.IN_FIRST: 0.05,         # 第一中枢中，轻微正面
        CenterPosition.AFTER_FIRST: 0.10,      # 第一中枢后，趋势初现
        CenterPosition.IN_SECOND: 0.10,        # 第二中枢中，正面
        CenterPosition.AFTER_SECOND: 0.15,     # 第二中枢后，趋势确认
        CenterPosition.IN_THIRD: -0.10,        # 第三中枢中，警惕
        CenterPosition.AFTER_THIRD: -0.25,     # 第三中枢后，背驰风险
        CenterPosition.EXTENSION: -0.05,       # 中枢延伸，级别扩张
    }
    
    return bonus_map.get(position, 0.0)
```

**实战效果**:

| 场景 | 原置信度 | 中枢序号调整 | 调整后 |
|------|---------|-------------|-------|
| buy2 @ 第 1 中枢后 | 60% | +10% | 70% |
| buy2 @ 第 2 中枢后 | 60% | +15% | 75% |
| buy1 @ 第 3 中枢后 | 65% | -25% | 40% ⚠️ |
| buy1 @ 第 1 中枢前 | 55% | 0% | 55% |

**核心价值**: 避免在第三中枢后盲目追 buy1，降低背驰风险

---

### 策略 2: 动量状态可信度调整

```python
def get_momentum_bonus(centers, segments):
    """
    根据动量状态调整可信度
    
    动量分析:
    - 动量增强: 趋势延续概率高，可信度 +10%
    - 动量稳定: 中性，不调整
    - 动量衰减: 趋势可能反转，可信度 -10%
    """
    if len(centers) < 2:
        return 0.0
    
    analyzer = CenterMomentumAnalyzer()
    momentum_status, momentum_score = analyzer.analyze_momentum(centers, segments)
    
    bonus_map = {
        MomentumStatus.INCREASING: 0.10,   # 动量增强，正面
        MomentumStatus.STABLE: 0.0,        # 动量稳定，中性
        MomentumStatus.DECREASING: -0.10,  # 动量衰减，负面
        MomentumStatus.UNKNOWN: 0.0,
    }
    
    return bonus_map.get(momentum_status, 0.0)
```

**实战效果**:

| 场景 | 原置信度 | 动量调整 | 调整后 |
|------|---------|---------|-------|
| buy2 + 动量增强 | 65% | +10% | 75% |
| buy2 + 动量稳定 | 65% | 0% | 65% |
| buy2 + 动量衰减 | 65% | -10% | 55% ⚠️ |

**核心价值**: 识别"假突破"，避免在动量衰减时入场

---

### 策略 3: 趋势延续性可信度调整

```python
def get_continuation_bonus(centers):
    """
    根据趋势延续概率调整可信度
    
    延续性评估:
    - 延续概率 > 70%: 趋势强劲，可信度 +10%
    - 延续概率 50-70%: 中性，不调整
    - 延续概率 < 50%: 趋势可能反转，可信度 -10%
    """
    if not centers:
        return 0.0
    
    analyzer = CenterMomentumAnalyzer()
    result = analyzer.analyze(centers, ...)
    
    if result.continuation_probability > 70:
        return 0.10
    elif result.continuation_probability < 50:
        return -0.10
    else:
        return 0.0
```

---

### 策略 4: 多级别中枢共振

```python
def multi_level_center_resonance(analysis_1d, analysis_30m, analysis_5m):
    """
    多级别中枢动量共振分析
    
    共振条件:
    1. 日线：第 2 中枢后，动量增强
    2. 30m: 第 1/2 中枢后，动量增强
    3. 方向一致：都是上涨或都是下跌
    
    共振成功 → 可信度 +20%
    """
    resonance_bonus = 0.0
    
    # 检查各级别中枢位置
    positions = [
        analysis_1d.center_position,
        analysis_30m.center_position,
        analysis_5m.center_position if analysis_5m else None
    ]
    
    # 检查动量状态
    momentums = [
        analysis_1d.momentum_status,
        analysis_30m.momentum_status,
        analysis_5m.momentum_status if analysis_5m else None
    ]
    
    # 检查趋势方向
    directions = [
        analysis_1d.trend_direction,
        analysis_30m.trend_direction,
    ]
    
    # 共振条件判断
    favorable_positions = sum(1 for p in positions if p in [
        CenterPosition.AFTER_FIRST,
        CenterPosition.AFTER_SECOND
    ])
    
    favorable_momentums = sum(1 for m in momentums if m == MomentumStatus.INCREASING)
    
    same_direction = len(set(directions)) == 1
    
    # 计算共振 bonus
    if favorable_positions >= 2 and favorable_momentums >= 2:
        resonance_bonus += 0.10
    
    if same_direction:
        resonance_bonus += 0.10
    
    return min(0.20, resonance_bonus)
```

**实战效果**:

| 场景 | 原置信度 | 共振调整 | 调整后 |
|------|---------|---------|-------|
| 单级别 buy2 | 60% | 0% | 60% |
| 双级别共振 | 60% | +15% | 75% |
| 三级别共振 | 60% | +20% | 80% ✅ |

**核心价值**: 捕捉高置信度机会，提高胜率

---

### 策略 5: 背驰风险预警

```python
def divergence_risk_warning(centers, price):
    """
    背驰风险预警
    
    背驰高风崄场景:
    1. 第三中枢后
    2. 动量明显衰减
    3. 价格创新高/新低但力度不足
    
    触发预警 → 强制降低可信度至 40% 以下
    """
    if not centers:
        return False, 0.0
    
    analyzer = CenterMomentumAnalyzer()
    result = analyzer.analyze(centers, ..., price)
    
    risk_score = 0.0
    
    # 第三中枢后 +30%
    if result.center_position == CenterPosition.AFTER_THIRD:
        risk_score += 0.30
    
    # 动量衰减 +20%
    if result.momentum_status == MomentumStatus.DECREASING:
        risk_score += 0.20
    
    # 反转风险 > 60% +20%
    if result.reversal_risk > 60:
        risk_score += 0.20
    
    # 判断是否触发预警
    if risk_score >= 0.50:
        return True, risk_score
    
    return False, risk_score
```

**实战应用**:

```python
# 在综合置信度计算中
is_risk, risk_score = divergence_risk_warning(centers, price)

if is_risk:
    # 强制降低可信度
    final_confidence = min(final_confidence, 0.40)
    operation_suggestion = OperationSuggestion.AVOID
    alert_message = "⚠️ 背驰风险预警！建议规避"
```

---

## 技术实现方案

### 文件结构

```
chanlunInvester/
├── python-layer/trading_system/
│   ├── center_momentum.py          # ✅ 已创建 (中枢动量分析核心)
│   └── center_momentum_confidence.py  # 🆕 新建 (可信度整合模块)
│
├── scripts/
│   ├── center_momentum_analysis.py    # ✅ 已创建 (分析脚本)
│   ├── confidence_calculator.py       # 🔄 修改 (整合中枢动量)
│   └── comprehensive_confidence_engine.py  # 🔄 修改 (引擎整合)
│
└── docs/
    ├── CENTER_MOMENTUM_MODULE.md      # ✅ 已创建 (使用文档)
    └── CENTER_MOMENTUM_INTEGRATION.md # 🆕 新建 (整合文档)
```

### 核心代码实现

#### 1. 中枢动量可信度整合模块

```python
# python-layer/trading_system/center_momentum_confidence.py

from center_momentum import (
    CenterMomentumAnalyzer,
    CenterPosition,
    MomentumStatus,
    TrendDirection
)
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CenterMomentumConfidence:
    """中枢动量可信度结果"""
    # 输入信息
    symbol: str
    level: str
    price: float
    
    # 中枢分析结果
    center_count: int
    center_position: CenterPosition
    momentum_status: MomentumStatus
    trend_direction: TrendDirection
    
    # 可信度调整
    position_bonus: float      # 中枢序号调整
    momentum_bonus: float      # 动量状态调整
    continuation_bonus: float  # 延续性调整
    total_bonus: float         # 总调整
    
    # 风险评估
    divergence_risk: bool      # 背驰风险
    reversal_risk: float       # 反转风险 (0-1)
    
    # 建议
    suggestion: str
    confidence_level: str      # HIGH/MEDIUM/LOW


class CenterMomentumConfidenceCalculator:
    """中枢动量可信度计算器"""
    
    def __init__(self):
        self.analyzer = CenterMomentumAnalyzer()
        
        # 配置参数
        self.POSITION_BONUS = {
            CenterPosition.BEFORE_FIRST: 0.00,
            CenterPosition.IN_FIRST: 0.05,
            CenterPosition.AFTER_FIRST: 0.10,
            CenterPosition.IN_SECOND: 0.10,
            CenterPosition.AFTER_SECOND: 0.15,
            CenterPosition.IN_THIRD: -0.10,
            CenterPosition.AFTER_THIRD: -0.25,
            CenterPosition.EXTENSION: -0.05,
        }
        
        self.MOMENTUM_BONUS = {
            MomentumStatus.INCREASING: 0.10,
            MomentumStatus.STABLE: 0.00,
            MomentumStatus.DECREASING: -0.10,
            MomentumStatus.UNKNOWN: 0.00,
        }
    
    def calculate(self, symbol: str, level: str, price: float,
                  centers: List, segments: List) -> CenterMomentumConfidence:
        """
        计算中枢动量可信度
        
        Args:
            symbol: 股票代码
            level: 级别
            price: 当前价格
            centers: 中枢列表
            segments: 线段列表
        
        Returns:
            CenterMomentumConfidence: 可信度结果
        """
        # 1. 执行中枢动量分析
        analysis = self.analyzer.analyze(centers, segments, price)
        
        # 2. 计算各维度调整
        position_bonus = self.POSITION_BONUS.get(analysis.center_position, 0.0)
        momentum_bonus = self.MOMENTUM_BONUS.get(analysis.momentum_status, 0.0)
        
        # 延续性调整
        if analysis.continuation_probability > 70:
            continuation_bonus = 0.10
        elif analysis.continuation_probability < 50:
            continuation_bonus = -0.10
        else:
            continuation_bonus = 0.0
        
        # 总调整
        total_bonus = position_bonus + momentum_bonus + continuation_bonus
        
        # 3. 背驰风险评估
        divergence_risk = (
            analysis.center_position == CenterPosition.AFTER_THIRD and
            analysis.momentum_status == MomentumStatus.DECREASING
        )
        
        reversal_risk = analysis.reversal_risk / 100.0
        
        # 4. 生成建议
        if divergence_risk or reversal_risk > 0.6:
            suggestion = "AVOID"
            confidence_level = "LOW"
        elif total_bonus > 0.20:
            suggestion = "STRONG"
            confidence_level = "HIGH"
        elif total_bonus > 0.10:
            suggestion = "FAVORABLE"
            confidence_level = "MEDIUM_HIGH"
        elif total_bonus > 0:
            suggestion = "NEUTRAL"
            confidence_level = "MEDIUM"
        else:
            suggestion = "CAUTION"
            confidence_level = "MEDIUM_LOW"
        
        return CenterMomentumConfidence(
            symbol=symbol,
            level=level,
            price=price,
            center_count=len(centers),
            center_position=analysis.center_position,
            momentum_status=analysis.momentum_status,
            trend_direction=analysis.trend_direction,
            position_bonus=position_bonus,
            momentum_bonus=momentum_bonus,
            continuation_bonus=continuation_bonus,
            total_bonus=total_bonus,
            divergence_risk=divergence_risk,
            reversal_risk=reversal_risk,
            suggestion=suggestion,
            confidence_level=confidence_level
        )
```

#### 2. 整合到 confidence_calculator.py

```python
# scripts/confidence_calculator.py 修改

from python_layer.trading_system.center_momentum_confidence import (
    CenterMomentumConfidenceCalculator
)

class ComprehensiveConfidenceCalculator:
    """综合可信度计算器 (整合中枢动量)"""
    
    def __init__(self):
        # ... 原有初始化 ...
        
        # 新增：中枢动量可信度计算器
        self.center_confidence_calc = CenterMomentumConfidenceCalculator()
    
    def calculate(self, symbol: str, signal_type: str, level: str, price: float,
                  prices: List[float], volumes: List[float],
                  macd_data: List,
                  centers: List = None, segments: List = None,
                  chanlun_base_confidence: float = 0.5,
                  ...) -> ComprehensiveConfidenceResult:
        """
        计算综合可信度 (整合中枢动量)
        
        新增参数:
            centers: 中枢列表
            segments: 线段列表
        """
        # ... 原有计算逻辑 ...
        
        # 【新增】中枢动量可信度计算
        center_confidence_result = None
        if centers and segments:
            center_confidence_result = self.center_confidence_calc.calculate(
                symbol=symbol,
                level=level,
                price=price,
                centers=centers,
                segments=segments
            )
            
            # 调整缠论基础置信度
            if center_confidence_result:
                # 应用中枢动量调整
                adjusted_chanlun_base = chanlun_base_confidence + center_confidence_result.total_bonus
                adjusted_chanlun_base = max(0.0, min(1.0, adjusted_chanlun_base))
                
                # 背驰风险强制降级
                if center_confidence_result.divergence_risk:
                    adjusted_chanlun_base = min(adjusted_chanlun_base, 0.40)
                
                chanlun_base_confidence = adjusted_chanlun_base
        
        # 继续原有计算流程...
        # ...
        
        # 在结果中包含中枢动量信息
        result = ComprehensiveConfidenceResult(
            # ... 原有字段 ...
            center_momentum_result=center_confidence_result,  # 新增
        )
        
        return result
```

#### 3. 整合到 monitor_all.py

```python
# monitor_all.py 修改

from scripts.confidence_calculator import ComprehensiveConfidenceCalculator
from python_layer.trading_system.center import CenterDetector
from python_layer.trading_system.center_momentum_confidence import CenterMomentumConfidenceCalculator

def analyze_symbol_with_center_momentum(symbol, data, level):
    """带中枢动量分析的标的分析"""
    
    # 1. 原有缠论结构分析
    fractals = calculate_fractals(data)
    pivots = calculate_pivots(data, fractals)
    segments = calculate_segments(pivots)
    
    # 2. 中枢检测
    center_det = CenterDetector(min_segments=3)
    centers = center_det.detect_centers(segments)
    
    # 3. 买卖点检测
    bsp_signals = detect_buy_sell_points(data, fractals, pivots, segments)
    
    # 4. 【新增】中枢动量分析
    price = data['Close'].iloc[-1]
    center_confidence = None
    if centers:
        center_calc = CenterMomentumConfidenceCalculator()
        center_confidence = center_calc.calculate(
            symbol=symbol,
            level=level,
            price=price,
            centers=centers,
            segments=segments
        )
    
    # 5. 综合可信度计算 (整合中枢动量)
    confidence_results = []
    for signal in bsp_signals:
        result = confidence_calc.calculate(
            symbol=symbol,
            signal_type=signal['type'],
            level=level,
            price=signal['price'],
            prices=data['Close'].tolist(),
            volumes=data['Volume'].tolist(),
            macd_data=macd_data,
            centers=centers,      # 新增
            segments=segments,    # 新增
            chanlun_base_confidence=0.6 if signal['type'] in ['buy2', 'sell2'] else 0.5,
        )
        confidence_results.append(result)
    
    return {
        'bsp_signals': bsp_signals,
        'centers': centers,
        'center_confidence': center_confidence,
        'confidence_results': confidence_results,
    }
```

---

### 警报推送增强

```python
# 在 send_telegram_alert 中整合中枢动量信息

def send_telegram_alert_with_center_momentum(symbol, signal, confidence_result, center_confidence):
    """
    发送带中枢动量信息的警报
    
    警报格式增强:
    原格式:
    🟢 SMR 30m 第二类买点 @ $11.51
    综合置信度：62% (MEDIUM)
    
    新格式:
    🟢 SMR 30m 第二类买点 @ $11.51
    综合置信度：72% (HIGH) ⬆️ +10%
    
    中枢分析:
    - 中枢序号：第 2 中枢后 ✅
    - 动量状态：增强 ✅
    - 延续概率：75%
    - 背驰风险：低 ✅
    
    操作建议：BUY (40-50% 仓位)
    """
    
    # 基础信息
    message = f"🟢 {symbol} {signal['level']}级别{signal['type']} @ ${signal['price']:.2f}\n\n"
    
    # 综合置信度 (显示调整)
    base_conf = confidence_result.final_confidence - center_confidence.total_bonus
    message += f"综合置信度：{confidence_result.final_confidence*100:.0f}% "
    message += f"({confidence_result.reliability_level.value.upper()})"
    
    if center_confidence.total_bonus > 0.05:
        message += f" ⬆️ +{center_confidence.total_bonus*100:.0f}%"
    elif center_confidence.total_bonus < -0.05:
        message += f" ⬇️ {center_confidence.total_bonus*100:.0f}%"
    
    message += "\n\n"
    
    # 中枢分析详情
    message += "中枢分析:\n"
    message += f"- 中枢序号：{center_confidence.center_position.value} "
    
    if center_confidence.center_position in [CenterPosition.AFTER_FIRST, CenterPosition.AFTER_SECOND]:
        message += "✅"
    elif center_confidence.center_position == CenterPosition.AFTER_THIRD:
        message += "⚠️"
    
    message += f"\n- 动量状态：{center_confidence.momentum_status.value} "
    
    if center_confidence.momentum_status == MomentumStatus.INCREASING:
        message += "✅"
    elif center_confidence.momentum_status == MomentumStatus.DECREASING:
        message += "⚠️"
    
    message += f"\n- 延续概率：{center_confidence.continuation_bonus*100:+.0f}%"
    message += f"\n- 背驰风险：{'高 ⚠️' if center_confidence.divergence_risk else '低 ✅'}"
    
    message += "\n\n"
    
    # 操作建议
    message += f"操作建议：{confidence_result.operation_suggestion.value} "
    message += f"({get_position_suggestion(confidence_result.final_confidence)})"
    
    # 发送警报
    send_telegram_message(message)
```

---

## 开发计划与验收

### 开发阶段

| 阶段 | 任务 | 预计时间 | 状态 |
|------|------|---------|------|
| **Phase 1** | 中枢动量可信度计算器开发 | 1 天 | ⏳ 待开始 |
| **Phase 2** | 整合到 confidence_calculator.py | 1 天 | ⏳ 待开始 |
| **Phase 3** | 整合到 monitor_all.py | 1 天 | ⏳ 待开始 |
| **Phase 4** | 警报推送增强 | 0.5 天 | ⏳ 待开始 |
| **Phase 5** | 回测验证 | 2-3 天 | ⏳ 待开始 |
| **Phase 6** | 参数优化 | 1-2 天 | ⏳ 待开始 |

### 验收标准

| 指标 | 目标 | 验收方法 |
|------|------|---------|
| **代码完整** | 100% | 代码审查 |
| **单元测试** | 通过率≥90% | pytest |
| **集成测试** | 功能完整 | 实盘模拟 |
| **回测提升** | 胜率 +5-10% | 历史数据回测 |
| **背驰规避** | 第三中枢后背驰识别率≥80% | 案例分析 |
| **文档完整** | 100% | 文档审查 |

### 回测验证方案

```python
# 回测对比
# 方案 A: 原系统 (无中枢动量)
original_results = backtest_original_strategy(data)

# 方案 B: 新系统 (整合中枢动量)
enhanced_results = backtest_enhanced_strategy(data)

# 对比指标
metrics_comparison = {
    '胜率': (original_results.win_rate, enhanced_results.win_rate),
    '盈亏比': (original_results.profit_loss_ratio, enhanced_results.profit_loss_ratio),
    '最大回撤': (original_results.max_drawdown, enhanced_results.max_drawdown),
    '年化收益': (original_results.annual_return, enhanced_results.annual_return),
    '背驰规避率': (N/A, enhanced_results.divergence_avoidance_rate),
}

# 验收标准
assert enhanced_results.win_rate >= original_results.win_rate + 0.05
assert enhanced_results.max_drawdown <= original_results.max_drawdown * 0.8
assert enhanced_results.divergence_avoidance_rate >= 0.80
```

---

## 预期效果

### 可信度提升效果

| 场景 | 原置信度 | 新置信度 | 提升 |
|------|---------|---------|------|
| buy2 @ 第 2 中枢后 + 动量增强 | 60% | 85% | +25% ✅ |
| buy2 @ 第 1 中枢后 + 动量稳定 | 60% | 70% | +10% |
| buy1 @ 第 3 中枢后 + 动量衰减 | 65% | 35% | -30% ⚠️ (降级) |
| buy1 @ 第 1 中枢前 + 动量增强 | 55% | 70% | +15% |

### 实战价值

1. **提高胜率**: 通过中枢序号筛选，避免低质量信号
2. **规避背驰**: 第三中枢后强制降级，降低反转风险
3. **捕捉共振**: 多级别中枢共振识别高置信度机会
4. **精细决策**: 中枢动量提供额外维度，支持更精细的仓位管理

### 风险控制

| 风险 | 控制措施 |
|------|---------|
| 过度拟合 | 参数通过回测验证，不使用经验值 |
| 计算复杂度 | 中枢检测复用现有模块，增量计算 |
| 误判风险 | 背驰风险预警采用保守策略 |
| 性能影响 | 中枢动量分析延迟 < 100ms |

---

## 总结

### 核心创新

1. **中枢序号量化**: 将缠论定性分析转化为量化调整因子
2. **动量状态评估**: 多维度分析中枢间动量变化
3. **背驰风险预警**: 第三中枢后强制降级，规避反转风险
4. **多级别共振**: 跨级别中枢动量共振识别高置信度机会

### 整合优势

1. **向后兼容**: 不改变现有权重配置，便于回测对比
2. **理论一致**: 中枢动量归入缠论基础维度，符合缠论理论
3. **灵活配置**: 调整参数可通过配置修改，无需改代码
4. **渐进式升级**: 可以逐步启用，不影响现有系统稳定

### 下一步行动

1. ✅ 中枢动量核心模块开发完成
2. ⏳ 中枢动量可信度计算器开发
3. ⏳ 整合到 confidence_calculator.py
4. ⏳ 整合到 monitor_all.py
5. ⏳ 回测验证与参数优化

---

**文档版本**: v6.0-beta  
**创建日期**: 2026-04-17  
**作者**: ChanLun AI Agent  
**状态**: 🟡 待审批
