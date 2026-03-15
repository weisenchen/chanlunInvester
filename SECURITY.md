# 🔒 Security Guidelines

## ⚠️ CRITICAL: Files That Must NEVER Be Pushed to GitHub

This is a **public repository**. The following files contain sensitive information and must **NEVER** be committed or pushed:

### 🚫 Never Push These Files

#### Identity & Memory (OpenClaw)
- ❌ `MEMORY.md` - Long-term memory (personal context)
- ❌ `SOUL.md` - Behavioral guidelines (AI persona)
- ❌ `USER.md` - User information
- ❌ `AGENTS.md` - Agent configuration
- ❌ `IDENTITY.md` - AI identity
- ❌ `HEARTBEAT.md` - Task management
- ❌ `TOOLS.md` - Tool configurations
- ❌ `BOOTSTRAP.md` - Bootstrap configuration

#### Memory Directory
- ❌ `memory/` - All daily memory files
- ❌ `*.memory.md` - Any memory files

#### Logs & Analysis
- ❌ `logs/` - May contain sensitive operational data
- ❌ `*.log` - Log files
- ❌ `examples/uvix_analysis_result.json` - Real-time analysis results

#### Credentials & Secrets
- ❌ `config/*.local.yaml` - Local configuration
- ❌ `config/*.private.yaml` - Private configuration
- ❌ `config/secrets.yaml` - Secret credentials
- ❌ `*.env` - Environment variables
- ❌ `.env` - Environment file
- ❌ `TELEGRAM_*.md` - Telegram configuration
- ❌ Any file containing tokens, passwords, or API keys

#### Personal Notes
- ❌ `*.private.md` - Private notes
- ❌ `*.personal.md` - Personal notes
- ❌ `notes/` - Personal notes directory

#### Internal Documentation
- ❌ `GAP_ANALYSIS*.md` - Internal analysis reports
- ❌ `GITHUB_PUSH*.md` - Internal push instructions
- ❌ `PUSH_*.md` - Internal scripts

---

## ✅ Safe to Push

These files are **safe** for public repository:

### Code
- ✅ Python scripts (`.py`)
- ✅ Rust code (`.rs`)
- ✅ Shell scripts (`.sh`)
- ✅ Configuration templates (`.yaml` without secrets)

### Public Documentation
- ✅ `README.md` - Project overview
- ✅ `ARCHITECTURE.md` - System design
- ✅ `DEVELOPMENT_PLAN.md` - Development roadmap
- ✅ `QUICK_REFERENCE.md` - Quick reference guide
- ✅ `GANTT_CHART.md` - Timeline
- ✅ `SECURITY.md` - This file
- ✅ Feature documentation (`*_FEATURE.md`)

### Examples
- ✅ `examples/` - Code examples (no credentials)
- ✅ Sample data (non-sensitive)

### Tests
- ✅ `tests/` - Test files
- ✅ Test data (non-sensitive)

---

## 🔐 Security Checklist Before Pushing

Before pushing to GitHub, verify:

```bash
# 1. Check .gitignore is in place
ls -la .gitignore

# 2. Check for sensitive files
git status --short | grep -E "(MEMORY|SOUL|USER|AGENT|IDENTITY|memory/|logs/)"

# 3. Review what will be pushed
git status

# 4. Dry run push (check what would be pushed)
git push --dry-run origin main
```

**Expected output:** No sensitive files should appear in the list.

---

## 🛡️ .gitignore Rules

The `.gitignore` file automatically excludes:

```
# OpenClaw Identity & Memory
MEMORY.md
SOUL.md
USER.md
AGENTS.md
IDENTITY.md
HEARTBEAT.md
TOOLS.md
memory/

# Logs
logs/
*.log

# Credentials
*.env
config/*.local.yaml
config/*.private.yaml

# Personal files
*.private.md
*.personal.md
```

---

## 🚨 If You Accidentally Push Sensitive Data

1. **Immediately delete the commit:**
   ```bash
   git reset --hard HEAD~1
   git push --force origin main
   ```

2. **Rotate any exposed credentials** (tokens, passwords, API keys)

3. **Add the files to .gitignore**

4. **Contact repository admin** if data was exposed

---

## 📋 Best Practices

1. **Always check `git status`** before committing
2. **Review diffs** with `git diff --cached`
3. **Use `.gitignore`** for all sensitive patterns
4. **Never commit credentials** - use environment variables
5. **Separate config from code** - templates only, no secrets
6. **Regular audits** - periodically check for sensitive files

---

## 🔍 Audit Command

Run this to check for sensitive files:

```bash
# Check for sensitive files in git
git ls-files | grep -iE "(memory|soul|user|agent|identity|heartbeat|tools|secret|password|token|\.env)"

# Should return: (empty)
```

---

**Remember:** This is a PUBLIC repository. When in doubt, don't push it! 🔒
