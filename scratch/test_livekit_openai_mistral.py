import os
import asyncio
from dotenv import load_dotenv
from livekit.plugins import openai as lk_openai
from livekit.agents import llm

load_dotenv()

async def main():
    api_key = os.getenv("MISTRAL_API_KEY")
    ai_llm = lk_openai.LLM(
        model="mistral-small-latest",
        base_url="https://api.mistral.ai/v1",
        api_key=api_key
    )
    
    ctx = llm.ChatContext()
    ctx.add_message(role="system", content="Tu es un conseiller bancaire poli.")
    ctx.add_message(role="user", content="Bonjour, je voudrais fermer mon compte.")
    
    stream = ai_llm.chat(chat_ctx=ctx)
    print("Streaming response:")
    async for chunk in stream:
        delta = chunk.delta.content
        if delta:
            print(delta, end="", flush=True)
    print("\nDone.")

if __name__ == "__main__":
    asyncio.run(main())
