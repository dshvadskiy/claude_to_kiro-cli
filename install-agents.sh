#!/bin/bash

# Copy specific agents from local .kiro to global .kiro config
# Usage: ./install-agents.sh agent1 agent2 agent3...

set -e

LOCAL_KIRO="./.kiro"
GLOBAL_KIRO="$HOME/.kiro"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <agent1> [agent2] [agent3]..."
    echo "Available local agents:"
    if [ -d "$LOCAL_KIRO/agents" ]; then
        ls -1 "$LOCAL_KIRO/agents" 2>/dev/null || echo "  (none found)"
    else
        echo "  No local .kiro/agents directory found"
    fi
    exit 1
fi

# Create global agents directory if it doesn't exist
if [ ! -d "$GLOBAL_KIRO/agents" ]; then
    mkdir -p "$GLOBAL_KIRO/agents"
fi

# Copy each specified agent
for agent in "$@"; do
    if [ -f "$LOCAL_KIRO/agents/$agent" ]; then
        cp "$LOCAL_KIRO/agents/$agent" "$GLOBAL_KIRO/agents/"
        echo "✓ Copied $agent to global config"
    else
        echo "✗ Agent '$agent' not found in $LOCAL_KIRO/agents/"
    fi
done
