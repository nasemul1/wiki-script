# Use Cases

wiki-script is designed for anyone who manages a Wiki.js instance and wants to work faster from the terminal.

## Documentation Teams

**Problem:** Maintaining large documentation sites requires frequent page updates, restructuring, and cross-referencing.

**Solution:** Use the CLI for bulk operations and the AI assistant for natural language edits.

```
> update the title of page 42 to "API Reference v2"
> clone page 15 to docs/api/v2 with title "API Reference v2"
> show me all pages under the "api/" path
```

## DevOps & CI/CD

**Problem:** Documentation needs to be updated as part of deployment pipelines.

**Solution:** Use wiki-script as a Python library in scripts.

```python
from wiki_cli import WikiJSClient, PagesManager, Page

client = WikiJSClient()
pages = PagesManager(client)

# Auto-update changelog
page = pages.get_by_path("changelog")
page.content += "\n\n## v2.1.0\n- Fixed authentication bug"
pages.update(page)
```

## Content Migration

**Problem:** Moving content from another platform or restructuring your wiki.

**Solution:** Export pages to files, edit them, and import back.

```bash
# Export all pages
wiki-cli  # → Option 10: Export Page to File

# Edit files locally
vim docs_introduction.md

# Import back
wiki-cli  # → Option 11: Import Page from File
```

## Quick Edits

**Problem:** Simple changes like fixing a typo or updating a title shouldn't require opening a browser.

**Solution:** Use the AI assistant for one-line commands.

```
wiki-ai

> fix the typo on page 12: "recieve" should be "receive"
> update page 5 description to "Getting started guide for new users"
> mark page 8 as unpublished
```

## Wiki Auditing

**Problem:** You need to understand what's in your wiki and what's changed recently.

**Solution:** Use listing, search, and history features.

```
# See the full tree structure
wiki-cli  # → Option 7: Browse Pages (tree)

# Search for all pages mentioning "deprecated"
wiki-cli  # → Option 6: Search Pages

# Check what changed recently
wiki-cli  # → Option 12: View Page History
```

## Content Review

**Problem:** Reviewing changes before they go live.

**Solution:** Compare revisions with diff and restore if needed.

```
wiki-cli  # → Option 14: Diff Two Revisions
wiki-cli  # → Option 15: Restore Revision (if needed)
```

## Multi-Language Wikis

**Problem:** Managing pages in multiple languages.

**Solution:** Wiki.js supports locales — wiki-script passes them through.

```
wiki-ai

> create a page at docs/intro in French with title "Introduction"
> fetch page docs/intro with locale "fr"
```

## Tag-Based Organization

**Problem:** Keeping pages organized by topic.

**Solution:** Use tags for filtering and organization.

```
wiki-ai

> list all pages tagged "api"
> add tags "deprecated" and "v1" to page 23
> search for "authentication" and filter by tag "security"
```
