# Quick Reference: Using Converted Agents

## Installation & Setup

```bash
# One-command setup (recommended)
./setup.sh

# Manual setup
pip install pyyaml
git clone https://github.com/wshobson/agents.git
python claude_to_kiro_converter.py --source ./agents --create-index
```

---

## Agent Management

### List All Agents
```bash
# All agents
kiro-cli agent list

# With details
kiro-cli agent list --format json-pretty
```

### View Agent Details
```bash
# View JSON config
cat ~/.kiro/agents/python-pro.json | jq

# Validate agent
kiro-cli agent validate -p ~/.kiro/agents/python-pro.json
```

### Edit an Agent
```bash
# Interactive editor
kiro-cli agent edit python-pro

# Or edit directly
vim ~/.kiro/agents/python-pro.json
```

### Set Default Agent
```bash
kiro-cli agent set-default python-pro
```

---

## Using Agents

### Interactive Chat
```bash
# Start chat with specific agent
kiro-cli chat --agent python-pro

# Start with default agent
kiro-cli chat
```

### One-Shot Commands
```bash
# Single question
kiro-cli chat --agent python-pro "Show me async/await examples"

# Non-interactive mode (auto-approve tools)
kiro-cli chat --agent devops-troubleshooter \
    --no-interactive \
    --trust-all-tools \
    "Deploy a Lambda function"
```

### Resume Previous Session
```bash
# Resume last session
kiro-cli chat --resume

# Pick from saved sessions
kiro-cli chat --resume-picker

# List all sessions
kiro-cli chat --list-sessions
```

---

## Agent Categories (from agents_index.md)

```bash
# View all categories and agents
cat ~/.kiro/agents/agents_index.md

# Search for agents by keyword
grep -i "python" ~/.kiro/agents/agents_index.md
```

---

## Common Agents & Use Cases

### Development
```bash
# Python development
kiro-cli chat --agent python-pro

# JavaScript/TypeScript
kiro-cli chat --agent javascript-pro

# Backend APIs
kiro-cli chat --agent backend-architect
```

### Infrastructure
```bash
# AWS infrastructure
kiro-cli chat --agent cloud-architect

# Kubernetes
kiro-cli chat --agent kubernetes-architect

# Terraform
kiro-cli chat --agent terraform-specialist
```

### Security
```bash
# Security scanning
kiro-cli chat --agent threat-modeling-expert

# Code review
kiro-cli chat --agent security-auditor
```

### Quality
```bash
# Code review
kiro-cli chat --agent code-reviewer

# Testing
kiro-cli chat --agent test-automator
```

---

## Customizing Agents

### Add MCP Server
```bash
# Edit agent
vim ~/.kiro/agents/python-pro.json

# Add to mcpServers section
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

### Modify Tool Permissions
```bash
# Edit allowedTools for auto-approval
{
  "allowedTools": [
    "read",
    "write",
    "shell",
    "@github/*"
  ]
}

# Add tool restrictions
{
  "toolsSettings": {
    "shell": {
      "allowedCommands": ["git status", "git diff"],
      "deniedCommands": ["rm -rf", "sudo.*"]
    }
  }
}
```

### Add Hooks
```bash
# Auto-format Python after writing
{
  "hooks": {
    "postToolUse": [
      {
        "matcher": "write",
        "command": "if [[ $FILE == *.py ]]; then black $FILE; fi"
      }
    ]
  }
}
```

---

## Troubleshooting

### Agent Not Found
```bash
# Check agent exists
ls ~/.kiro/agents/*.json | grep agent-name

# List all available agents
kiro-cli agent list
```

### Agent Fails to Load
```bash
# Validate JSON syntax
jq . ~/.kiro/agents/agent-name.json

# Check Kiro validation
kiro-cli agent validate -p ~/.kiro/agents/agent-name.json
```

### MCP Server Issues
```bash
# List configured MCP servers
kiro-cli mcp list

# Test MCP server
kiro-cli mcp status server-name

# Add MCP server
kiro-cli mcp add github npx -y @modelcontextprotocol/server-github
```

### Tool Permission Denied
```bash
# Check allowedTools in agent config
cat ~/.kiro/agents/agent-name.json | jq '.allowedTools'

# Add tool to allowedTools or approve during chat
```

---

## Advanced Usage

### Multiple Agents in Sequence
```bash
# Use architect for design, then dev for implementation
kiro-cli chat --agent architect-review "Design a REST API"
kiro-cli chat --agent backend-architect "Implement the design from previous chat"
```

### Agent Chaining with Scripts
```bash
#!/bin/bash
# design-and-build.sh

# 1. Architect designs
kiro-cli chat --agent architect-review \
    --no-interactive \
    "Design microservice architecture for e-commerce" \
    > design.md

# 2. Developer implements
kiro-cli chat --agent backend-architect \
    --no-interactive \
    "Implement the architecture in design.md"

# 3. Security reviews
kiro-cli chat --agent security-auditor \
    --no-interactive \
    "Review the implementation for security issues"
```

### Batch Processing
```bash
# Process multiple files
for file in src/**/*.py; do
    kiro-cli chat --agent code-reviewer \
        --no-interactive \
        "Review $file for code quality" \
        >> review-report.md
done
```

---

## Sharing Agents with Team

### Project-Specific Agents
```bash
# Create in project directory
mkdir -p .kiro/agents
cp ~/.kiro/agents/python-pro.json .kiro/agents/

# Customize for project
vim .kiro/agents/python-pro.json

# Commit to repo
git add .kiro/agents/
git commit -m "Add project-specific agents"
```

### Global Team Agents
```bash
# Export agents
tar -czf kiro-agents.tar.gz -C ~/.kiro/agents .

# Share via GitHub/network drive
# Team members extract to their ~/.kiro/agents
```

---

## Tips & Best Practices

### 1. Start with Read-Only Agents
When testing, start with agents that only have `read`, `list_dir`, `grep` permissions.

### 2. Use Dry-Run for Dangerous Operations
```bash
kiro-cli chat --agent devops-troubleshooter --dry-run "Deploy to production"
```

### 3. Review Auto-Approved Tools
Check `allowedTools` before using agents for critical tasks.

### 4. Customize Prompts for Your Workflow
Edit agent prompts to match your team's coding standards.

### 5. Use Hooks for Consistency
Add post-write hooks for automatic formatting/linting.

### 6. Keep Index Updated
Regenerate after adding/removing agents:
```bash
python claude_to_kiro_converter.py \
    --source ./agents \
    --create-index
```

---

## Keyboard Shortcuts (in chat)

```
Ctrl+C        Cancel current operation
Ctrl+D        Exit chat
/help         Show available commands
/model        Select different model
/save <file>  Save conversation
/load <file>  Load conversation
```

---

## Resources

- [Kiro CLI Docs](https://kiro.dev/docs/cli/)
- [Custom Agents Guide](https://kiro.dev/docs/cli/custom-agents/)
- [MCP Documentation](https://kiro.dev/docs/cli/mcp/)
- [wshobson/agents](https://github.com/wshobson/agents) (original)
- [Kiro Discord](https://discord.gg/kiro) (share configs)

---

## Quick Wins

```bash
# 1. List all agents nicely
cat ~/.kiro/agents/agents_index.md

# 2. Test random agents
ls ~/.kiro/agents/*.json | head -5 | xargs -n1 basename -s .json | while read agent; do
    echo "Testing: $agent"
    kiro-cli chat --agent "$agent" "Hello, introduce yourself"
done

# 3. Find agents by keyword
grep -l "kubernetes" ~/.kiro/agents/*.json | xargs -n1 basename -s .json

# 4. Count total agents
ls ~/.kiro/agents/*.json | wc -l
```

---

Happy coding! 🚀
