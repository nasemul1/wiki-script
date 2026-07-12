# Custom System Prompts

The AI assistant's behavior is controlled by a system prompt. You can modify it to change how the AI responds.

## Default System Prompt

The default prompt is in `wiki_cli/ai/agent.py`:

```python
SYSTEM_PROMPT = """You are a Wiki.js assistant. You manage wiki pages using the tools provided.

Rules:
- Always confirm with the user before performing destructive actions (delete, restore, move).
- When creating or updating pages, generate high-quality Markdown content when the user provides a topic.
- If a tool returns an error, explain it to the user and suggest fixes.
- For searches or lists, summarize results in a readable format instead of dumping raw data.
- Never fabricate page IDs or paths. Always fetch first if unsure.
"""
```

## Customizing the Prompt

### Option 1: Edit the Source

Modify `SYSTEM_PROMPT` in `wiki_cli/ai/agent.py`:

```python
SYSTEM_PROMPT = """You are a documentation assistant for our internal wiki.

Additional rules:
- Always use formal tone in page content.
- Include a "Last Updated" section at the bottom of new pages.
- Default to Markdown format.
- Suggest related pages when creating new content.
- When creating pages, add relevant tags automatically.
"""
```

### Option 2: Override at Runtime

Create a wrapper script:

```python
#!/usr/bin/env python3
"""Custom wiki-ai with modified system prompt."""

from wiki_cli.ai.agent import WikiAgent, SYSTEM_PROMPT
from wiki_cli.ai.cli import ai_mode

# Override the system prompt
import wiki_cli.ai.agent as agent_module

agent_module.SYSTEM_PROMPT = """You are a senior documentation writer.

Rules:
- Write in a professional, clear tone.
- Use headings, bullet points, and code blocks.
- Always include examples when creating content.
- Suggest improvements to existing content.
- Flag outdated information.
"""

# Now run the normal AI mode
ai_mode()
```

Save as `my-wiki-ai.py` and run:

```bash
python my-wiki-ai.py
```

### Option 3: Environment-Based Prompts

```python
import os

SYSTEM_PROMPT = os.environ.get("WIKI_AI_PROMPT", """You are a Wiki.js assistant.""")
```

Then:

```bash
WIKI_AI_PROMPT="You are a technical writer. Always use Markdown." wiki-ai
```

## Prompt Engineering Tips

### For Content Generation

```python
SYSTEM_PROMPT = """You are a technical documentation writer.

When creating pages:
- Use clear, concise language
- Include code examples where relevant
- Structure content with headings (H1 → H2 → H3)
- Add a "Prerequisites" section for tutorials
- Include a "Related Pages" section when applicable
- Write for an audience of software developers
"""
```

### For Bulk Operations

```python
SYSTEM_PROMPT = """You are a wiki maintenance assistant.

When listing or searching:
- Always show page IDs
- Group results by directory
- Highlight unpublished or draft pages
- Suggest cleanup actions (unused tags, empty pages)
"""
```

### For Security-Conscious Environments

```python
SYSTEM_PROMPT = """You are a wiki assistant for a security-sensitive organization.

Additional rules:
- NEVER create pages with sensitive information (passwords, tokens, keys)
- Always flag pages that might contain sensitive data
- Confirm ALL operations (not just destructive ones)
- Log all operations to the user before executing
- Prefer read-only operations when possible
"""
```

## Adding Custom Behavior

You can extend the agent with custom tool handlers:

```python
from wiki_cli.ai.agent import WikiAgent

class CustomAgent(WikiAgent):
    def _tool_create_page(self, args):
        # Add custom logic before creation
        args["tags"] = list(set(args.get("tags", []) + ["auto-generated"]))
        return super()._tool_create_page(args)
```

## Testing Custom Prompts

Test your custom prompt without connecting to an LLM:

```python
from wiki_cli.ai.agent import WikiAgent, SYSTEM_PROMPT

print("Current system prompt:")
print(SYSTEM_PROMPT)

# Test the agent initialization
agent = WikiAgent()
print(f"\nAgent messages: {len(agent.messages)}")
print(f"First message role: {agent.messages[0]['role']}")
```
