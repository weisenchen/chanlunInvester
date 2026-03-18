#!/bin/bash
# Phase 1 测试脚本

echo "======================================================================="
echo "UVIX Phase 1 三级联动监控系统 - 测试"
echo "======================================================================="
echo ""

cd "$(dirname "$0")/.."

echo "[1/3] 运行 Phase 1 分析..."
python3 scripts/uvix_phase1_monitor.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Phase 1 分析成功"
else
    echo ""
    echo "❌ Phase 1 分析失败"
    exit 1
fi

echo ""
echo "[2/3] 检查分析结果..."
if [ -f "logs/phase1_analysis.json" ]; then
    echo "✅ 分析结果已保存"
    echo ""
    echo "最新信号:"
    cat logs/phase1_analysis.json | python3 -m json.tool
else
    echo "❌ 分析结果未找到"
    exit 1
fi

echo ""
echo "[3/3] 测试完成"
echo ""
echo "======================================================================="
echo "✅ Phase 1 测试通过"
echo "======================================================================="
