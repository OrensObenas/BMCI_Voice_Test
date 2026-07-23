import os
import json
import re
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

app = FastAPI()

# Configuration des chemins locaux pour le modèle TinyLlama 1.1B BMCI
adapter_path = r"C:\Users\user\bmci-model-comparator-internship\fine_tuned\bmci_client__tinyllama_1_1b_chat_fr"
base_model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

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

def clean_response(text: str) -> str:
    """Nettoie le texte généré par le modèle local pour corriger les inversions de rôle."""
    # Remplacer les inversions de rôle où l'IA appelle le conseiller "mon client"
    cleaned = re.sub(r"\bmon client\b", "mon conseiller", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bmon cher client\b", "monsieur", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bcher client\b", "monsieur", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bà bientôt, mon client\b", "à bientôt.", cleaned, flags=re.IGNORECASE)
    return cleaned

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
        cleaned_text = clean_response(text)
        
        return {
            "id": "chatcmpl-local",
            "object": "chat.completion",
            "created": 123456789,
            "model": "local-model",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": cleaned_text
                },
                "finish_reason": "stop"
            }]
        }

    # Mode streaming (Server-Sent Events)
    # Pour pouvoir filtrer le texte de manière fiable (regex sur des expressions complètes),
    # nous générons d'abord la réponse complète (très rapide sur Qwen 0.5B: ~150-250ms),
    # nous la nettoyons, puis nous la streamons de manière fluide à LiveKit.
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
    full_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
    cleaned_text = clean_response(full_text)
    
    async def event_generator():
        # Découper par mots pour simuler le streaming de jetons
        words = cleaned_text.split(" ")
        for i, word in enumerate(words):
            token = (" " if i > 0 else "") + word
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
            # 20ms par mot pour une sensation de streaming fluide et naturelle
            await asyncio.sleep(0.02)
            
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
