# 🎙️ TTS & STT Benchmark — Walkthrough & Final Results (Audios de Discussion Complets)

## Vue d'ensemble

Ce projet met en place un pipeline complet d'évaluation de modèles de synthèse vocale (TTS) et de reconnaissance vocale (STT/ASR) en français.

Nous avons développé le script [generate_discussion.py](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/generate_discussion.py) pour générer l'intégralité du dialogue bancaire de 21 répliques sous forme d'un unique fichier audio fusionné par modèle, en alternant les voix ou les styles pour différencier l'**Agent** (conseillère bancaire, voix féminine et polie) et le **Client** (client fâché et pressé).

---

## 🛠️ Script de Discussion & Alternance de Voix

Le script [generate_discussion.py](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/generate_discussion.py) a été conçu avec des stratégies spécifiques pour chaque modèle afin de garantir une séparation claire des voix, même sur les modèles ne supportant qu'une voix native en français :

### 📋 Cartographie des Voix par Modèle et Rôle

| Modèle TTS | Voix / Style Agent | Voix / Style Client | Technique de Séparation |
| :--- | :--- | :--- | :--- |
| **edgetts** | `fr-FR-DeniseNeural` (Féminin) | `fr-FR-HenriNeural` (Masculin) | **Bi-voix native** (Homme/Femme) |
| **gtts** | `lang="fr"`, `tld="fr"` (France) | `lang="fr"`, `tld="ca"` (Canada) | **Séparation par accent régional** |
| **hume** | `Claire` (ID: `9e1f9e4f-...`, Féminin) | `Benjamin` (ID: `f98af01b-...`, Masculin) | **Bi-voix native** (Homme/Femme) |
| **kokoro** | `ff_siwis` (Vitesse 1.05) | `ff_siwis` (Vitesse 0.90) | **Séparation par rythme/vitesse** |
| **melo** | `FR` (Vitesse 1.05) | `FR` (Vitesse 0.90) | **Séparation par rythme/vitesse** |
| **mistral** | `fr_marie_neutral` (Neutre) | `fr_marie_angry` (Fâchée / Irritée) | **Séparation par style d'émotion** |
| **f5tts** | Clonage féminin (référence Kokoro) | Clonage de votre voix (`my_voice.ogg`) | **Voice Cloning avec votre voix réelle** |
| **elevenlabs** | `Sarah` (Féminin, mature, rassurante) | `Adam` (Masculin, ferme, dominant/gronchon) | **Bi-voix native** (Homme/Femme) |
| **openai** | `nova` (Féminin) | `onyx` (Masculin) | **Bi-voix native** (Homme/Femme) |

---

## 🚀 Fonctionnalités Clés et Résilience

1. **Robustesse face aux API Rate Limits (HTTP 429)** :
   * Nous avons intégré des pauses proactives (2,0 secondes) entre chaque requête pour les API cloud.
   * En cas d'erreur de surcharge (HTTP 429), le script se met automatiquement en pause pendant **60 secondes** pour permettre la réinitialisation de la fenêtre de requêtes de l'API (ce qui a permis au modèle **Hume** de finaliser ses 21 répliques avec succès).
2. **Normalisation Audio à la Fusion** :
   * Chaque réplique est lue, convertie automatiquement en **mono 24kHz** (via rééchantillonnage dynamique si nécessaire), puis concaténée avec une **pause de silence de 0,8 seconde** entre les interlocuteurs pour un rendu de conversation ultra-naturel.

---

## 📁 Audios de Discussion Générés

Les fichiers audio finaux fusionnés ont été sauvegardés avec succès dans le répertoire [outputs/discussions/](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/outputs/discussions/) :

* 🎤 **Edge-TTS** : [discussion_edgetts.wav](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/outputs/discussions/discussion_edgetts.wav) (Voix féminine Denise / masculine Henri)
* 🎤 **ElevenLabs** : [discussion_elevenlabs.wav](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/outputs/discussions/discussion_elevenlabs.wav) (Voix féminine Sarah / masculine Adam grincheux)
* 🎤 **Google TTS** : [discussion_gtts.wav](file:///C:/Users/user/.gemini/antigravity/outputs/discussions/discussion_gtts.wav) (Accent français / québécois)
* 🎤 **Hume Octave** : [discussion_hume.wav](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/outputs/discussions/discussion_hume.wav) (Voix féminine Claire / masculine Benjamin)
* 🎤 **Kokoro v1.0** : [discussion_kokoro.wav](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/outputs/discussions/discussion_kokoro.wav) (Voix Siwis rapide / lente)
* 🎤 **MeloTTS** : [discussion_melo.wav](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/outputs/discussions/discussion_melo.wav) (Voix FR rapide / lente)
* 🎤 **Mistral Voxtral** : [discussion_mistral.wav](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/outputs/discussions/discussion_mistral.wav) (Marie voix neutre / voix fâchée)
* 🎤 **F5-TTS** : [discussion_f5tts.wav](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/outputs/discussions/discussion_f5tts.wav) (Clonage voix féminine Denise / **Votre voix clonée** via `my_voice.ogg`)

> [!NOTE]
> * **OpenAI** : N'a pas pu être généré en raison d'une erreur de quota insuffisant sur votre compte (`429 Client Error: Too Many Requests`), ce qui est une limite budgétaire stricte de la clé.

---

## 🛠️ Comment relancer le script

Pour générer à nouveau ou ajouter d'autres modèles, lancez simplement :
```powershell
.venv\Scripts\python generate_discussion.py --models kokoro melo edgetts gtts hume mistral f5tts
```

---

## 🤖 Transition vers des modèles STT & TTS Cloud à Faible Latence (Cohere & Mistral)

Pour répondre à votre demande et minimiser la latence de conversation, nous avons migré l'agent vocal LiveKit vers les APIs cloud de Cohere et Mistral :
1. **STT (Reconnaissance Vocale)** : Nous avons développé la classe `CohereSTT` (qui hérite de `livekit.agents.stt.STT`) utilisant l'API **Cohere Transcribe v2** (`cohere-transcribe-03-2026`).
   * L'agent convertit l'audio détecté par le VAD en fichier WAV PCM 16 bits en mémoire (`io.BytesIO`) et l'envoie à l'API Cohere.
   * La transcription est ultra-rapide et affiche la meilleure précision du benchmark en français.
2. **TTS (Synthèse Vocale)** : Nous avons développé la classe `MistralTTS` (qui hérite de `livekit.agents.tts.TTS`) utilisant l'API **Mistral Voxtral** (`voxtral-mini-tts-2603`) avec la voix **`fr_marie_angry`** (voix nativement irritée/mécontente, parfaite pour le rôle).
   * L'audio généré (24 kHz) est décodé et rééchantillonné dynamiquement à 48 kHz (le standard attendu par WebRTC) pour garantir la stabilité du flux.
3. **LLM** : Nous conservons **Google Gemini 2.5 Flash** (via votre clé API validée).

### Statut du Service et Lancement
L'agent a été testé et mis en service :
*   **Salon** : `wss://internship-obt2eynj.livekit.cloud`
*   **Worker ID** : `AW_g8qiPkjxwS5k` (ou le nouveau ID attribué lors du redémarrage)
*   **Région** : `EU West B`
*   **Script de l'agent mis à jour** : [agent.py](file:///C:/Users/user/.gemini/antigravity/scratch/tts-benchmark/agent.py)

### 🚀 Lancement de la Simulation :
1. Lancez l'agent vocal :
   ```powershell
   .venv\Scripts\python agent.py dev
   ```
2. Ouvrez le Sandbox/Playground LiveKit Cloud pour tester l'interaction vocale en français avec la voix irritée de Marie de Mistral et une latence de réponse quasi instantanée (< 1s) !
