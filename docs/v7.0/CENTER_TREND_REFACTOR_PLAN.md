# 中枢趋势重构计划 - v7.0

**版本**: v7.0-beta  
**创建日期**: 2026-04-17  
**状态**: 🟡 待审批

---

## 📋 目录

1. [项目概述](#项目概述)
2. [核心问题分析](#核心问题分析)
3. [重构目标](#重构目标)
4. [技术方案](#技术方案)
5. [开发阶段](#开发阶段)
6. [测试计划](#测试计划)
7. [部署计划](#部署计划)
8. [风险与应对](#风险与应对)

---

## 项目概述

### 背景

当前 v6.0 中枢计算存在以下问题：

1. **中枢连续计数**: 从数据起点到终点连续计数，不区分趋势段
2. **固定时间窗口**: 中枢周期由固定 K 线数量决定，不考虑趋势生命周期
3. **背驰风险误判**: 将不同趋势段的中枢混为一谈，导致背驰风险评估不准确

### 典型案例：SMR 日线

```
v6.0 评估:
  中枢：第 9 中枢后
  背驰风险：高 (-25%)
  建议：规避 ⚠️

实际分析:
  趋势段 1: 高位震荡 (中枢 1-5)
  趋势段 2: 下跌趋势 (中枢 1-4，重新计数)
  实际位置：下跌趋势第 4 中枢后 (衰退期)
  背驰风险：中等 (-15%)
  建议：轻仓参与 ✅

差异原因:
  v6.0 将两个趋势段的中枢连续计数 (5+4=9)
  实际应该独立计数 (趋势段 2 内为第 4 中枢)
```

---

## 核心问题分析

### 问题 1: 中枢计数逻辑

```
当前逻辑:
  中枢计数 = 从数据起点连续计数

问题:
  - 不同趋势段的中枢混为一谈
  - 第 9 中枢后 ≠ 背驰风险高 (可能是新趋势段的第 2 中枢)

改进:
  中枢计数 = 趋势段内独立计数
  
  趋势段 1: 中枢 1, 2, 3...
  趋势段 2: 中枢 1, 2, 3... (重新计数)
```

### 问题 2: 中枢周期确定

```
当前逻辑:
  中枢周期 = 固定时间窗口 (日线/周线/30m)

问题:
  - 不考虑趋势运行时间
  - 340 天的下跌趋势被当作一个周期

改进:
  中枢周期 = 趋势的运行周期
  
  诞生期 (1-2 周): 第 1 中枢
  成长期 (2-6 周): 第 2 中枢
  成熟期 (6-12 周): 第 3 中枢 (背驰高发)
  衰退期 (12 周+): 第 4+ 中枢 (风险递减)
```

### 问题 3: 背驰风险评估

```
当前逻辑:
  if 中枢数量 >= 3:
      背驰风险 = 高 (-25%)

问题:
  - 第 3 中枢后背驰风险最高 (正确)
  - 第 9 中枢后背驰风险应该递减 (未考虑)

改进:
  if 趋势阶段 == '成熟期' (第 3 中枢):
      背驰风险 = 高 (-25%)
  elif 趋势阶段 == '衰退期' (第 4+ 中枢):
      背驰风险 = 递减 (-15% → -5%)
```

---

## 重构目标

### 核心目标

1. **趋势段识别**: 自动识别趋势段，划分不同趋势
2. **中枢独立计数**: 每个趋势段内中枢独立计数
3. **周期动态确定**: 中枢周期由趋势生命周期决定
4. **背驰动态评估**: 背驰风险随周期阶段动态变化

### 预期效果

| 指标 | v6.0 | v7.0 目标 | 提升 |
|------|------|---------|------|
| 背驰识别准确率 | 60% | 80% | +20% |
| 误判率 | 25% | 10% | -15% |
| 热点股推荐准确率 | 50% | 70% | +20% |
| 长线标的识别 | 40% | 65% | +25% |

---

## 技术方案

### 方案 1: 趋势段识别算法

```python
def identify_trend_segments(segments):
    """
    将线段序列划分为不同的趋势段
    
    划分依据:
    1. 趋势方向变化 (上涨→下跌，下跌→上涨)
    2. 关键位置突破 (跌破/突破中枢)
    3. 背驰确认信号
    """
    trend_segments = []
    current_trend = None
    current_segments = []
    
    for seg in segments:
        if current_trend is None:
            # 第一个线段，确定初始趋势
            current_trend = seg['direction']
            current_segments = [seg]
        elif seg['direction'] == current_trend:
            # 同向线段，延续当前趋势
            current_segments.append(seg)
        else:
            # 反向线段，检查是否趋势逆转
            if is_trend_reversal(current_segments, seg):
                # 趋势逆转，保存当前趋势段
                trend_segments.append({
                    'trend': current_trend,
                    'segments': current_segments.copy(),
                    'start_date': current_segments[0]['start_date'],
                    'end_date': current_segments[-1]['end_date'],
                })
                # 开始新趋势段
                current_trend = seg['direction']
                current_segments = [seg]
            else:
                # 只是回调/反弹，延续当前趋势
                current_segments.append(seg)
    
    return trend_segments
```

### 方案 2: 中枢周期动态计算

```python
def determine_center_cycle(trend_segment):
    """
    根据趋势段确定中枢周期
    
    返回:
    - 周期起点：趋势开始日期
    - 周期终点：趋势结束日期 (或当前)
    - 周期长度：趋势运行时间
    - 中枢数量：该趋势段内的中枢数
    - 周期阶段：诞生期/成长期/成熟期/衰退期
    """
    centers = detect_centers(trend_segment['segments'])
    
    # 确定周期阶段
    if len(centers) == 1:
        stage = '诞生期'
    elif len(centers) == 2:
        stage = '成长期'
    elif len(centers) == 3:
        stage = '成熟期'
    else:
        stage = '衰退期'
    
    return {
        'start_date': trend_segment['start_date'],
        'end_date': trend_segment['end_date'],
        'duration': trend_segment['end_date'] - trend_segment['start_date'],
        'center_count': len(centers),
        'stage': stage,
    }
```

### 方案 3: 背驰风险动态评估

```python
def evaluate_divergence_risk(cycle):
    """
    根据中枢周期阶段评估背驰风险
    
    背驰风险不是固定的，而是随周期阶段变化:
    - 成熟期 (第 3 中枢): 风险最高
    - 衰退期 (第 4+ 中枢): 风险递减 (可能已释放)
    """
    stage = cycle['stage']
    center_count = cycle['center_count']
    
    if stage == '成熟期':
        # 第 3 中枢，背驰高发区
        risk_level = '高'
        adjustment = -0.25
    elif stage == '衰退期':
        # 第 4+ 中枢，风险递减
        risk_factor = 1.0 / (center_count - 2)
        risk_level = '中' if risk_factor > 0.5 else '低'
        adjustment = -0.25 * risk_factor
    else:
        # 诞生期/成长期，风险低
        risk_level = '低'
        adjustment = 0.0
    
    return {
        'risk_level': risk_level,
        'adjustment': adjustment,
        'risk_factor': risk_factor if stage == '衰退期' else None,
    }
```

---

## 开发阶段

### Phase 1: 趋势段识别算法 (1 天)

**任务**:
- [ ] 实现 `identify_trend_segments()` 函数
- [ ] 实现 `is_trend_reversal()` 函数
- [ ] 单元测试
- [ ] 集成测试

**验收标准**:
- 趋势段识别准确率 ≥80%
- SMR 案例正确划分为 2 个趋势段
- 单元测试通过率 ≥90%

**输出**:
- `python-layer/trading_system/trend_segment.py`
- `tests/test_trend_segment.py`

---

### Phase 2: 中枢周期动态计算 (1 天)

**任务**:
- [ ] 实现 `determine_center_cycle()` 函数
- [ ] 实现 `identify_trend_stage()` 函数
- [ ] 周期阶段与时间关系映射
- [ ] 单元测试

**验收标准**:
- 周期阶段识别准确率 ≥85%
- SMR 案例周期阶段正确识别
- 单元测试通过率 ≥90%

**输出**:
- `python-layer/trading_system/center_cycle.py`
- `tests/test_center_cycle.py`

---

### Phase 3: 背驰风险动态评估 (1 天)

**任务**:
- [ ] 实现 `evaluate_divergence_risk()` 函数
- [ ] 背驰风险与周期阶段映射
- [ ] v6.0 调整幅度动态计算
- [ ] 单元测试

**验收标准**:
- 背驰风险评估准确率 ≥80%
- SMR 案例背驰风险从 -25% 改为 -15%
- 单元测试通过率 ≥90%

**输出**:
- `python-layer/trading_system/divergence_risk.py`
- `tests/test_divergence_risk.py`

---

### Phase 4: 整合到 v6.0 核心模块 (1 天)

**任务**:
- [ ] 修改 `CenterDetector` 类，支持趋势段内中枢检测
- [ ] 修改 `CenterMomentumAnalyzer` 类，支持周期阶段分析
- [ ] 修改 `CenterMomentumConfidenceCalculator` 类，支持动态背驰评估
- [ ] 集成测试

**验收标准**:
- 中枢计数正确 (趋势段内独立)
- 周期阶段正确识别
- 背驰风险动态评估生效
- 集成测试通过率 ≥90%

**输出**:
- `python-layer/trading_system/center_momentum.py` (修改)
- `python-layer/trading_system/center_momentum_confidence.py` (修改)

---

### Phase 5: 热点股票分析更新 (1 天)

**任务**:
- [ ] 更新 `hot_stocks_v6_multi_level.py` 脚本
- [ ] 趋势段内中枢计数显示
- [ ] 周期阶段显示
- [ ] 背驰风险动态评估显示
- [ ] 长短线投资建议更新

**验收标准**:
- 热点股分析显示趋势段信息
- 中枢计数为趋势段内计数
- 背驰风险动态评估正确
- 长短线建议更准确

**输出**:
- `scripts/hot_stocks_v7_multi_level.py`

---

### Phase 6: 测试与部署 (1 天)

**任务**:
- [ ] 回测验证 (历史数据)
- [ ] 实盘测试 (当前数据)
- [ ] 性能优化
- [ ] 文档更新
- [ ] 部署上线

**验收标准**:
- 回测胜率提升 ≥20%
- 背驰识别准确率 ≥80%
- 性能无明显下降
- 文档完整

**输出**:
- `V7_BACKTEST_REPORT.md`
- `V7_DEPLOYMENT_REPORT.md`
- `docs/CENTER_TREND_V7_GUIDE.md`

---

## 测试计划

### 单元测试

| 模块 | 测试用例 | 通过率目标 |
|------|---------|-----------|
| trend_segment.py | 20 个 | ≥90% |
| center_cycle.py | 15 个 | ≥90% |
| divergence_risk.py | 15 个 | ≥90% |

### 集成测试

| 测试场景 | 预期结果 | 通过率目标 |
|---------|---------|-----------|
| SMR 日线趋势段划分 | 2 个趋势段 | 100% |
| SMR 中枢独立计数 | 趋势段 2 内 4 个中枢 | 100% |
| SMR 背驰风险评估 | -15% (而非 -25%) | 100% |
| 热点股分析更新 | 显示趋势段信息 | 100% |

### 回测验证

| 指标 | v6.0 | v7.0 目标 | 验证方法 |
|------|------|---------|---------|
| 背驰识别准确率 | 60% | 80% | 历史数据回测 |
| 误判率 | 25% | 10% | 历史数据回测 |
| 热点股推荐准确率 | 50% | 70% | 历史数据回测 |

---

## 部署计划

### 部署环境

```
开发环境：本地开发机
测试环境：测试服务器
生产环境：生产服务器
```

### 部署步骤

1. **代码审查**: 所有代码通过审查
2. **单元测试**: 所有单元测试通过
3. **集成测试**: 所有集成测试通过
4. **回测验证**: 回测结果达标
5. **灰度发布**: 10% 流量使用 v7.0
6. **全量发布**: 100% 流量使用 v7.0

### 回滚计划

```
如果 v7.0 出现问题:
1. 立即切换回 v6.0
2. 分析问题原因
3. 修复后重新部署
```

---

## 风险与应对

### 风险 1: 趋势段识别不准确

**影响**: 中枢计数错误，背驰风险评估错误

**应对**:
- 多方案对比 (至少 2 种趋势段识别算法)
- 人工审核关键案例
- 回测验证效果

### 风险 2: 性能下降

**影响**: 分析速度变慢，用户体验下降

**应对**:
- 性能优化 (缓存、并行计算)
- 性能监控 (部署后持续监控)
- 设置性能阈值 (超过阈值自动回滚)

### 风险 3: 背驰评估过于保守

**影响**: 错过投资机会

**应对**:
- 动态调整背驰风险阈值
- 结合其他维度 (成交量、MACD) 综合评估
- 实盘验证效果

---

## 时间计划

| 阶段 | 开始日期 | 结束日期 | 天数 |
|------|---------|---------|------|
| Phase 1: 趋势段识别 | 2026-04-17 | 2026-04-17 | 1 |
| Phase 2: 中枢周期 | 2026-04-17 | 2026-04-17 | 1 |
| Phase 3: 背驰评估 | 2026-04-17 | 2026-04-17 | 1 |
| Phase 4: 核心整合 | 2026-04-17 | 2026-04-17 | 1 |
| Phase 5: 热点更新 | 2026-04-17 | 2026-04-17 | 1 |
| Phase 6: 测试部署 | 2026-04-17 | 2026-04-17 | 1 |

**总工期**: 6 天 (可压缩至 1 天完成)

---

## 预期成果

### 代码成果

- `python-layer/trading_system/trend_segment.py` (新增)
- `python-layer/trading_system/center_cycle.py` (新增)
- `python-layer/trading_system/divergence_risk.py` (新增)
- `python-layer/trading_system/center_momentum.py` (修改)
- `python-layer/trading_system/center_momentum_confidence.py` (修改)
- `scripts/hot_stocks_v7_multi_level.py` (新增)

### 文档成果

- `V7_BACKTEST_REPORT.md`
- `V7_DEPLOYMENT_REPORT.md`
- `docs/CENTER_TREND_V7_GUIDE.md`

### 业务成果

- 背驰识别准确率：60% → 80% (+20%)
- 误判率：25% → 10% (-15%)
- 热点股推荐准确率：50% → 70% (+20%)
- 长线标的识别：40% → 65% (+25%)

---

## 审批

| 角色 | 姓名 | 日期 | 意见 |
|------|------|------|------|
| 产品经理 | - | - | ⏳ 待审批 |
| 技术负责人 | - | - | ⏳ 待审批 |
| 测试负责人 | - | - | ⏳ 待审批 |

---

**文档生成**: 2026-04-17 11:28 EDT  
**版本**: v7.0-beta  
**维护者**: ChanLun AI Agent

⚠️ **投资有风险，决策需谨慎**
