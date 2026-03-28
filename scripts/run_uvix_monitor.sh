#!/bin/bash
# UVIX 监控包装脚本 - 设置正确的环境变量

export PATH=/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:$PATH
export PYTHONPATH=/home/wei/.openclaw/workspace/trading-system/python-layer:$PYTHONPATH

cd /home/wei/.openclaw/workspace/trading-system
python3 scripts/chanlun_monitor.py UVIX >> logs/uvix_cron.log 2>&1
