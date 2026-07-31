# bruh
bruh reads selected imessage conversations and identifies plans that have a possibility of coming together, as well as their status and any obstacles to making them happen.

## Requirements

- macos with Messages app (or a sqlite db in the format of apples chat.db)
- Python 3.12+
- Ollama running locally
- Full disk access granted to terminal application running the tool.
    - (this allows the application to read your messages database)

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

Give terminal application full disk access: https://support.apple.com/en-kg/guide/mac-help/mchlccb25729/mac

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

Useful scan options:

```bash
bruh scan --since-hours 24
bruh scan --model qwen3:8b
bruh scan --chat-db /path/to/chat.db
```

## Privacy

Bruh opens `chat.db` in read-only mode and does not modify Messages data.

Conversation analysis runs through your local Ollama model, so no stealing your data. Bruh stores its own plan state locally at:

```text
~/Library/Application Support/Bruh Agent/state.db
```

## Development

```bash
git clone https://github.com/bigbrainbrian7/bruh-agent.git
cd bruh-agent

python3.12 -m venv .venv
.venv/bin/python -m pip install -e .

ollama pull qwen3:1.7b
.venv/bin/bruh scan
```