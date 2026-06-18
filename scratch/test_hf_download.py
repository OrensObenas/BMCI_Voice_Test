import time
print("Importing transformers...")
from transformers import AutoTokenizer, AutoModelForMaskedLM

model_id = 'dbmdz/bert-base-french-europeana-cased'
print(f"Loading tokenizer for {model_id}...")
t0 = time.time()
tokenizer = AutoTokenizer.from_pretrained(model_id)
print(f"Tokenizer loaded in {time.time() - t0:.2f}s")

print(f"Loading model for {model_id}...")
t0 = time.time()
model = AutoModelForMaskedLM.from_pretrained(model_id)
print(f"Model loaded in {time.time() - t0:.2f}s")
