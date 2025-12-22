#!/usr/bin/env python3
"""Validate all agents are loaded correctly by scanning the agents directory."""

import json
import sys
import argparse
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List

def check_kiro_installed() -> bool:
    """Check if kiro-cli is installed and available."""
    return shutil.which("kiro-cli") is not None

def validate_agent_file(file_path: Path, use_kiro_cli: bool = False) -> List[str]:
    """Validate a single agent file. Returns list of error messages."""
    errors = []
    
    # 1. Static JSON validation
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except Exception as e:
        return [f"Could not read file: {e}"]

    # Basic required fields check
    required_fields = ['name', 'prompt']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")
            
    if 'name' in data and not isinstance(data['name'], str):
        errors.append("Field 'name' must be a string")
        
    if 'prompt' in data and not isinstance(data['prompt'], str):
        errors.append("Field 'prompt' must be a string")

    allowed_fields = {
        '$schema', 'name', 'description', 'prompt', 'mcpServers', 'tools', 
        'toolAliases', 'allowedTools', 'resources', 'hooks', 'toolsSettings', 
        'includeMcpJson', 'useLegacyMcpJson', 'model', 'temperature'
    }
    
    unknown_fields = set(data.keys()) - allowed_fields
    if unknown_fields:
        errors.append(f"Unknown fields found: {', '.join(unknown_fields)}")

    # 2. Dynamic Kiro CLI validation (if enabled)
    if use_kiro_cli and not errors:
        try:
            result = subprocess.run(
                ["kiro-cli", "agent", "validate", "--path", str(file_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # Clean up error message
                err_msg = result.stderr.strip() or result.stdout.strip()
                errors.append(f"Kiro CLI validation failed: {err_msg}")
                
        except Exception as e:
            errors.append(f"Failed to run kiro-cli: {e}")

    return errors

def main():
    parser = argparse.ArgumentParser(description="Validate Kiro CLI agent definitions.")
    parser.add_argument(
        "--agents-dir", 
        type=Path, 
        default=Path(".kiro/agents"),
        help="Directory containing agent JSON files"
    )
    parser.add_argument(
        "--no-cli", 
        action="store_true",
        help="Skip kiro-cli validation (static check only)"
    )
    args = parser.parse_args()
    
    agents_dir = args.agents_dir.expanduser()
    
    if not agents_dir.exists():
        print(f"❌ Agents directory not found: {agents_dir}")
        sys.exit(1)
        
    kiro_installed = check_kiro_installed()
    use_cli = kiro_installed and not args.no_cli
    
    if args.no_cli:
        print("ℹ️  Skipping kiro-cli validation (--no-cli specified)")
    elif not kiro_installed:
        print("⚠️  kiro-cli not found in PATH. Skipping CLI validation.")
    else:
        print("✓ kiro-cli found. Performing full validation.")
        
    print(f"\nValidating agents in: {agents_dir}\n")
    
    json_files = sorted(list(agents_dir.glob("*.json")))
    
    if not json_files:
        print("❌ No .json files found in agents directory.")
        sys.exit(1)
        
    valid_count = 0
    invalid_count = 0
    
    for file_path in json_files:
        if file_path.name == "INDEX.json":
            continue
            
        errors = validate_agent_file(file_path, use_kiro_cli=use_cli)
        
        if not errors:
            print(f"✓ {file_path.name}")
            valid_count += 1
        else:
            print(f"✗ {file_path.name}")
            for err in errors:
                # Indent error messages
                print(f"    - {err}")
            invalid_count += 1
            
    print(f"\n{'='*50}")
    print(f"Total Scanned: {len(json_files)}")
    print(f"Valid: {valid_count}")
    print(f"Invalid: {invalid_count}")
    
    if invalid_count > 0:
        print("\n❌ Validation failed for some agents.")
        sys.exit(1)
    else:
        print("\n✨ All agents valid!")
        sys.exit(0)

if __name__ == "__main__":
    main()
