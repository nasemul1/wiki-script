# AI Prompts Guide

The AI assistant understands natural language. Here are examples of what you can ask.

## Page Operations

### Creating Pages

```
> create a page at docs/introduction with title "Introduction" and content "# Introduction\n\nWelcome to our docs"
```

```
> create a new page at api/auth about authentication tokens in the REST API
```

```
> make a draft page at drafts/ideas for project ideas, don't publish it yet
```

### Reading Pages

```
> show me page 5
```

```
> fetch the page at docs/getting-started
```

```
> what's on page 42?
```

### Updating Pages

```
> update page 3 title to "API Reference v2"
```

```
> change the content of page 7 to "# Updated Content\n\nThis page has been revised."
```

```
> add tags "deprecated" and "v1" to page 12
```

```
> mark page 9 as unpublished
```

### Deleting Pages

```
> delete page 15
```

The AI will ask for confirmation before deleting.

### Listing and Searching

```
> list all pages
```

```
> show me pages sorted by path
```

```
> search for "authentication"
```

```
> find pages about API tokens
```

```
> list all pages tagged "docs"
```

### Browsing

```
> show me the page tree
```

```
> what's the structure of the wiki?
```

### Organizing

```
> move page 8 to docs/api/v2
```

```
> rename page 5 to "Getting Started Guide"
```

```
> clone page 3 to docs/api/backup with title "API Backup"
```

### Import and Export

```
> export page 12 to backup.md
```

```
> import the file my-page.md into the wiki
```

## History Operations

### Viewing History

```
> show me the history of page 5
```

```
> what revisions exist for page 3?
```

### Viewing Revisions

```
> show me version 10 of page 5
```

```
> what did page 3 look like 2 weeks ago?
```

### Comparing Revisions

```
> diff version 1 and version 5 of page 3
```

```
> what changed between revision 10 and 15 of page 7?
```

### Restoring Revisions

```
> restore page 5 to version 3
```

The AI will ask for confirmation before restoring.

## System

```
> test the connection
```

```
> are we connected to the wiki?
```

## Multi-Turn Conversations

The AI remembers context:

```
> create a page at docs/api with title "API Docs"
✓ page created (id=42)

> now add a section about authentication
✓ page updated

> show me the history
✓ 2 revisions

> diff the first two revisions
✓ diff computed

> revert to the first version
✓ version restored
```

## AI Slash Commands

| Command | Description |
|---------|-------------|
| `/edit` | Open your text editor for multi-line input |
| `/clear` | Clear conversation history (start fresh) |
| `/providers` | Switch AI provider |
| `/models` | Switch AI model |
| `/remove-key` | Remove saved API key |
| `/help` | Show available commands |
| `exit` | Quit |

## Tips for Better Prompts

1. **Be specific** — "create a page at docs/intro with title Introduction" is better than "make a page"
2. **Include paths** — Always specify the full path for new pages
3. **Mention content** — The AI generates better content when given context
4. **Use natural language** — "show me what changed" works as well as "diff revisions"
5. **Ask for confirmation** — Destructive operations (delete, restore) always ask first
6. **Chain operations** — The AI remembers previous actions in the conversation
