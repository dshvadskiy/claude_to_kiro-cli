# Anthropic Skills to Kiro Powers Converter

Converts Anthropic Skills format to Kiro Powers format with automatic keyword extraction and directory restructuring.

## Features

- ✅ Converts `SKILL.md` to `POWER.md` format
- ✅ Extracts keywords from descriptions and content
- ✅ Moves additional files to `steering/` directory
- ✅ Handles YAML frontmatter conversion
- ✅ No external dependencies (uses built-in Python)
- ✅ Dry-run mode for preview

## Usage

```bash
# Preview conversion
python3 skills_to_kiro_powers_converter.py --source ./skills --dry-run

# Convert skills to powers
python3 skills_to_kiro_powers_converter.py --source ./skills --output ./powers

# Help
python3 skills_to_kiro_powers_converter.py --help
```

## Conversion Process

### Input (Anthropic Skill)
```
my-skill/
├── SKILL.md          # Required
├── examples.md       # Optional
└── reference.md      # Optional
```

**SKILL.md format:**
```yaml
---
name: "React Component Generator"
description: "Generate React components with TypeScript and best practices"
---

# Instructions here...
```

### Output (Kiro Power)
```
power-react-component-generator/
├── POWER.md          # Converted main file
└── steering/         # Additional files moved here
    ├── examples.md
    └── reference.md
```

**POWER.md format:**
```yaml
---
name: "react-component-generator"
displayName: "React Component Generator"
description: "Generate React components with TypeScript and best practices"
keywords:
  - "react"
  - "typescript"
  - "components"
  - "generate"
---

# Instructions here...
```

## Key Transformations

1. **File Rename**: `SKILL.md` → `POWER.md`
2. **Frontmatter Enhancement**:
   - Adds `displayName` field
   - Generates `keywords` array from content
   - Normalizes `name` to kebab-case
3. **Directory Structure**: Additional files → `steering/` directory
4. **Keyword Extraction**: Automatic tech keyword detection

## Example

```bash
# Test with the included example
python3 skills_to_kiro_powers_converter.py --source . --output ./converted-powers

# Result: test-skill → power-react-component-generator
```

## Requirements

- Python 3.6+
- No external dependencies required
