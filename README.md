# bruh
bruh reads selected imessage conversations and identifies plans that have a possibility of coming together, as well as their status and any obstacles to making them happen.

## Choose a model

Bruh can use either provider:

- **Ollama (local):** Install [Ollama](https://ollama.com/) and pull a model,
  such as `ollama pull qwen3:8b`. Messages stay on your Mac.
- **Gemini (cloud):** Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey).
  Gemini sends analyzed conversation content to Google's API and does not
  require a local model download.

## Use the macOS app

The macOS app is the easiest way to use Bruh. It includes the Python backend,
so Python and the CLI do not need to be installed separately.

1. Download `BruhAgent.dmg` from the [latest GitHub Release](https://github.com/bigbrainbrian7/bruh-agent/releases/latest).
2. Open the DMG and drag **Bruh Agent** to Applications.
3. Open Bruh Agent. On first launch, follow the in-app instructions to grant
   it **Full Disk Access** so it can read your local Messages database.
4. In the **Chats** tab, select chats to track. In the **Plans** tab, choose a
   model and scan your tracked chats.

Choose Ollama or Gemini in the **Plans** tab. For Gemini, paste the API key you
created above; the app stores it in macOS Keychain.

(Cloud models tend to work **SIGNIFICANTLY** better than local ones)

## Use the command-line tool

### Requirements

- macOS with the Messages app, or a SQLite database compatible with Apple's `chat.db`
- Python 3.12+
- Either Ollama with a downloaded model, or a Gemini API key

### Install

```bash
brew install pipx
pipx ensurepath
pipx install "git+https://github.com/bigbrainbrian7/bruh-agent.git@v0.2.0"
```

Install an Ollama model:

```bash
ollama pull qwen3:8b
```

### Grant Full Disk Access

Bruh reads the Messages database in read-only mode, which macOS protects with
Full Disk Access.

- Grant Full Disk Access to the terminal app running `bruh`.

See [Apple's instructions](https://support.apple.com/en-kg/guide/mac-help/mchlccb25729/mac).

### Usage

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
`gemini-3.5-flash-lite`, which is available on Gemini's free tier. Export the
API key you created above in the terminal where you run Bruh, then scan:

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

The macOS app stores a Gemini API key in macOS Keychain. The CLI instead reads
`GEMINI_API_KEY` from the terminal environment.

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
development and release-build instructions are in that folder's README.
