# 分支管理总结

**日期**: 2026-04-16 17:15 EDT  
**操作**: 版本备份 + 新分支开发

---

## 📊 分支结构

```
main (与 origin/main 同步)
  │
  └── chanlun-origin (v5.3 完整版备份) ✅ 已推送
        │
        └── chanlun-v2 (v2.0 改进版开发中) 🟡 进行中
```

---

## 📁 分支详情

### 1. main 分支

**状态**: 与远程同步  
**最新提交**: `d218fb7 docs: 添加 4/10 收盘汇报和周总结`

**用途**: 主分支，稳定版本

---

### 2. chanlun-origin 分支 ✅

**创建时间**: 2026-04-16 17:09 EDT  
**最新提交**: `22a08bd v5.3 - 缠论系统完整版`  
**状态**: ✅ 已推送到 GitHub

**包含内容**:
- 52 个文件
- 13,455 行新增代码
- 中枢判断逻辑
- buy1 检查逻辑
- 综合可信度系统
- 成交量 + MACD 整合
- 热点股票扫描系统

**v5.3 核心功能**:
1. ✅ 中枢检测 (CenterDetector)
2. ✅ buy1/buy2/sell1/sell2 检测
3. ✅ buy1 确认检查
4. ✅ 中枢验证逻辑
5. ✅ 综合可信度计算
6. ✅ 成交量确认
7. ✅ MACD 高级分析

**访问方式**:
```bash
git checkout chanlun-origin
```

**GitHub**:
```
https://github.com/weisenchen/chanlunInvester/tree/chanlun-origin
```

---

### 3. chanlun-v2 分支 🟡

**创建时间**: 2026-04-16 17:10 EDT  
**最新提交**: `3b7d223 添加 Phase 1 开发总结文档`  
**状态**: 🟡 开发中

**开发目标**: 缠论改进版 v2.0
**核心理念**: 从"事后确认"到"事前预警"

**Phase 1 (进行中)**:
- ✅ 趋势起势检测模块
  - 中枢突破检测 (25%)
  - 动量加速检测 (20%)
  - 量能放大检测 (20%)
  - 小级别共振检测 (15%)
  - 均线多头检测 (10%)

**后续计划**:
- Phase 2: 趋势衰减监测 (1 周)
- Phase 3: 趋势反转预警 (1 周)
- Phase 4: 综合置信度引擎 (1 周)
- Phase 5: 资金管理系统 (1 周)
- Phase 6: 回测验证框架 (2 周)
- Phase 7: 实盘测试 (4 周)

**访问方式**:
```bash
git checkout chanlun-v2
```

**GitHub**:
```
https://github.com/weisenchen/chanlunInvester/tree/chanlun-v2
```

---

## 🔄 分支切换指南

### 查看当前分支
```bash
git branch
```

### 切换到 v5.3 完整版
```bash
git checkout chanlun-origin
```

### 切换到 v2.0 开发版
```bash
git checkout chanlun-v2
```

### 切换回 main
```bash
git checkout main
```

---

## 📊 版本对比

| 特性 | v5.3 (chanlun-origin) | v2.0 (chanlun-v2) |
|------|----------------------|------------------|
| **定位** | 缠论完整版 | 缠论改进版 |
| **入场时机** | 背驰确认后 | 起势预警 (提前 3-5 天) |
| **离场时机** | 反转确认后 | 衰减预警 (提前 3-5 天) |
| **中枢判断** | ✅ 完整 | ✅ 继承 + 增强 |
| **买卖点检测** | ✅ buy1/2/3 | ✅ 继承 + 起势检测 |
| **置信度** | ✅ 基础量化 | ✅ 高级量化模型 |
| **资金管理** | ❌ 无 | 🟡 计划中 |
| **回测验证** | ❌ 无 | 🟡 计划中 |

---

## 📝 提交历史

### chanlun-v2 分支
```
3b7d223 添加 Phase 1 开发总结文档
e6730cc v2.0-alpha - Phase 1 趋势起势检测模块 (初始版本)
22a08bd v5.3 - 缠论系统完整版 (中枢判断+buy1 检查 + 综合可信度)
```

### chanlun-origin 分支
```
22a08bd v5.3 - 缠论系统完整版 (中枢判断+buy1 检查 + 综合可信度)
d218fb7 docs: 添加 4/10 收盘汇报和周总结
...
```

---

## 🎯 开发路线图

### 短期 (本周)
- [ ] 完善 Phase 1 (市场情绪检测)
- [ ] 编写单元测试
- [ ] 参数回测优化

### 中期 (1 个月内)
- [ ] Phase 2-5 完成
- [ ] 综合置信度引擎
- [ ] 资金管理系统

### 长期 (2 个月内)
- [ ] Phase 6-7 完成
- [ ] 回测验证
- [ ] 实盘测试
- [ ] v2.0 正式版发布

---

## 📞 快速参考

### 查看分支
```bash
git branch -a
```

### 查看提交历史
```bash
git log --oneline chanlun-v2
git log --oneline chanlun-origin
```

### 推送分支
```bash
git push origin chanlun-v2
git push origin chanlun-origin
```

### 查看文件差异
```bash
git diff chanlun-origin..chanlun-v2 --stat
```

---

## 💡 使用建议

### 使用 v5.3 (稳定版)
```bash
# 适合：生产环境、实时监控
git checkout chanlun-origin
python monitor_all.py
```

### 使用 v2.0 (开发版)
```bash
# 适合：测试新功能、开发贡献
git checkout chanlun-v2
python scripts/trend_start_detector.py
```

---

## ⚠️ 注意事项

1. **chanlun-origin**: 稳定版本，可用于生产环境
2. **chanlun-v2**: 开发版本，功能可能不稳定
3. **main**: 与远程同步，不要直接在此开发

---

**总结时间**: 2026-04-16 17:15 EDT  
**操作者**: ChanLun AI Agent  
**状态**: ✅ 备份完成，开发分支已创建
