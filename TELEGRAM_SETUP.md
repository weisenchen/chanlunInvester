# Telegram 告警配置指南

## 🚀 快速配置 (3 分钟完成)

### 第一步：创建 Telegram Bot

1. **打开 Telegram**，搜索并联系 **@BotFather**

2. **发送命令:** `/newbot`

3. **按提示输入:**
   - Bot 名称：`UVIX Monitor Bot` (可自定义)
   - Bot 用户名：`uvix_monitor_bot` (必须以 bot 结尾，且唯一)

4. **保存 Bot Token:**
   ```
   BotFather 会返回:
   Use this token to access the HTTP API:
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

   ⚠️ 复制并保存这个 Token！
   ```

---

### 第二步：获取你的 Chat ID

**方法 1: 使用 @userinfobot**

1. 在 Telegram 搜索 **@userinfobot**
2. 发送 `/start`
3. 它会回复你的 ID，例如：`123456789`

**方法 2: 使用 @getmyid_bot**

1. 在 Telegram 搜索 **@getmyid_bot**
2. 发送任意消息
3. 它会显示你的 ID

**方法 3: 手动查看**

1. 在浏览器打开：`https://web.telegram.org/`
2. 登录后，查看 URL:
   ```
   https://web.telegram.org/#/im?p=@YourUsername&123456789
   最后一串数字就是你的 ID
   ```

---

### 第三步：配置环境变量

编辑 `~/.bashrc`:

```bash
nano ~/.bashrc
```

添加以下内容 (替换为你的 Token 和 ID):

```bash
# UVIX Telegram 告警配置
export TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="123456789"
```

保存后执行:

```bash
source ~/.bashrc
```

---

### 第四步：测试告警

```bash
cd /home/wei/.openclaw/workspace/trading-system

# 发送测试消息
python3 -c "
import sys
sys.path.insert(0, 'python-layer')
from examples.uvix_monitor import send_alert
send_alert('【UVIX 测试消息】\\n\\nTelegram 告警配置成功！✅', ['telegram'])
"
```

**如果收到 Telegram 消息，说明配置成功！** 🎉

---

## 🔧 故障排查

### 问题 1: 收不到消息

**检查 Token 和 ID:**

```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

**测试 Bot API:**

```bash
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/sendMessage" \
  -d "chat_id=YOUR_CHAT_ID&text=Test"
```

### 问题 2: Bot 未启动

联系 @BotFather，发送 `/start` 启动你的 Bot。

### 问题 3: 权限问题

确保你的 Bot 有发送消息的权限：
- 如果在群聊中使用，需要将 Bot 添加为管理员
- 私聊无需额外权限

---

## 📊 验证配置

运行完整测试:

```bash
cd /home/wei/.openclaw/workspace/trading-system
python3 examples/uvix_monitor.py
```

如果出现买卖点，你会收到 Telegram 告警！

---

## 🎯 告警格式示例

当 UVIX 出现买卖点时，你会收到:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ UVIX 缠论买卖点提醒
📅 时间：2026-03-03 15:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【UVIX 缠论买卖点信号 - 5m 级别】

📊 标的：UVIX
⏰ 级别：5m
🎯 类型：第二类买点
💰 价格：$6.85
📈 置信度：85%
📝 说明：次级别回踩确认

操作建议：BUY
入场：$6.85
止损：$6.51 (-5%)
目标：$7.54 (+10%)

⚠️ 风险提示：缠论分析仅供参考，不构成投资建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

**配置完成后，买卖点出现时会立即收到 Telegram 通知！** 🚨
