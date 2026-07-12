# Authentication

wiki-script uses two authentication mechanisms: Wiki.js API keys for the wiki connection and optional API keys for AI providers.

## Wiki.js API Authentication

### How It Works

Wiki.js uses Bearer token authentication. The token is sent with every GraphQL request:

```
Authorization: Bearer your_api_key_here
```

### Setup

Set your API key in the `.env` file:

```env
WIKIJS_URL=https://your-wiki-instance.com/graphql
WIKIJS_API_KEY=your_api_key_here
```

Or pass it directly when using as a library:

```python
from wiki_cli import WikiJSClient

client = WikiJSClient(
    url="https://your-wiki-instance.com/graphql",
    api_key="your_api_key_here",
)
```

### API Key Permissions

When creating an API key in Wiki.js, ensure these permissions are enabled:

| Permission | Required For |
|------------|--------------|
| Pages (read) | Fetching, listing, searching pages |
| Pages (write) | Creating, updating, deleting pages |
| History (read) | Viewing revision history |
| History (write) | Restoring previous versions |

### Finding Your API Key

1. Log in to your Wiki.js instance as an admin
2. Go to **Administration** → **API Access**
3. Click **Create New API Key**
4. Name it (e.g. "wiki-script-cli")
5. Select the permissions listed above
6. Copy the key immediately (it won't be shown again)

## AI Provider Authentication

### How It Works

Each AI provider uses its own API key. wiki-script stores these locally and sends them to the provider's API endpoint.

### Provider-Specific Setup

#### OpenRouter

1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Go to **Keys** → **Create Key**
3. Copy the key (starts with `sk-or-v1-`)
4. Enter it when prompted by `wiki-ai`

#### Groq

1. Sign up at [console.groq.com](https://console.groq.com)
2. Go to **API Keys** → **Create API Key**
3. Copy the key (starts with `gsk_`)
4. Enter it when prompted by `wiki-ai`

#### OpenAI

1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Go to **API Keys** → **Create new secret key**
3. Copy the key (starts with `sk-`)
4. Enter it when prompted by `wiki-ai`

#### Mistral

1. Sign up at [console.mistral.ai](https://console.mistral.ai)
2. Go to **API Keys** → **Create API Key**
3. Copy the key
4. Enter it when prompted by `wiki-ai`

#### Ollama (Local)

No API key needed. Ollama runs locally on your machine.

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2

# Start the server (if not running as a service)
ollama serve
```

wiki-script connects to `http://localhost:11434` by default.

#### Ollama Cloud (Remote)

For remote Ollama instances, you'll need the server URL and optionally an API key.

### Credential Storage

AI API keys are stored at:

```
~/.config/wiki-cli/credentials.json
```

- File permissions: `0600` (owner-only read/write)
- Keys are stored per provider
- Only one key per provider is stored
- Use `/remove-key` in the AI chat to delete a stored key

### Security Notes

- API keys are never logged or printed in full
- The CLI shows only a masked version: `sk-or-v1-xxxxx...•••xxxx`
- Credentials file is only created when you save a key
- No keys are transmitted to any server other than the configured provider
