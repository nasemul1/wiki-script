# Configuration

wiki-script uses environment variables for Wiki.js connection settings and stores AI provider credentials locally.

## Wiki.js Configuration

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

```env
WIKIJS_URL=https://your-wiki-instance.com/graphql
WIKIJS_API_KEY=your_api_key_here
```

### Configuration Fields

| Variable | Required | Description |
|----------|----------|-------------|
| `WIKIJS_URL` | Yes | Full URL to the Wiki.js GraphQL endpoint |
| `WIKIJS_API_KEY` | Yes | API key from Wiki.js admin settings |

### Finding Your GraphQL URL

1. Open your Wiki.js instance in a browser
2. Go to **Administration** → **GraphQL API**
3. The endpoint URL is shown at the top (typically `https://your-domain.com/graphql`)

### Generating an API Key

1. Open your Wiki.js instance in a browser
2. Go to **Administration** → **API Access**
3. Click **Create New API Key**
4. Give it a name (e.g. "wiki-script")
5. Set the appropriate permissions (at minimum: Pages read/write, History read)
6. Copy the generated key

## AI Provider Configuration

AI provider credentials are stored in:

```
~/.config/wiki-cli/credentials.json
```

This file is created automatically when you first select an AI provider. File permissions are set to `0600` (owner-only read/write).

### Stored Data

```json
{
  "openrouter": "sk-or-v1-...",
  "groq": "gsk_...",
  "openai": "sk-..."
}
```

### Managing Stored Keys

From the AI chat interface:

```
/remove-key    # Remove the saved key for the current provider
/providers     # Switch provider (re-prompts for key if needed)
```

Or manually:

```bash
# View
cat ~/.config/wiki-cli/credentials.json

# Remove all keys
rm ~/.config/wiki-cli/credentials.json
```

## Last Used Configuration

The AI assistant remembers your last provider and model selection:

```
~/.config/wiki-cli/last_config.json
```

```json
{
  "provider": "openrouter",
  "model": "meta-llama/llama-4-scout:free"
}
```

On next launch, it skips provider/model selection and goes straight to chat.

## Environment Variable Priority

Settings are resolved in this order:

1. Function arguments (for library usage)
2. Environment variables (`WIKIJS_URL`, `WIKIJS_API_KEY`)
3. `.env` file in the project root

```bash
# Override with environment variables
export WIKIJS_URL=https://other-wiki.com/graphql
wiki-cli
```
