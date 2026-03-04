# OpenAI Agents SDK Configurations

This directory contains OpenAI Agents SDK interface definitions that were
previously stored inside each skill's `agents/` folder. They are **not** part
of the Anthropic skill format and are kept here for reference or reuse with
the OpenAI Agents SDK.

Each YAML file is named after the skill it originated from.

## File Format

```yaml
interface:
  display_name: "Human-Readable Skill Name"
  short_description: "One-line description."
  default_prompt: "Default prompt text for the agent."
```

## Usage

These files can be imported into an OpenAI Agents SDK project to expose each
synthetic-data generator as a callable agent tool.
