# Self-Improving Agent Installation Guide

## Options Found

I found two main self-improving agent projects:

### 1. EvoAgentX (Recommended for most users)
**Repository:** https://github.com/EvoAgentX/EvoAgentX  
**Stars:** 1000+  
**Location:** `/home/wei/.openclaw/workspace/EvoAgentX`

**Features:**
- 🧱 Agent Workflow Autoconstruction
- 🔍 Built-in Evaluation
- 🔁 Self-Evolution Engine
- 🧩 Plug-and-Play Compatibility (OpenAI, Claude, Qwen, etc.)
- 🧰 Comprehensive Built-in Tools
- 🧠 Memory Module
- 🧑‍💻 Human-in-the-Loop Support

**Installation:**
```bash
cd /home/wei/.openclaw/workspace/EvoAgentX

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install (note: has complex dependencies, may need Python 3.11)
pip install -e .

# Or simple install
pip install evoagentx
```

**Note:** This package has complex ML dependencies (torch, faiss, etc.) that may require Python 3.11 for best compatibility.

---

### 2. Self-Improving Coding Agent (SICA)
**Repository:** https://github.com/MaximeRobeyns/self_improving_coding_agent  
**Location:** `/home/wei/.openclaw/workspace/self_improving_coding_agent`

**Features:**
- A coding agent that works on its own codebase
- Iterative improvement loop
- Docker-based isolation for safety
- Web-based visualization UI
- Published at ICLR 2025 Workshop

**Installation:**
```bash
cd /home/wei/.openclaw/workspace/self_improving_coding_agent

# Export API keys
export ANTHROPIC_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here

# Build Docker image
make image
# Or for Apple Silicon:
make image-mac

# Install local requirements
python3 -m venv venv
source venv/bin/activate
pip install -r base_agent/requirements.txt
pip install swebench

# Run interactively
make int

# Then in the container:
python -m agent_code.agent --server true -p "Your initial prompt"

# Open browser: http://localhost:8080
```

**Note:** This agent runs in Docker for safety since it can execute shell commands.

---

## Quick Start (EvoAgentX - Simple Mode)

```bash
cd /home/wei/.openclaw/workspace/EvoAgentX

# Create and activate venv
python3 -m venv venv
source venv/bin/activate

# Set API key
export OPENAI_API_KEY=your_key_here

# Install basic package
pip install evoagentx

# Create a simple test script
cat > test_agent.py << 'EOF'
from evoagentx.models import OpenAILLMConfig, OpenAILLM
import os

# Initialize LLM
config = OpenAILLMConfig(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
llm = OpenAILLM(config)

# Test
response = llm.generate("Hello, who are you?")
print(response)
EOF

python test_agent.py
```

---

## Next Steps

1. **Choose which agent** you want to use
2. **Set up API keys** (OpenAI, Anthropic, etc.)
3. **Install dependencies** based on the chosen project
4. **Run the agent** following the project's documentation

---

## Files Created

- `EvoAgentX/` - Full EvoAgentX framework (needs Python 3.11 for full install)
- `self_improving_coding_agent/` - SICA framework (Docker-based)
- `SELF_IMPROVING_AGENT_SETUP.md` - This guide

---

**Recommendation:** Start with EvoAgentX for a more polished experience, or use SICA if you want a coding-focused self-improving agent that can modify its own codebase.
