# bruh
looks at your messages and scans for plans that have a possibility of coming together. more features coming soon

## usage

must have ollama server running with your choice of model. 

must have full disk access for terminal app running bruh

brew install pipx
pipx ensurepath
pipx install "git+https://github.com/bigbrainbrian7/bruh-agent.git@v0.1.0"


DO: `bruh scan `
will look at all your new messages in last 12 hours

flags: 
--since-hours
--model
--chat-db
--state-db

this is probably safe, no data acquistion, works offline, uses local model.
opens up imessages database in read only :D
makes local state db under Application Support directory

## development installation

setup venv 
install python package requirements 
install ollama 
start server on brew
pull qwen3:8b
give vscode(or wherever you're running python files from) full disk access (for sqlite connection into chat.db) if you need to test on own database (make a copy preferrably however)