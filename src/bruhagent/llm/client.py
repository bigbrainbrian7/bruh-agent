from openai import OpenAI

client = OpenAI(
    #default address for ollama server
    base_url="http://localhost:11434/v1",
    #you not stealing anything
    api_key="bruh"
)