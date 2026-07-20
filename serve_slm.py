import os
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from peft import PeftModel
from threading import Thread

app = FastAPI()

# Configuration des chemins locaux pour le modèle Qwen BMCI
adapter_path = r"C:\Users\user\bmci-model-comparator-internship\Qwen model fine tune 1\fine_tuned\bmci_client__qwen2_5_0_5b_fr\final"
base_model_name = "Qwen/Qwen2.5-0.5B-Instruct"

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Chargement du modèle sur le périphérique : {device}...")

# Charger le tokenizer et le modèle
tokenizer = AutoTokenizer.from_pretrained(adapter_path, trust_remote_code=True)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    torch_dtype=torch.float32 if device == "cpu" else torch.float16,
    trust_remote_code=True
)
model = PeftModel.from_pretrained(base_model, adapter_path)
model = model.to(device)
model.eval()

print("Modèle chargé avec succès. Prêt à recevoir des requêtes.")

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    temperature = body.get("temperature", 0.7)
    stream = body.get("stream", False)
    
    # Appliquer le chat template du modèle
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    
    if not stream:
        # Mode hors-streaming
        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=256,
                do_sample=True,
                temperature=temperature,
                pad_token_id=tokenizer.pad_token_id
            )
        generated_ids = outputs[0][inputs.input_ids.shape[1]:]
        text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        return {
            "id": "chatcmpl-local",
            "object": "chat.completion",
            "created": 123456789,
            "model": "local-model",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": text
                },
                "finish_reason": "stop"
            }]
        }

    # Mode streaming (Server-Sent Events)
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    generation_kwargs = dict(
        input_ids=inputs.input_ids,
        attention_mask=inputs.attention_mask,
        max_new_tokens=256,
        do_sample=True,
        temperature=temperature,
        streamer=streamer,
        pad_token_id=tokenizer.pad_token_id
    )
    
    # Exécuter dans un thread séparé pour ne pas bloquer l'event loop asynchrone
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()
    
    async def event_generator():
        for token in streamer:
            if not token:
                continue
            chunk = {
                "id": "chatcmpl-local",
                "object": "chat.completion.chunk",
                "created": 123456789,
                "model": "local-model",
                "choices": [{
                    "index": 0,
                    "delta": {
                        "content": token
                    },
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.01)
            
        # Signal de fin
        final_chunk = {
            "id": "chatcmpl-local",
            "object": "chat.completion.chunk",
            "created": 123456789,
            "model": "local-model",
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
