#!/usr/bin/env python3
"""
Claude Code to Kiro CLI Agent Converter

Converts agents from wshobson/agents (Claude Code format) to Kiro CLI format.

Usage:
    python claude_to_kiro_converter.py --source /path/to/wshobson-agents --output ~/.kiro/agents
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml


class ClaudeToKiroConverter:
    """Converts Claude Code agents to Kiro CLI format."""
    
    def __init__(self, source_dir: Path, output_dir: Path):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def parse_frontmatter(self, content: str) -> tuple[Optional[Dict], str]:
        """Extract YAML frontmatter from markdown."""
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1))
                body = match.group(2)
                return frontmatter, body
            except yaml.YAMLError:
                return None, content
        return None, content
    
    def extract_tools_from_content(self, content: str) -> List[str]:
        """Extract tool mentions from agent content."""
        tools = set()
        
        # Common tool patterns
        tool_patterns = [
            r'use.*?`(\w+)`.*?tool',
            r'tool.*?`(\w+)`',
            r'@(\w+)',
            r'mcp.*?(\w+)',
        ]
        
        for pattern in tool_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            tools.update(matches)
        
        # Built-in Kiro tools
        builtin_tools = ['read', 'write', 'shell', 'grep', 'list_dir']
        for tool in builtin_tools:
            if tool in content.lower():
                tools.add(tool)
        
        return list(tools)
    
    def infer_allowed_tools(self, agent_type: str, content: str) -> List[str]:
        """Infer which tools should be auto-approved based on agent type."""
        allowed = []
        
        # Safe read-only tools
        safe_tools = ['read', 'list_dir', 'grep', 'introspect']
        
        type_lower = agent_type.lower()
        content_lower = content.lower()
        
        # Type-based permissions
        if 'architect' in type_lower or 'design' in type_lower:
            allowed.extend(safe_tools)
        elif 'review' in type_lower or 'audit' in type_lower:
            allowed.extend(safe_tools)
        elif 'security' in type_lower or 'scanner' in type_lower:
            allowed.extend(safe_tools)
            if 'scan' in content_lower:
                allowed.append('@security-scanner/*')
        elif 'dev' in type_lower or 'engineer' in type_lower:
            allowed.extend(['read', 'write', 'list_dir', 'shell'])
        elif 'devops' in type_lower or 'infrastructure' in type_lower:
            allowed.extend(['read', 'write', 'shell'])
            if 'aws' in content_lower:
                allowed.append('@aws/*')
            if 'kubernetes' in content_lower or 'k8s' in content_lower:
                allowed.append('@kubernetes/*')
        
        return list(set(allowed))
    
    def extract_mcp_servers(self, content: str, frontmatter: Optional[Dict]) -> Dict[str, Any]:
        """Extract MCP server configurations."""
        mcps = {}
        
        # Check frontmatter
        if frontmatter and 'mcpServers' in frontmatter:
            mcps.update(frontmatter['mcpServers'])
        
        # Infer from content
        mcp_keywords = {
            'github': {'command': 'npx', 'args': ['-y', '@modelcontextprotocol/server-github']},
            'gitlab': {'command': 'npx', 'args': ['-y', '@modelcontextprotocol/server-gitlab']},
            'aws': {'command': 'npx', 'args': ['-y', '@aws/mcp-server']},
            'kubernetes': {'command': 'npx', 'args': ['-y', '@kubernetes/mcp-server']},
            'postgres': {'command': 'npx', 'args': ['-y', '@modelcontextprotocol/server-postgres']},
            'slack': {'command': 'npx', 'args': ['-y', '@modelcontextprotocol/server-slack']},
        }
        
        content_lower = content.lower()
        for keyword, config in mcp_keywords.items():
            if keyword in content_lower and keyword not in mcps:
                mcps[keyword] = config
        
        return mcps
    
    def convert_agent(self, agent_path: Path) -> Optional[Dict[str, Any]]:
        """Convert a single Claude Code agent to Kiro format."""
        try:
            content = agent_path.read_text()
            frontmatter, body = self.parse_frontmatter(content)
            
            # Extract name from filename
            agent_name = agent_path.stem
            
            # Build Kiro agent config
            kiro_agent = {
                "name": agent_name,
                "description": "",
                "prompt": body.strip(),
                "tools": ["*"],  # Start with all tools
                "allowedTools": [],
                "mcpServers": {},
                "resources": []
            }
            
            # Extract from frontmatter if available
            if frontmatter:
                kiro_agent["description"] = frontmatter.get('description', '')
                
                # Map Claude Code fields to Kiro
                if 'model' in frontmatter:
                    kiro_agent["model"] = frontmatter['model']
                
                if 'temperature' in frontmatter:
                    kiro_agent["temperature"] = frontmatter['temperature']
                
                if 'tools' in frontmatter:
                    kiro_agent["tools"] = frontmatter['tools']
            
            # If no description in frontmatter, extract from content
            if not kiro_agent["description"]:
                # Try to get first line or paragraph as description
                first_para = body.strip().split('\n\n')[0]
                if len(first_para) < 200:
                    kiro_agent["description"] = first_para.strip('#').strip()
            
            # Extract and configure tools
            mentioned_tools = self.extract_tools_from_content(content)
            if mentioned_tools:
                kiro_agent["tools"].extend([f"@{t}" for t in mentioned_tools])
                kiro_agent["tools"] = list(set(kiro_agent["tools"]))
            
            # Infer allowed tools
            kiro_agent["allowedTools"] = self.infer_allowed_tools(
                agent_name, 
                content
            )
            
            # Extract MCP servers
            kiro_agent["mcpServers"] = self.extract_mcp_servers(content, frontmatter)
            
            return kiro_agent
            
        except Exception as e:
            print(f"Error converting {agent_path}: {e}")
            return None
    
    def find_agent_files(self) -> List[Path]:
        """Find all agent markdown files in the source directory."""
        agent_files = []
        
        # Look for agents in plugins/*/agents/*.md
        plugins_dir = self.source_dir / "plugins"
        if plugins_dir.exists():
            for plugin_dir in plugins_dir.iterdir():
                if plugin_dir.is_dir():
                    agents_dir = plugin_dir / "agents"
                    if agents_dir.exists():
                        agent_files.extend(agents_dir.glob("*.md"))
        
        return agent_files
    
    def convert_all(self, dry_run: bool = False) -> Dict[str, Any]:
        """Convert all agents from source to output directory."""
        stats = {
            'total': 0,
            'converted': 0,
            'failed': 0,
            'agents': []
        }
        
        agent_files = self.find_agent_files()
        stats['total'] = len(agent_files)
        
        print(f"Found {len(agent_files)} agent files")
        
        for agent_path in agent_files:
            print(f"Converting: {agent_path.name}")
            
            kiro_agent = self.convert_agent(agent_path)
            
            if kiro_agent:
                output_path = self.output_dir / f"{kiro_agent['name']}.json"
                
                if not dry_run:
                    with open(output_path, 'w') as f:
                        json.dump(kiro_agent, f, indent=2)
                    print(f"  ✓ Saved to {output_path}")
                else:
                    print(f"  ✓ Would save to {output_path}")
                
                stats['converted'] += 1
                stats['agents'].append(kiro_agent['name'])
            else:
                stats['failed'] += 1
                print(f"  ✗ Failed to convert")
        
        return stats
    
    def create_index(self) -> None:
        """Create an index file listing all converted agents."""
        agent_files = list(self.output_dir.glob("*.json"))
        
        # Sort agent files by name
        agent_files.sort(key=lambda x: x.name)
        
        index_path = self.output_dir / "agents_index.md"
        
        with open(index_path, 'w') as f:
            f.write("# Available Kiro Agents\n\n")
            f.write(f"Total agents: {len(agent_files)}\n\n")
            
            categories = {}
            
            for agent_file in agent_files:
                try:
                    with open(agent_file) as af:
                        agent_data = json.load(af)
                        name = agent_data.get("name", agent_file.stem)
                        desc = agent_data.get("description", "").strip()
                        if desc:
                            # Take first line only
                            desc = desc.split('\n')[0]
                        
                        # Categorize
                        category = "General"
                        name_lower = name.lower()
                        if "architect" in name_lower or "design" in name_lower:
                            category = "Architecture"
                        elif "dev" in name_lower or "engineer" in name_lower:
                            category = "Development"
                        elif "devops" in name_lower or "infra" in name_lower:
                            category = "Infrastructure"
                        elif "security" in name_lower or "audit" in name_lower:
                            category = "Security"
                        elif "review" in name_lower:
                            category = "Quality Assurance"
                            
                        if category not in categories:
                            categories[category] = []
                        categories[category].append((name, desc))
                except Exception:
                    continue
            
            # Write by category
            for category in sorted(categories.keys()):
                f.write(f"## {category}\n\n")
                for name, desc in categories[category]:
                    f.write(f"- **{name}**: {desc}\n")
                f.write("\n")
        
        print(f"\nCreated index at {index_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Claude Code agents to Kiro CLI format"
    )
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Path to wshobson/agents repository"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / ".kiro" / "agents",
        help="Output directory for Kiro agents (default: ~/.kiro/agents)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be converted without writing files"
    )
    parser.add_argument(
        "--create-index",
        action="store_true",
        help="Create an index file of all agents"
    )
    
    args = parser.parse_args()
    
    if not args.source.exists():
        print(f"Error: Source directory {args.source} does not exist")
        print("\nTo clone wshobson/agents:")
        print("  git clone https://github.com/wshobson/agents.git")
        return 1
    
    converter = ClaudeToKiroConverter(args.source, args.output)
    
    print(f"Converting agents from {args.source}")
    print(f"Output directory: {args.output}")
    print(f"Dry run: {args.dry_run}\n")
    
    stats = converter.convert_all(dry_run=args.dry_run)
    
    print(f"\n{'='*60}")
    print(f"Conversion complete!")
    print(f"Total agents found: {stats['total']}")
    print(f"Successfully converted: {stats['converted']}")
    print(f"Failed: {stats['failed']}")
    
    if args.create_index and not args.dry_run:
        print(f"\nCreating index...")
        converter.create_index()
    
    if stats['converted'] > 0:
        print(f"\n{'='*60}")
        print("Next steps:")
        print(f"1. Review the converted agents in {args.output}")
        print("2. Test an agent: kiro-cli chat --agent <agent-name>")
        print("3. List all agents: kiro-cli agent list")
        print("4. Customize agents as needed by editing the JSON files")
    
    return 0


if __name__ == "__main__":
    exit(main())
