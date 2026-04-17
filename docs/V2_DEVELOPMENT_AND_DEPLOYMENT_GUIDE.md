# 缠论 v2.0 开发与部署指南

**更新日期**: 2026-04-16 23:15 EDT  
**版本**: v2.0-beta  
**状态**: 🟢 准备发布

---

## 📋 目录

1. [开发环境准备](#开发环境准备)
2. [本地开发](#本地开发)
3. [测试验证](#测试验证)
4. [部署流程](#部署流程)
5. [发布计划](#发布计划)
6. [运维监控](#运维监控)

---

## 🛠️ 开发环境准备

### 1. 系统要求

**最低配置**:
- Python 3.10+
- 内存：4GB+
- 磁盘：10GB+
- 网络：可访问 Yahoo Finance

**推荐配置**:
- Python 3.10+
- 内存：8GB+
- 磁盘：20GB+
- 网络：稳定连接

---

### 2. 安装依赖

```bash
# 进入项目目录
cd /home/wei/.openclaw/workspace/chanlunInvester

# 创建虚拟环境 (如果还没有)
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r python-layer/requirements.txt

# 验证安装
python -c "import yfinance; import numpy; print('依赖安装成功')"
```

**主要依赖**:
```
yfinance>=0.2.0
numpy>=1.20.0
pandas>=1.3.0
```

---

### 3. 获取代码

**当前状态**: 代码已在 `chanlun-v2` 分支

```bash
# 切换到 v2.0 分支
git checkout chanlun-v2

# 查看当前状态
git status

# 查看提交历史
git log --oneline -10
```

**文件结构**:
```
chanlunInvester/
├── scripts/                      # 核心脚本
│   ├── comprehensive_confidence_engine.py  # v2.0 统一引擎
│   ├── trend_start_detector.py             # Phase 1 起势检测
│   ├── trend_decay_monitor.py              # Phase 2 衰减监测
│   ├── trend_reversal_warning.py           # Phase 3 反转预警
│   ├── backtest_*.py                       # 回测脚本
│   └── compare_v2_v5_*.py                  # 对比工具
├── tests/                        # 单元测试
│   ├── test_trend_start_detector.py
│   ├── test_trend_decay_monitor.py
│   ├── test_trend_reversal_warning.py
│   └── test_comprehensive_confidence.py
├── docs/                         # 文档
│   ├── V2_*.md                   # v2.0 文档
│   └── PHASE*_ACCEPTANCE_REPORT.md
└── python-layer/                 # Python 核心层
    └── trading_system/           # 交易系统
```

---

## 💻 本地开发

### 1. 快速测试

**测试 v2.0 引擎**:
```bash
cd /home/wei/.openclaw/workspace/chanlunInvester
source venv/bin/activate

# 运行综合置信度引擎测试
python scripts/comprehensive_confidence_engine.py
```

**预期输出**:
```
======================================================================
综合置信度引擎测试
======================================================================

获取 TSLA 数据...
======================================================================
📊 综合置信度评估 - TSLA (1d)
======================================================================
时间：2026-04-16 19:28:23

综合置信度：67%
置信度区间：HIGH
风险等级：  🟡 MEDIUM

买卖点检测：❌ 无
提前预警：  ✅ 已提前 2 天预警

操作建议：🟢 BUY
建议仓位：60%
```

---

### 2. 对比测试

**v2.0 vs v5.3 对比**:
```bash
# 运行对比分析
python scripts/compare_v2_v5_monitor.py
```

**预期输出**:
```
======================================================================
缠论 v2.0 vs v5.3 监控股票对比分析
======================================================================
  SMR: v2.0 🚀 STRONG_BUY (92%), v5.3 buy1
  其他：v2.0 🟢 BUY (67%), v5.3 ❌ 无

v2.0: 买入 12/12 (100.0%), 平均置信度 68.8%
v5.3: 信号 1/12 (8.3%)
```

---

### 3. 单元测试

**运行所有测试**:
```bash
# Phase 1 测试
python tests/test_trend_start_detector.py

# Phase 2 测试
python tests/test_trend_decay_monitor.py

# Phase 3 测试
python tests/test_trend_reversal_warning.py

# Phase 4 测试
python tests/test_comprehensive_confidence.py
```

**预期结果**:
```
测试结果：X 通过，0 失败
通过率：100.0%
✅ 单元测试通过验收标准 (≥90%)
```

---

### 4. 回测验证

**运行回测**:
```bash
# Phase 1 回测
python scripts/backtest_trend_start.py

# Phase 2 回测
python scripts/backtest_trend_decay.py

# Phase 3 回测
python scripts/backtest_trend_reversal.py

# Phase 4 回测
python scripts/backtest_comprehensive.py
```

**预期关键指标**:
```
Phase 1: 胜率≥65%, 提前天数≥3 天
Phase 2: 准确率≥80%, 误报率<20%
Phase 3: 识别率≥75%, 利润保住率≥40%
Phase 4: 误差<18%
```

---

## 🧪 测试验证

### 1. 功能测试清单

**核心功能测试**:
- [ ] v5.3 买卖点检测正常工作
- [ ] Phase 1 起势检测正常工作
- [ ] Phase 2 衰减监测正常工作
- [ ] Phase 3 反转预警正常工作
- [ ] 综合置信度计算正确
- [ ] 统一输出格式正确
- [ ] v5.3 确认奖励正确 (+25%)

**对比测试**:
- [ ] v2.0 vs v5.3 对比正确
- [ ] 双系统确认股票置信度提升
- [ ] 区分度明显 (92% vs 67%)

---

### 2. 性能测试

**单股票分析时间**:
```bash
time python -c "
from scripts.comprehensive_confidence_engine import ComprehensiveConfidenceEngine
import yfinance as yf
data = yf.Ticker('SMR').history(period='60d')
# ... 分析代码
"
```

**预期**: <1 秒/股票

**批量分析时间**:
```bash
time python scripts/compare_v2_v5_monitor.py
```

**预期**: <2 分钟 (12 只股票)

---

### 3. 验收测试

**验收标准**:
- [ ] 11/15 回测指标达标
- [ ] 单元测试通过率≥90%
- [ ] 文档完整
- [ ] 无严重 Bug

**验收流程**:
1. 运行所有单元测试
2. 运行所有回测
3. 检查回测结果
4. 审查代码
5. 审查文档
6. 签署验收报告

---

## 🚀 部署流程

### 1. 部署前准备

**检查清单**:
- [ ] 所有测试通过
- [ ] 回测结果达标
- [ ] 文档完整
- [ ] 代码审查完成
- [ ] 版本号确认 (v2.0-beta)

**打包**:
```bash
# 创建发布包
cd /home/wei/.openclaw/workspace/chanlunInvester
tar -czf chanlun_v2_beta.tar.gz \
    scripts/ \
    tests/ \
    docs/ \
    python-layer/ \
    v2_requirements.txt

# 验证包
tar -tzf chanlun_v2_beta.tar.gz
```

---

### 2. 部署到生产环境

**步骤 1: 备份现有版本**:
```bash
# 备份 v5.3 (如果还在使用)
cp -r /path/to/production/chanlunInvester \
      /path/to/backup/chanlunInvester_v5.3_$(date +%Y%m%d)
```

**步骤 2: 上传新版本**:
```bash
# 上传发布包
scp chanlun_v2_beta.tar.gz user@production:/tmp/

# 解压
ssh user@production
cd /path/to/production
tar -xzf /tmp/chanlun_v2_beta.tar.gz
```

**步骤 3: 安装依赖**:
```bash
cd /path/to/production
source venv/bin/activate
pip install -r python-layer/requirements.txt
```

**步骤 4: 验证部署**:
```bash
# 运行快速测试
python scripts/comprehensive_confidence_engine.py

# 验证输出
python scripts/compare_v2_v5_monitor.py
```

**步骤 5: 切换流量**:
```bash
# 如果是蓝绿部署
# 1. 启动 v2.0 实例
# 2. 验证健康检查
# 3. 切换负载均衡
# 4. 监控错误率
```

---

### 3. 部署验证

**部署后测试**:
```bash
# 1. 基础功能测试
python scripts/comprehensive_confidence_engine.py

# 2. 对比测试
python scripts/compare_v2_v5_monitor.py

# 3. 监控股票分析
python monitor_all.py

# 4. 检查日志
tail -f logs/*.log
```

**验证清单**:
- [ ] 综合置信度引擎正常工作
- [ ] v5.3 买卖点检测正常
- [ ] 提前预警正常
- [ ] 统一输出正常
- [ ] 日志正常
- [ ] 无错误报警

---

## 📅 发布计划

### v2.0-beta (2026-04-18)

**发布内容**:
- ✅ 核心功能完整
- ✅ 11/15 指标达标
- ✅ 文档完整
- ⚠️ 4 个指标接近达标 (待优化)

**发布范围**:
- 内部测试
- 核心用户
- 收集反馈

**发布步骤**:
1. 创建 GitHub Release (v2.0-beta)
2. 发布到 chanlun-v2 分支
3. 通知测试用户
4. 收集反馈 (≥5 条)

---

### v2.0 正式版 (2026-04-20)

**发布条件**:
- [ ] 收集≥5 条 beta 反馈
- [ ] 修复严重 Bug
- [ ] 优化接近达标指标
- [ ] 完成最终验收

**发布范围**:
- 所有用户
- 生产环境

**发布步骤**:
1. 合并 chanlun-v2 到 main 分支
2. 创建 GitHub Release (v2.0)
3. 更新生产环境
4. 发布公告

---

## 📊 运维监控

### 1. 监控指标

**核心指标**:
- 分析成功率：≥99%
- 平均响应时间：<1 秒/股票
- 错误率：<1%
- 数据获取成功率：≥95%

**业务指标**:
- 信号准确率：≥75%
- 提前预警准确率：≥80%
- 用户满意度：≥4/5

---

### 2. 日志监控

**关键日志**:
```bash
# 查看错误日志
tail -f logs/error.log

# 查看分析日志
tail -f logs/analysis.log

# 查看回测日志
tail -f logs/backtest.log
```

**告警规则**:
- 错误率>5% → 告警
- 响应时间>5 秒 → 告警
- 数据获取失败>10 次 → 告警

---

### 3. 性能优化

**优化方向**:
1. 缓存历史数据 (减少 API 调用)
2. 并行分析多股票 (提升速度)
3. 优化中枢检测算法 (提升性能)

**监控工具**:
```bash
# 使用 top 监控 CPU
top -p $(pgrep -f comprehensive_confidence)

# 使用 memory 监控内存
free -h

# 使用 netstat 监控网络
netstat -an | grep ESTABLISHED | wc -l
```

---

## 📞 快速参考

### 开发命令

```bash
# 运行测试
python tests/test_comprehensive_confidence.py

# 运行回测
python scripts/backtest_comprehensive.py

# 对比分析
python scripts/compare_v2_v5_monitor.py

# 查看文档
cat docs/V2_DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md
```

### 部署命令

```bash
# 打包
tar -czf chanlun_v2_beta.tar.gz scripts/ tests/ docs/ python-layer/

# 上传
scp chanlun_v2_beta.tar.gz user@production:/tmp/

# 部署
ssh user@production 'cd /path/to/production && tar -xzf /tmp/chanlun_v2_beta.tar.gz'
```

---

## 🙏 致谢

感谢所有参与开发和测试的团队成员！

---

**文档生成**: 2026-04-16 23:15 EDT  
**生成者**: ChanLun AI Agent  
**版本**: v2.0-beta  
**状态**: 🟢 准备发布
