#!/usr/bin/env python3
"""
Convert Anthropic Skills to Kiro Powers format
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Simple YAML parser for frontmatter (avoiding external dependencies)
def parse_yaml_frontmatter(yaml_str: str) -> Dict:
    """Simple YAML parser for basic frontmatter"""
    result = {}
    for line in yaml_str.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"\'')
            result[key] = value
    return result

def dump_yaml(data: Dict) -> str:
    """Simple YAML dumper"""
    lines = []
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - \"{item}\"")
        else:
            lines.append(f"{key}: \"{value}\"")
    return '\n'.join(lines)

def extract_keywords(description: str, skill_name: str, skill_path: str = "") -> List[str]:
    """Extract specific keywords from skill name and path structure"""
    keywords = []
    
    # Extract from skill name (most specific)
    name_parts = re.split(r'[-_\s]+', skill_name.lower())
    keywords.extend([part for part in name_parts if len(part) > 2])
    
    # Extract from path segments (plugin category)
    if skill_path:
        path_parts = skill_path.split('/')
        for part in path_parts:
            if 'plugins' in part or 'skills' in part or 'wshobson-agents' in part:
                continue
            # Split hyphens and underscores into separate keywords
            sub_parts = re.split(r'[-_\s]+', part)
            for sub_part in sub_parts:
                if sub_part and len(sub_part) > 2:
                    keywords.append(sub_part)
    
    # Extract specific technologies from name/description
    tech_terms = []
    combined = f"{skill_name} {description}".lower()
    
    # Direct technology matches
    direct_matches = re.findall(r'\b(stripe|paypal|pci|gdpr|fastapi|nextjs|react|vue|angular|typescript|javascript|python|rust|go|java|aws|azure|gcp|docker|kubernetes|terraform|helm|istio|linkerd|prometheus|grafana|postgres|mysql|mongodb|redis|graphql|rest|grpc|oauth|jwt|webpack|tailwind|jest|cypress|playwright|gitlab|github|unity|godot|solidity|ethereum)\b', combined)
    tech_terms.extend(direct_matches)
    
    # Combine all, prioritize skill name parts
    all_keywords = name_parts[:2] + tech_terms + keywords
    
    # Remove duplicates, keep order
    unique = []
    for kw in all_keywords:
        if kw not in unique and len(kw) > 2:
            unique.append(kw)
    
    return unique[:4]

def parse_skill_md(file_path: Path) -> Dict:
    """Parse SKILL.md file and extract frontmatter and content"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split frontmatter and body
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parse_yaml_frontmatter(parts[1])
            body = parts[2].strip()
        else:
            frontmatter = {}
            body = content
    else:
        frontmatter = {}
        body = content
    
    return {
        'frontmatter': frontmatter,
        'body': body,
        'full_content': content
    }

def convert_skill_to_power(skill_dir: Path, output_dir: Path, dry_run: bool = False) -> bool:
    """Convert a single skill directory to power format"""
    skill_md = skill_dir / 'SKILL.md'
    
    if not skill_md.exists():
        print(f"❌ No SKILL.md found in {skill_dir}")
        return False
    
    try:
        parsed = parse_skill_md(skill_md)
        frontmatter = parsed['frontmatter']
        body = parsed['body']
        
        # Extract required fields
        name = frontmatter.get('name', skill_dir.name)
        description = frontmatter.get('description', '')
        
        if not description:
            print(f"⚠️  No description found in {skill_md}")
            description = f"Converted from {name} skill"
        
        # Generate keywords from description, skill name, and path
        keywords = extract_keywords(description, name, str(skill_dir))
        
        # Create power frontmatter
        power_frontmatter = {
            'name': name.lower().replace(' ', '-'),
            'displayName': name,
            'description': description,
            'keywords': keywords
        }
        
        # Create POWER.md content
        power_content = f"---\n{dump_yaml(power_frontmatter)}\n---\n\n{body}"
        
        # Determine output directory
        power_name = name.lower().replace(' ', '-').replace('_', '-')
        power_dir = output_dir / f"power-{power_name}"
        
        if dry_run:
            print(f"📋 Would create: {power_dir}/POWER.md")
            print(f"   Source: {skill_dir.absolute()}")
            print(f"   Keywords: {keywords}")
            return True
        
        # Create output directory
        power_dir.mkdir(parents=True, exist_ok=True)
        
        # Write POWER.md
        power_md = power_dir / 'POWER.md'
        with open(power_md, 'w', encoding='utf-8') as f:
            f.write(power_content)
        
        # Handle additional files
        additional_files = []
        for file_path in skill_dir.iterdir():
            if file_path.name != 'SKILL.md' and file_path.is_file():
                additional_files.append(file_path)
        
        if additional_files:
            steering_dir = power_dir / 'steering'
            steering_dir.mkdir(exist_ok=True)
            
            for file_path in additional_files:
                dest_path = steering_dir / file_path.name
                with open(file_path, 'r', encoding='utf-8') as src:
                    with open(dest_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
        
        print(f"✅ Converted: {skill_dir.name} → {power_dir.name}")
        print(f"   Source: {skill_dir.absolute()}")
        if additional_files:
            print(f"   📁 Moved {len(additional_files)} files to steering/")
        
        return True
        
    except Exception as e:
        print(f"❌ Error converting {skill_dir}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Convert Anthropic Skills to Kiro Powers')
    parser.add_argument('--source', '-s', type=Path, required=True,
                       help='Source directory containing skill folders')
    parser.add_argument('--output', '-o', type=Path, default=Path('./powers'),
                       help='Output directory for powers (default: ./powers)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview conversion without creating files')
    
    args = parser.parse_args()
    
    if not args.source.exists():
        print(f"❌ Source directory does not exist: {args.source}")
        return 1
    
    # Find all skill directories recursively
    skill_dirs = []
    for skill_md in args.source.rglob('SKILL.md'):
        skill_dirs.append(skill_md.parent)
    
    if not skill_dirs:
        print(f"❌ No skill directories found in {args.source}")
        return 1
    
    print(f"🔍 Found {len(skill_dirs)} skills to convert")
    
    if not args.dry_run:
        args.output.mkdir(parents=True, exist_ok=True)
    
    # Convert each skill
    success_count = 0
    for skill_dir in skill_dirs:
        if convert_skill_to_power(skill_dir, args.output, args.dry_run):
            success_count += 1
    
    print(f"\n✨ Converted {success_count}/{len(skill_dirs)} skills successfully")
    
    if not args.dry_run:
        print(f"📁 Powers saved to: {args.output}")
    
    return 0

if __name__ == '__main__':
    exit(main())
