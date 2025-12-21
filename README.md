# Claude Code to Kiro CLI Agent Converter

Converts agents from [wshobson/agents](https://github.com/wshobson/agents) (Claude Code format) to Kiro CLI format.

## Features

- ✅ Converts 99 Claude Code agents to Kiro CLI JSON format
- ✅ Parses YAML frontmatter and markdown content
- ✅ Infers tool permissions based on agent type
- ✅ Extracts and configures MCP servers
- ✅ Creates categorized index of all agents
- ✅ Dry-run mode to preview changes

## Prerequisites

```bash
# Install required Python packages
pip install pyyaml

# Clone the wshobson/agents repository
git clone https://github.com/wshobson/agents.git
```

## Quick Start

```bash
# Convert all agents (dry run first to preview)
python claude_to_kiro_converter.py \
    --source ./agents \
    --output ~/.kiro/agents \
    --dry-run

# Actually convert and create index
python claude_to_kiro_converter.py \
    --source ./agents \
    --output ~/.kiro/agents \
    --create-index
```

## Usage

### Basic Conversion

```bash
python claude_to_kiro_converter.py --source /path/to/wshobson-agents
```

This will:
1. Find all agent `.md` files in `plugins/*/agents/`
2. Convert them to Kiro JSON format
3. Save to `~/.kiro/agents/` (default output)

### Custom Output Directory

```bash
# Save to project-specific directory
python claude_to_kiro_converter.py \
    --source ./agents \
    --output ./.kiro/agents
```

### Dry Run (Preview Only)

```bash
# See what would be converted without writing files
python claude_to_kiro_converter.py \
    --source ./agents \
    --dry-run
```

### Create Index File

```bash
# Generate agents_index.md with categorized agent list
python claude_to_kiro_converter.py \
    --source ./agents \
    --create-index
```

## What Gets Converted

### From Claude Code Format

```markdown
---
description: Python development expert
model: claude-sonnet-4
temperature: 0.7
---

You are a Python development specialist...
```

### To Kiro CLI Format

```json
{
  "name": "python-pro",
  "description": "Python development expert",
  "model": "claude-sonnet-4",
  "temperature": 0.7,
  "prompt": "You are a Python development specialist...",
  "tools": ["*", "@python-linter", "@pytest"],
  "allowedTools": ["read", "write", "list_dir", "shell"],
  "mcpServers": {
    "python": {
      "command": "npx",
      "args": ["-y", "@python/mcp-server"]
    }
  },
  "resources": []
}
```

## Conversion Logic

### Tool Permissions

The converter automatically infers safe permissions based on agent type:

| Agent Type | Auto-Approved Tools |
|------------|---------------------|
| `architect`, `design` | `read`, `list_dir`, `grep`, `introspect` |
| `review`, `audit` | `read`, `list_dir`, `grep` |
| `security`, `scanner` | `read`, `list_dir`, `@security-scanner/*` |
| `dev`, `engineer` | `read`, `write`, `list_dir`, `shell` |
| `devops`, `infrastructure` | `read`, `write`, `shell`, `@aws/*`, `@kubernetes/*` |

### MCP Server Detection

Automatically adds MCP servers based on content keywords:

- **github** → `@modelcontextprotocol/server-github`
- **aws** → `@aws/mcp-server`
- **kubernetes** → `@kubernetes/mcp-server`
- **postgres** → `@modelcontextprotocol/server-postgres`
- **slack** → `@modelcontextprotocol/server-slack`

### Categories

Agents are automatically categorized:

- **architecture**: architects, designers
- **development**: developers, engineers
- **infrastructure**: devops, cloud specialists
- **security**: security scanners, auditors
- **quality**: code reviewers
- **general**: everything else

## Using Converted Agents

### List Available Agents

```bash
kiro-cli agent list
```

### Use a Specific Agent

```bash
# Start chat with Python expert
kiro-cli chat --agent python-pro

# One-off command
kiro-cli chat --agent cloud-architect "Deploy a Lambda function"
```

### Customize an Agent

Edit the JSON file:

```bash
# Open in editor
vim ~/.kiro/agents/python-pro.json

# Or use Kiro's built-in editor
kiro-cli agent edit python-pro
```

### Set Default Agent

```bash
kiro-cli agent set-default python-pro
```

## Output Structure

```
~/.kiro/agents/
├── agents_index.md                    # Categorized agent index
├── python-pro.json
├── javascript-pro.json
├── kubernetes-architect.json
├── security-auditor.json
└── ... (99 total agents)
```

### agents_index.md Structure

```markdown
# Available Kiro Agents

Total agents: 99

## Development
- **python-pro**: Python development expert
- **javascript-pro**: Modern JavaScript developer
...

## Infrastructure
- **kubernetes-architect**: Expert Kubernetes architect
...
```

## Important Considerations

### ⚠️ Manual Review Required

The converter does its best, but you should **review and test** each agent:

1. **Tool Permissions**: Some agents may need more/fewer permissions
2. **MCP Servers**: Verify MCP server configs are correct
3. **Prompts**: Agent prompts may need adjustment for Kiro's behavior
4. **Models**: Check if specified models are available in Kiro

### MCP Server Installation

If agents reference MCP servers, you need to install them:

```bash
# Example: Install GitHub MCP server
npx -y @modelcontextprotocol/server-github

# Configure in Kiro
kiro-cli mcp add github npx -y @modelcontextprotocol/server-github
```

### Agent Naming Conflicts

If you already have agents in `~/.kiro/agents/`, the converter will **overwrite** them. Consider:

```bash
# Backup existing agents first
cp -r ~/.kiro/agents ~/.kiro/agents.backup

# Or use a different output directory
python claude_to_kiro_converter.py \
    --source ./agents \
    --output ./converted-agents
```

## Troubleshooting

### "Source directory does not exist"

```bash
# Make sure you've cloned wshobson/agents
git clone https://github.com/wshobson/agents.git
cd agents
```

### "No agent files found"

Check that the source directory has the expected structure:

```
agents/
└── plugins/
    ├── python-development/
    │   └── agents/
    │       └── python-pro.md
    └── ...
```

### Agent doesn't work in Kiro

1. **Check model availability**: `kiro-cli` → `/model`
2. **Verify MCP servers**: `kiro-cli mcp list`
3. **Test with minimal config**: Remove all but essential fields
4. **Check logs**: Look for errors when starting the agent

### YAML parsing errors

Some agents may have malformed frontmatter. The script will skip them and report:

```
Error converting python-pro.md: YAML parsing error
```

Manually fix the frontmatter and re-run.

## Example Workflow

```bash
# 1. Clone repositories
git clone https://github.com/wshobson/agents.git
git clone <this-converter-repo>

# 2. Preview conversion
python claude_to_kiro_converter.py \
    --source ./agents \
    --dry-run

# 3. Convert with index
python claude_to_kiro_converter.py \
    --source ./agents \
    --create-index

# 4. Review Index
cat ~/.kiro/agents/agents_index.md

# 5. Test a few agents
kiro-cli chat --agent python-pro "Help me with async/await"
kiro-cli chat --agent cloud-architect "Create an S3 bucket"

# 6. Customize as needed
kiro-cli agent edit python-pro
```

## Advanced: Batch Testing

Test all converted agents:

```bash
#!/bin/bash
# test-all-agents.sh

for agent in ~/.kiro/agents/*.json; do
    agent_name=$(basename "$agent" .json)
    echo "Testing $agent_name..."
    kiro-cli chat --agent "$agent_name" "Hello, introduce yourself" --no-interactive
done
```

## Contributing

Found an issue with the conversion? Improvements to suggest?

1. The converter is a starting point - it won't be perfect for all agents
2. Some agent-specific logic may need manual adjustment
3. MCP server configurations may vary
4. Tool permissions should be reviewed for security

Consider this a **80% solution** that saves you manual work, not a 100% automated conversion.

## License

MIT - Use freely, modify as needed.

## Related Projects

- [wshobson/agents](https://github.com/wshobson/agents) - Original Claude Code agent collection
- [Kiro CLI Documentation](https://kiro.dev/docs/cli/)
- [Kiro Custom Agents Guide](https://kiro.dev/docs/cli/custom-agents/)
