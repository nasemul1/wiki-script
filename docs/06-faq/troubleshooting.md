# Troubleshooting

Common issues and their solutions.

## Connection Issues

### "Error initializing client: WIKIJS_URL not set"

**Cause:** The `.env` file is missing or doesn't contain `WIKIJS_URL`.

**Solution:**

```bash
# Check if .env exists
cat .env

# Create it if missing
cp .env.example .env

# Edit with your values
vim .env
```

Ensure the URL ends with `/graphql`:

```env
WIKIJS_URL=https://wiki.example.com/graphql
```

### "Error initializing client: WIKIJS_API_KEY not set"

**Cause:** The `.env` file doesn't contain `WIKIJS_API_KEY`.

**Solution:**

1. Go to your Wiki.js admin → API Access
2. Create a new API key with Pages and History permissions
3. Add it to `.env`:

```env
WIKIJS_API_KEY=your_key_here
```

### "Connection refused" or "SSL error"

**Cause:** The Wiki.js instance is not reachable or has SSL issues.

**Solutions:**

```bash
# Test connectivity
curl -I https://wiki.example.com/graphql

# If using self-signed cert, set SSL_CERT_FILE
export SSL_CERT_FILE=/path/to/cert.pem

# If behind a proxy
export HTTPS_PROXY=http://proxy:8080
```

### "Page update failed: undefined passed as a property"

**Cause:** A field with `None` value was sent to the GraphQL API.

**Solution:** This is usually fixed in the codebase. Update to the latest version:

```bash
git pull
pip install -e .
```

## AI Assistant Issues

### "No module named 'openai'"

**Cause:** AI dependencies not installed.

**Solution:**

```bash
pip install -e ".[ai]"
```

### "API key not valid" or 401 error

**Cause:** The stored API key is incorrect or expired.

**Solution:**

```
/remove-key
```

Then restart and enter a new key:

```bash
wiki-ai
```

### "Model not found"

**Cause:** The selected model is not available at your provider.

**Solution:**

```
/models
```

Pick a different model, or check available models at your provider's website.

### Ollama: "Connection refused"

**Cause:** Ollama server is not running.

**Solution:**

```bash
# Start Ollama
ollama serve

# Or if installed as a service
sudo systemctl start ollama

# Verify it's running
curl http://localhost:11434/api/tags
```

### AI seems to forget context

**Cause:** Conversation history was cleared or the session restarted.

**Solution:** The AI maintains history within a session. Use `/clear` only when you want to start fresh. If you need persistent history across sessions, that's a feature request.

## CLI Menu Issues

### "Invalid option. Try again."

**Cause:** You entered a number not in the menu (0-17).

**Solution:** Enter a number between 0 and 17.

### "Invalid ID"

**Cause:** You entered a non-numeric page ID.

**Solution:** Enter only numbers for page IDs.

### Page not found

**Cause:** The page ID doesn't exist in the wiki.

**Solution:**

```
wiki-cli → Option 5  # List all pages to find the correct ID
```

Or use the AI assistant:

```
> search for "page title"
```

### "No pages found"

**Cause:** The wiki is empty or the search returned no results.

**Solution:**

1. Create some pages first (Option 1)
2. Or import from files (Option 11)

## Import/Export Issues

### "File not found" on import

**Cause:** The file path is incorrect.

**Solution:**

```bash
# Use absolute path
wiki-cli → Option 11
Filename: /home/user/my-page.md

# Or relative to current directory
wiki-cli → Option 11
Filename: my-page.md
```

### Frontmatter not parsed correctly

**Cause:** The frontmatter format is not recognized.

**Solution:** Ensure your frontmatter uses this exact format:

```yaml
---
title: Page Title
path: docs/page-path
description: A description
tags: [tag1, tag2]
---

# Page Content
```

- Must start with `---`
- Must end with `---`
- Tags must be in `[tag1, tag2]` format
- Each field must be `key: value` on its own line

### Export creates empty file

**Cause:** The page has no content.

**Solution:** This is expected behavior. The frontmatter is still exported. Add content to the page first.

## Performance Issues

### Slow list/search operations

**Cause:** The wiki has many pages.

**Solution:**

- Use search (Option 6) instead of listing all pages
- Use tag filtering to narrow results
- Use the AI assistant which summarizes results

### Slow AI responses

**Cause:** The LLM provider is slow or the model is large.

**Solution:**

- Use a faster model (Groq is fastest)
- Use a smaller model (e.g. `llama-3.1-8b-instant`)
- Check your internet connection
- Try a different provider

## Testing Issues

### Tests fail with import errors

**Cause:** Dev dependencies not installed.

**Solution:**

```bash
pip install -e ".[dev]"
```

### Tests fail with connection errors

**Cause:** Tests should not require a network connection.

**Solution:** Ensure you're running tests from the project root:

```bash
pytest tests/ -v
```

If tests try to connect, check that mocks are properly applied.

## Getting Help

If you encounter an issue not listed here:

1. Check the [GitHub Issues](https://github.com/Imranslab/wiki-script/issues)
2. Run with verbose output:

```bash
python -m wiki_cli 2>&1 | tee debug.log
```

3. Test the connection:

```bash
wiki-cli → Option 16
```

4. Check the AI status:

```bash
wiki-ai → /help
```
