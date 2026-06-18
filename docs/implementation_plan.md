# Transition vers des modèles locaux (Whisper & Kokoro) pour l'agent vocal LiveKit

Ce plan décrit les modifications pour adapter l'agent vocal LiveKit afin qu'il fonctionne avec des modèles 100% locaux pour l'écoute (STT) et la parole (TTS). Nous utiliserons :
1. **ASR / STT local** : `faster-whisper` avec le modèle `large-v3-turbo`.
2. **TTS local** : `Kokoro v0.19` avec la voix française `ff_siwis`.
3. **LLM** : Google Gemini (qui reste distant, via la clé API validée de l'utilisateur).

---

## User Review Required

> [!IMPORTANT]
> Pour que le TTS Kokoro fonctionne correctement sous Windows, l'exécutable `eSpeak NG` doit être installé sur le système. Nous avons vérifié sa présence dans `C:\Program Files\eSpeak NG`. Nous injecterons ce chemin au démarrage de l'agent.

---

## Open Questions

Il n'y a pas de questions ouvertes pour le moment. La faisabilité a été validée via des tests d'importation et de chargement des modèles en local.

---

## Proposed Changes

### Configuration et Exécution de l'Agent Vocal

#### [MODIFY] [agent.py](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/agent.py)

Nous allons implémenter deux classes adaptatrices directement dans `agent.py` :
1. `LocalWhisperSTT` : Hérite de `livekit.agents.stt.STT` et utilise `faster-whisper` en forçant la langue française, avec rééchantillonnage automatique à 16 kHz si l'audio entrant est dans une autre fréquence.
2. `LocalKokoroTTS` : Hérite de `livekit.agents.tts.TTS` et utilise le pipeline `kokoro` en français avec la voix `ff_siwis`.

Nous mettrons ensuite à jour la fonction `entrypoint` pour instancier ces modules locaux. Le STT local sera encapsulé dans un `StreamAdapter` de LiveKit avec le Silero VAD local pour gérer le découpage de la parole.

Voici le squelette du code qui sera injecté dans `agent.py` :
```python
import os
import logging
import asyncio
import numpy as np
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli, llm, inference, AgentSession, Agent, TurnHandlingOptions, stt, tts
from livekit.plugins import google
from faster_whisper import WhisperModel
from kokoro import KPipeline

# (Configuration du PATH pour espeak-ng)
# (Définition de LocalWhisperSTT)
# (Définition de LocalKokoroTTS et KokoroChunkedStream)
# (Mise à jour de entrypoint pour brancher ces plugins locaux)
```

---

## Verification Plan

### Automated Tests
Nous ferons tourner le script en mode validation de syntaxe/chargement :
```powershell
.venv\Scripts\python.exe -c "import agent; print('Syntaxe OK!')"
```

### Manual Verification
1. Démarrer l'agent de développement en le connectant au salon LiveKit Cloud de l'utilisateur :
   ```powershell
   .venv\Scripts\python.exe agent.py dev
   ```
2. Ouvrir le Sandbox/Playground LiveKit Cloud pour tester l'interaction vocale en français et vérifier que l'agent transcrit, réfléchit avec Gemini, et répond localement avec la voix Kokoro en temps réel.
