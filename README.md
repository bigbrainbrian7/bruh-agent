# bruh
bruh reads selected imessage conversations and identifies plans that have a possibility of coming together, as well as their status and any obstacles to making them happen.

## Requirements

- macos with Messages app (or a sqlite db in the format of apples chat.db)
- Python 3.12+
- Ollama and a downloaded model. Otherwise, an API key for a cloud model (Only gemini is supported as of now)

## Installation

```bash
brew install pipx
pipx ensurepath
pipx install "git+https://github.com/bigbrainbrian7/bruh-agent.git@v0.1.1"
```

Install an Ollama model

```bash
ollama pull qwen3:1.7b
```

### Full Disk Access

Bruh reads the Messages database in read-only mode, which macOS protects with
Full Disk Access.

- When using the CLI, grant Full Disk Access to the terminal app running `bruh`.
- When using the built macOS app, grant Full Disk Access to `Bruh Agent.app`
  itself. During Xcode development, this is the debug build under Derived Data.

See [Apple's instructions](https://support.apple.com/en-kg/guide/mac-help/mchlccb25729/mac).

## Usage

List recently active chats:

```bash
bruh chats list
bruh chats list --limit 20
```
Add a chat to analyze:

```bash
bruh chats add "iMessage;-;+15555555555"
```

View tracked chats:

```bash
bruh chats tracked
```

Remove a tracked chat:

```bash
bruh chats rm "iMessage;-;+15555555555"
```

Scan tracked chats:

```bash
bruh scan
```

### Model providers

Ollama is the default local provider:

```bash
bruh scan --provider ollama --model qwen3:1.7b
```

Gemini is an optional cloud provider. It defaults to
`gemini-3.5-flash-lite`, which is available on Gemini's free tier. To set it up, create an API key in [Google AI Studio](https://aistudio.google.com/apikey), export it in the terminal where you run Bruh, then scan:

```bash
export GEMINI_API_KEY="..."
bruh scan --provider gemini
```

Pass `--model <model-name>` to choose another supported Gemini model.  
Gemini does not require downloading a local model, but its free tier does have rate limits.

Useful scan options:

```bash
bruh scan --since-hours 24
bruh scan --chat-db /path/to/chat.db
```

## Privacy

Bruh opens `chat.db` in read-only mode and does not modify Messages data.

Ollama analysis stays local and offline. Gemini sends the selected conversation
content to Google's API. Bruh sets `store=False`, so it does not use Gemini's
server-side interaction history. Review Google's free-tier data-use policy
before using it with private conversations.

Bruh stores its own plan state locally at:

```text
~/Library/Application Support/Bruh Agent/state.db
```

## Development

```bash
git clone https://github.com/bigbrainbrian7/bruh-agent.git
cd bruh-agent

python3.12 -m venv .venv
.venv/bin/python -m pip install -e .

# If you want to use a local model
ollama pull qwen3:1.7b
.venv/bin/bruh scan

# Or use Gemini without downloading a local model
export GEMINI_API_KEY="<API_KEY>"
.venv/bin/bruh scan --provider gemini
```

The native macOS app is in [`macos/BruhAgent`](macos/BruhAgent/). Its
development and backend-bundling notes are in that folder's README.
