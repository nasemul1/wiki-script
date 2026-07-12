# Best Practices

Guidelines for using wiki-script effectively and safely.

## Configuration

### Use Environment Variables for CI/CD

```bash
WIKIJS_URL=https://wiki.example.com/graphql \
WIKIJS_API_KEY=$WIKIJS_API_KEY \
wiki-cli
```

### Secure Your API Keys

- Never commit `.env` files to version control
- Use `0600` permissions on credential files (wiki-script does this automatically)
- Use separate API keys for different environments (dev, staging, prod)
- Rotate keys periodically

### Use the `.env` File Locally

```bash
# .env (not committed)
WIKIJS_URL=https://dev-wiki.internal/graphql
WIKIJS_API_KEY=dev_key_here
```

## Page Management

### Path Conventions

```
✅ docs/getting-started
✅ guides/installation
✅ api/v2/authentication

❌ Docs/GettingStarted
❌ guides/installation_guide
❌ api/v2/authentication/
```

- Use lowercase
- Use hyphens, not underscores or camelCase
- No trailing slashes
- Keep it concise but descriptive

### Use Descriptive Titles

```
✅ "API Authentication Guide"
✅ "Getting Started with Wiki.js"

❌ "Page 1"
❌ "Auth"
❌ "New Document"
```

### Organize with Tags

```python
# Good: consistent tag taxonomy
tags = ["api", "v2", "authentication"]

# Bad: random tags
tags = ["important", "fixme", "john", "monday"]
```

Suggested tag categories:
- **Type:** `api`, `guide`, `reference`, `tutorial`
- **Status:** `draft`, `review`, `deprecated`
- **Topic:** `security`, `authentication`, `deployment`

### Use Descriptions

Descriptions help with SEO and search:

```python
page = Page(
    path="docs/api/auth",
    title="API Authentication",
    description="How to authenticate API requests using bearer tokens",
    ...
)
```

## AI Assistant

### Be Specific in Prompts

```
✅ "create a page at docs/api/authentication about bearer tokens with code examples"
✅ "update page 5 title to 'API Reference v2'"
✅ "show me all pages tagged 'api'"

❌ "make a page"
❌ "fix page 5"
❌ "list stuff"
```

### Confirm Destructive Operations

The AI always asks before deleting or restoring. Always verify:

```
> delete page 15
Are you sure you want to delete page 15? (yes/no): yes
```

### Use `/clear` When Switching Contexts

```
> /clear
history cleared

> now let's work on the API docs
```

### Use `/edit` for Long Content

```
> /edit
# (opens your editor)
# Write your content here
# Save and close

> (content is sent to the AI)
```

## Version Control

### Export Before Major Changes

```bash
wiki-cli → Option 10  # Export the page
# Make changes
# If something goes wrong, re-import the backup
```

### Use History for Auditing

```
wiki-cli → Option 12  # View history
wiki-cli → Option 14  # Diff revisions
```

### Tag Drafts

```python
page.tags = ["draft", "wip"]
page.isPublished = False
```

## Performance

### Limit List Operations

For large wikis, use search instead of listing everything:

```
> search for "authentication" instead of listing all 500 pages
```

### Use Pagination

When listing pages, use the built-in pagination (20 items per page):

```
wiki-cli → Option 5
# Shows 20 pages, press Enter for next page, 'q' to quit
```

## Security

### Never Hardcode Credentials

```python
# ❌ Bad
client = WikiJSClient(url="...", api_key="sk-...")

# ✅ Good — reads from environment
client = WikiJSClient()
```

### Restrict API Key Permissions

Only grant the permissions wiki-script needs:
- Pages: read + write
- History: read + write

### Use Private Pages for Sensitive Content

```python
page = Page(
    path="internal/security-notes",
    title="Security Notes",
    isPrivate=True,  # Only visible to authenticated users
    ...
)
```

## Testing

### Run Tests Before Deploying

```bash
pytest tests/ -v
```

### Run Specific Tests

```bash
pytest tests/test_create_page.py -v
pytest tests/test_search_pages.py -v
```

### Check Coverage

```bash
pytest tests/ --cov=wiki_cli --cov-report=term-missing
```
